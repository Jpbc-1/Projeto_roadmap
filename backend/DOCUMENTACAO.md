# Documentação do Backend — Roadmap AI

Resumo de tudo que existe no backend hoje, organizado por área, com a lógica
principal de cada implementação. Escrito depois de três rodadas de trabalho:
correção de bugs, funcionalidades novas, e ajuste fino de custo de IA.

---

## 1. Confiabilidade e infraestrutura

### 1.1 Conexão com o banco não expira mais
**Onde:** `app/infrastructure/database/session.py`, `app/core/config.py`
O engine do SQLAlchemy agora usa `pool_pre_ping=True` (testa a conexão com um
`SELECT 1` antes de emprestar do pool — se o Supabase já tiver derrubado ela
por inatividade, troca por uma nova na hora, sem erro) e `pool_recycle`
(configurável via `DB_POOL_RECYCLE_SECONDS`, recicla proativamente conexões
velhas). Também existe `GET /health/db`, que roda um `SELECT 1` de verdade —
útil pra testar conectividade sem esperar isso quebrar no meio de uma feature.

### 1.2 Fila de tarefas em background (substitui BackgroundTasks)
**Onde:** `app/infrastructure/database/models.py` (`BackgroundJob`),
`app/infrastructure/repositories/job_repository.py`,
`app/core/jobs/worker.py`, `app/core/jobs/handlers.py`
Toda tarefa demorada (gerar roadmap, adaptar, auto-adaptar, extrair
conhecimento) agora vira uma linha na tabela `background_jobs` em vez de um
`BackgroundTasks.add_task` solto. Um worker (`start_worker`/`stop_worker`,
ligado no `lifespan` do FastAPI em `main.py`) roda um loop de polling
assíncrono dentro do próprio processo da API — sem precisar de Redis/Celery.
A cada ciclo, ele:
1. Recupera jobs presos em `"processing"` há mais de `JOB_STALE_AFTER_SECONDS`
   (worker que caiu no meio) de volta pra `"pending"`.
2. Reivindica até `JOB_BATCH_SIZE` jobs pendentes com
   `SELECT ... FOR UPDATE SKIP LOCKED` (seguro mesmo com múltiplos workers).
3. Processa o lote em paralelo; em erro, incrementa `attempts` e reagenda com
   backoff exponencial (até `JOB_MAX_ATTEMPTS`), ou marca `"failed"`.
`GET /api/v1/jobs/{id}` deixa consultar o status de qualquer job.

### 1.3 Fallback de modelo em cadeia (2 ou 3 níveis) em erro 503
**Onde:** `app/core/ai/gemini_client.py`, `app/core/config.py`
`GeminiClient` aceita `model` + `fallback_models` (lista ordenada). Se a
chamada com o modelo principal vier com **503** (sobrecarregado — o motivo
mais comum de falha em horário de pico), tenta o próximo da lista, e assim
por diante, até acertar ou esgotar. Erros que não são 503 (API key errada,
prompt bloqueado) nunca acionam fallback — trocar de modelo não resolve isso.
Cadeia atual: `GEMINI_PRO_MODEL` (gemini-3.6-flash) → `GEMINI_MODEL`
(gemini-3.5-flash-lite) → `GEMINI_FALLBACK_MODEL` (gemini-3.1-flash-lite,
mais barato e ainda confirmado funcionando — ver nota de preços abaixo).
Chamadas que já usam só o modelo "lite" (moderação, triagem, extração) também
ganharam esse terceiro nível como fallback.

> **Nota sobre preços/modelos (checar de novo antes de confiar cegamente):**
> pesquisei os preços mais recentes que encontrei (final de julho/2026):
> `gemini-3.5-flash-lite` ~$0.30/$2.50 por milhão de tokens (entrada/saída),
> `gemini-3.1-flash-lite` ~$0.13–0.25/$0.75–1.50 (as fontes discordam um
> pouco entre si), `gemini-3.6-flash` ~$1.50/$7.50. **Não usei
> `gemini-2.5-flash-lite`** apesar de ser o mais barato no papel (~$0.10/
> $0.40): há relatos de julho/2026 de erro 404 nele bem antes do
> desligamento oficialmente anunciado — pode já estar instável. Preço de
> IA muda toda hora; vale conferir a página oficial de preços do Google
> antes de trocar esses valores de novo.

---

## 2. Geração e adaptação do roadmap

### 2.1 Bug corrigido: modelo "pro" era idêntico ao "lite"
**Onde:** `app/core/config.py`
`GEMINI_PRO_MODEL` estava com o mesmo valor de `GEMINI_MODEL` — provável
copy-paste. Corrigido para modelos distintos (ver 1.3).

### 2.2 Prompt por categoria (fitness, carreira, finanças, hábito)
**Onde:** `app/application/goals/generate_roadmap.py` (`CATEGORY_GUIDANCE`),
usado também em `app/application/roadmaps/adapt_roadmap.py`
Dicionário `categoria -> texto extra de instrução`, injetado no prompt de
geração/adaptação conforme `goal.category` (definido pela moderação). Fitness
não gera missão de teoria/anatomia (foco em treino, rotina, medição);
carreira inclui currículo/entrevista sem cortar o aprendizado técnico;
finanças e hábito seguem a mesma lógica de "teoria só quando vira ação".

### 2.3 Missão-relâmpago no início
**Onde:** `generate_roadmap.py` (prompt) e `adapt_roadmap.py`
(`_generate_immediate_chapter` com `is_first_chapter`)
A missão 1 do capítulo 1 é sempre curta/fácil de propósito (vitória rápida) —
tanto na geração original quanto se a pessoa adaptar antes mesmo de terminar
o capítulo 1 (detectado por `current_chapter.order_index == 0`).

### 2.4 Títulos mais curtos e renomeação automática
**Onde:** mesmos arquivos do item 2.3
Limite de título caiu de 60 para 40 caracteres (objetivo e capítulos). Quando
a adaptação substitui o capítulo 1 inteiro, a IA também devolve um
`new_goal_title` (schema com `include_goal_title=True`) e o backend atualiza
`goal.title` automaticamente — o nome antigo não fazia mais sentido.

### 2.5 Triagem inicial + melhorador de prompt
**Onde:** `app/application/goals/intake_goal.py` (`IntakeGoalUseCase`),
`app/application/goals/answer_goal_questions.py`
Depois da moderação (já existente) passar, uma chamada de IA (modelo lite)
melhora a redação do pedido e detecta se falta informação prática importante
(peso/altura pra estética, orçamento mensal pra investir, etc.) — no máximo
3 perguntas, só quando vale a pena. Sem pergunta necessária, o `job_repository`
já encadeia `"generate_roadmap"` na mesma fila (ver 1.2). Com pergunta, o goal
fica em `generation_status="awaiting_info"` com `pending_questions` populado,
até `POST /goals/{id}/answers` liberar a geração de verdade.

### 2.6 Recomendações de recursos
**Onde:** `GoalRecommendation` (model), `recommendation_repository.py`
(domain+infra), prompt em `generate_roadmap.py`
A própria chamada que gera o roadmap sugere até 3 recursos pagos + 3
gratuitos (campo `"recommendations"` no JSON). De propósito **sem URL** — a
IA não tem como garantir que um link existe de verdade. `GET
/goals/{id}/recommendations`.

### 2.7 Adaptação em formato "git": propor, confirmar, rejeitar, travar
**Onde:** `app/application/roadmaps/propose_chapter_operation.py`,
`confirm_adaptation.py`, `set_chapter_lock.py`; campos `pending_adaptation`
(Roadmap) e `is_locked_from_ai` (RoadmapChapter)
Todo `POST /adapt` primeiro roda `ProposeChapterOperationUseCase`, que
classifica o feedback:
- **Mira um capítulo específico** → a IA gera uma operação
  (`replace_chapter` ou `insert_chapter`) mas **não aplica nada** — vira
  proposta pendente (`roadmap.pending_adaptation`), devolvida com
  `requires_confirmation: true` e um resumo. `POST /adapt/confirm` aplica de
  fato; `POST /adapt/reject` descarta sem tocar em nada.
- **Feedback amplo** (ritmo, dificuldade geral) → cai no fluxo de sempre
  (`AdaptRoadmapUseCase`, aplicado direto, comportamento **inalterado**).
Segurança em código (não só no prompt): nunca propõe operação num capítulo
`"completed"` ou com `is_locked_from_ai=True` — revalidado depois da IA
responder, não só confiando na instrução. `PATCH
/goals/{id}/chapters/{chapter_id}/lock` liga/desliga a trava manualmente.

---

## 3. Qualidade e integridade de dados

### 3.1 `created_by` (IA vs. usuário)
**Onde:** colunas em `Mission` e `RoadmapChapter`
Toda missão/capítulo agora sabe se veio de geração de IA ou de criação
manual — hardcoded no repositório em cada um dos ~7 pontos de criação
(nenhum parâmetro extra passado pelos use cases, já que cada método só é
chamado de um único lugar com origem sempre conhecida).

### 3.2 `is_conceptual` — o que entra no Mapa do Conhecimento
**Onde:** coluna em `Mission`; filtro em
`app/application/knowledge/extract_knowledge_nodes.py`
A IA já classifica cada missão como conceitual ou prática **na hora de
gerar** o roadmap (não só na hora de extrair). A extração filtra por esse
campo **antes** de chamar a IA de extração — resolve o bug de missões tipo
"configure o ambiente" virarem cartão de revisão com nome sem sentido
("python", "script").

### 3.3 Buraco no `order_index` ao deletar missão
**Onde:** `delete_mission` em
`app/infrastructure/repositories/roadmap_repository.py`
Depois de apagar, reordena as missões remanescentes do capítulo pra fechar a
sequência (só reescreve as que realmente mudaram de posição).

### 3.4 `current_chapter_id` / `current_mission_id`
**Onde:** `GET /goals/{id}/roadmap` (endpoint), calculado a partir do
primeiro capítulo `"in_progress"` e, dentro dele, da primeira missão sem
execução — o front não precisa mais varrer a árvore inteira.

---

## 4. Estrutura do roadmap

### 4.1 Inserir capítulo em qualquer posição
**Onde:** `insert_chapter_after` (repositório), `create_chapter.py`
`POST /goals/{id}/chapters` aceita `after_chapter_id` opcional — sem ele,
mantém o comportamento antigo (sempre no final). Bloqueado explicitamente
inserir logo após um capítulo `"completed"` que não seja o último (ficaria
travado pra sempre, já que o desbloqueio só dispara quando o capítulo
*imediatamente anterior* termina).

---

## 5. Próximas melhorias possíveis

Confiabilidade / operação:
- **Zero testes automatizados.** `pytest` está no `requirements.txt` mas não
  há nenhum arquivo de teste no projeto — dado o tanto de lógica de negócio
  que já existe (XP, streak, desbloqueio de capítulo, fila, fallback),
  cobertura básica valeria bastante a pena.
- **Sem rate limiting.** Nenhuma proteção visível contra abuso/spam de
  requisições (nem middleware, nem limite por usuário) — isso importa
  especialmente pros endpoints que disparam chamada de IA (criar objetivo,
  adaptar), que custam dinheiro por chamada.
- **Worker no mesmo processo da API.** Funciona bem no volume atual; se
  crescer bastante, competir por CPU/memória com as requisições HTTP pode
  virar gargalo. A migração pra processo separado é pequena (a query de
  claim já usa `SKIP LOCKED`, então já é segura pra múltiplos workers).
- **Sem visibilidade de jobs falhados em lote** — hoje só dá pra consultar
  um job de cada vez (`GET /jobs/{id}`); um `GET /jobs?status=failed` (ou um
  painel simples) ajudaria a notar se algo está falhando sistematicamente.

Produto:
- **`is_locked_from_ai` só é respeitado no fluxo de adaptação específico**
  (`ProposeChapterOperationUseCase`). O fluxo amplo antigo
  (`AdaptRoadmapUseCase`, que regenera capítulos futuros) ainda não checa a
  trava — deixado assim de propósito pra não mexer em código que já
  funcionava, mas é um ajuste pequeno se quiser a trava valendo em todo lugar.
- **`POST /adapt` (fluxo amplo) continua síncrono**, bloqueando a
  requisição até a IA responder — diferente de tudo que passa pela fila
  agora. Migrar faz sentido natural quando/se decidir estender o fluxo
  "git" pra também cobrir adaptação ampla.
- **Recomendações não se atualizam depois da criação inicial** — mesmo que
  o roadmap mude bastante numa adaptação, as recomendações continuam sendo
  as do dia 1. Dá pra regenerar no mesmo gatilho usado pra renomear o
  objetivo (substituição do capítulo 1).
- **Sem paginação em `GET /goals`** — hoje devolve todos os objetivos do
  usuário de uma vez (`list_by_user`, sem `limit`/`offset`). Não é um
  problema agora, mas vale ter antes de um usuário acumular muitos objetivos.

Custo/observabilidade de IA:
- **Nenhum tracking de gasto por usuário/objetivo** — não há registro de
  quantos tokens/chamadas cada objetivo consome. Como já existe
  `created_by` pra separar dado de IA vs. usuário, um próximo passo natural
  é registrar esse tipo de métrica também (ex: uma tabela `ai_usage_log`,
  ou simplesmente um contador em `BackgroundJob`).
- **Sem limite de tamanho** no feedback livre do `/adapt` nem nas respostas
  de `/answers` — um texto gigante (acidental ou não) vira uma chamada de
  IA cara. Um `max_length` nos schemas Pydantic resolveria.
