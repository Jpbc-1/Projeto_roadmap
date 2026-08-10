# Roadmap AI — Backend

API do Roadmap AI: transforma um objetivo digitado pela pessoa num plano
de capítulos e missões diárias, usando IA (Google Gemini), com fila de
jobs em background e sistema de lembretes/notificações.

Se vocês querem entender a arquitetura e o raciocínio por trás do
código (não só rodar), tem um guia de onboarding completo à parte —
peçam pro tech lead. Este README é só "como colocar isso rodando na sua
máquina".

## Stack

- **Python 3.11+** (recomendado; testado em 3.12)
- **FastAPI** + **Uvicorn** (servidor ASGI)
- **PostgreSQL 14+** (único banco suportado — o código usa `asyncpg`,
  não roda em SQLite/MySQL sem trocar o driver)
- **SQLAlchemy 2.0** (async) + **Alembic** (migrations)
- **Google Gemini** (geração de roadmap, moderação, embeddings) — a API
  funciona sem chave de Gemini configurada, mas qualquer fluxo que
  dependa de IA (criar objetivo, adaptar roadmap, extrair conhecimento)
  vai falhar até você configurar uma

Não tem Redis, Celery, RabbitMQ nem nenhuma infraestrutura de fila
externa — a fila de background jobs roda dentro do próprio processo da
API, usando o Postgres como fila (ver `app/core/jobs/`). Isso significa
que **o único serviço externo que vocês precisam rodar é o Postgres**.

## Pré-requisitos

- Python 3.11 ou superior
- Uma chave de API do Google Gemini (opcional pra só subir a API, mas
  necessária pra qualquer fluxo de IA funcionar de verdade) — pegue em
  [aistudio.google.com/apikey](https://aistudio.google.com/apikey)

## Passo a passo

### 1. Crie e ative um ambiente virtual

```bash
cd backend
python3 -m venv venv
source venv/bin/activate        # Linux/Mac
# venv\Scripts\activate         # Windows
```

### 2. Instale as dependências

```bash
pip install -r requirements.txt
```


### 3. Configure o `.env`

```bash
cp .env.example .env
```

Abra o `.env` e preencha pelo menos:

- `DATABASE_URL` — connection string do Postgres do passo 3
- `SECRET_KEY` — **obrigatório**, a aplicação recusa subir sem isso (ver
  nota de segurança abaixo). Gere uma com:

  ```bash
  python -c "import secrets; print(secrets.token_urlsafe(32))"
  ```

- `GEMINI_API_KEY` — sem isso, tudo relacionado a IA falha em runtime
  (mas a API sobe normalmente e endpoints que não dependem de IA
  funcionam)

O resto das variáveis já tem um valor padrão sensato pra
desenvolvimento — só mexam se souberem o que estão mudando (o
`.env.example` documenta cada uma).

> **Nota de segurança:** `SECRET_KEY` não tem valor padrão de propósito.
> Se ela estivesse vazia por padrão, a aplicação subiria normalmente
> assinando token com uma string fraca/vazia — o que permitiria
> qualquer pessoa forjar um JWT válido pra qualquer usuário,
> silenciosamente, sem nenhum erro visível até alguém explorar isso.
> Por isso a API falha já no boot, com um erro de log claro, se
> `SECRET_KEY` estiver ausente ou tiver menos de 32 caracteres.





### 5. Suba a API

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

- `--reload` reinicia o servidor sozinho a cada mudança de código —
  ótimo pra desenvolvimento, tirem em produção.
- `--host 0.0.0.0` é o que permite o app mobile (rodando no celular ou
  emulador) acessar a API pela sua rede local, não só `localhost`.
- `--port 8000`: **usem essa porta se forem testar contra o app
  mobile** — o `.env.example` do frontend já assume `8000` por padrão.
  Se preferirem outra porta, tudo bem, só ajustem
  `EXPO_PUBLIC_API_URL` no `.env` do frontend pra combinar.

Se tudo deu certo:

- `GET http://localhost:8000/health` deve responder `{"status": "ok"}`
  (não toca o banco, só confirma que o processo está de pé)
- `GET http://localhost:8000/docs` abre a documentação interativa
  (Swagger UI) com todos os endpoints, gerada automaticamente pelo
  FastAPI

## Rodando os testes

```bash
pytest
```

**Aviso honesto:** hoje não existe nenhum teste escrito no projeto —
`pytest`/`pytest-asyncio` estão instalados, mas a suíte está vazia. Se
vocês forem os primeiros a escrever teste aqui, é uma contribuição bem-
vinda (ver o guia de onboarding pra sugestões de por onde começar).

## Erros comuns ao subir pela primeira vez

| Sintoma | Causa provável |
|---|---|
| `ValueError: SECRET_KEY ausente ou fraca` no boot | `.env` sem `SECRET_KEY`, ou com menos de 32 caracteres — gerem uma nova (passo 4). |
| `ConnectionRefusedError` / `OSError` ao subir | Postgres não está rodando, ou `DATABASE_URL` aponta pro host/porta errados. |
| Erro do tipo `relation "goals" does not exist` | Esqueceram de rodar `alembic upgrade head` (passo 5). |
| App mobile não consegue falar com a API | Confiram: (a) subiram com `--host 0.0.0.0`, não só `--port`; (b) celular/emulador e a máquina estão na mesma rede Wi-Fi; (c) `EXPO_PUBLIC_API_URL` no app aponta pro IP local certo, não `localhost` (`localhost` no celular é o próprio celular, não a sua máquina). |
| Criar objetivo fica travado em "processando" pra sempre | Confiram os logs do processo — se `GEMINI_API_KEY` estiver vazia ou inválida, o job de geração falha e o objetivo cai em `generation_status = "failed"` (o app mostra isso, mas vale conferir os logs pra confirmar a causa). |
| Requisição de um Swagger/frontend web externo dá erro de CORS | Esperado: a API hoje não tem `CORSMiddleware` configurado, porque o único cliente é o app mobile (que não passa por CORS de browser). Se forem integrar um cliente web, precisam adicionar `CORSMiddleware` em `app/main.py`. |

## Estrutura do projeto (resumo)

```
backend/
├── alembic/              # Migrations do banco
├── app/
│   ├── api/                 # Endpoints HTTP + schemas Pydantic
│   ├── application/           # Casos de uso (a lógica de negócio)
│   ├── domain/                   # Entidades e contratos (interfaces)
│   ├── infrastructure/              # Banco de dados, repositórios concretos
│   ├── core/                           # Config, segurança, cliente de IA, fila de jobs
│   └── main.py                            # Entrypoint da API
├── DOCUMENTACAO.md        # Histórico técnico de decisões de arquitetura
└── requirements.txt
```

Pra entender **por que** o código está organizado assim, e o caminho
completo de ponta a ponta de features como "criar objetivo" e
"notificações", consultem o guia de onboarding do backend.

## Variáveis de ambiente — referência completa

Ver `.env.example` para a lista comentada de cada variável, seus
valores padrão e o motivo de cada um. Só `DATABASE_URL`, `SECRET_KEY` e
`GEMINI_API_KEY` normalmente precisam ser tocadas em desenvolvimento; o
resto (custo em créditos por ação, intervalos da fila de jobs, rate
limit de login, OAuth) já vem com um padrão razoável.

## `.gitignore`

O projeto não tinha `.gitignore` — adicionado (`venv/`, `__pycache__/`,
`.env`, caches de teste). Sem isso, o ambiente virtual e o `.env` com
segredos reais correm o risco de ir parar no controle de versão no
primeiro `git add .` de quem clonar o projeto.