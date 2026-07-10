# Modelagem do Banco de Dados — MVP

Modelagem organizada em 3 domínios, implementada como modelos SQLAlchemy em
`backend/app/infrastructure/database/models.py`.

## 1. Domínio: Core (Jornada e Planejamento)

- **users**: conta do usuário.
- **goals**: objetivo definido pelo usuário. Guarda `context_prompt` (o que o usuário disse à IA).
- **roadmaps**: plano gerado pela IA para um `goal`. Versionado (`version`, `is_active`) —
  1 goal pode ter N roadmaps ao longo do tempo, mas apenas 1 ativo por vez.
  `ai_generation_log` guarda o raciocínio da IA ao gerar o plano.
- **roadmap_chapters**: divisões do roadmap, com progresso (`status`).
- **missions**: missões diárias dentro de um capítulo.

## 2. Domínio: Execução e Diário

- **mission_executions**: registro de cada missão concluída — inclui `user_reflection`
  (texto do diário da evolução) e `ai_feedback` (resposta da IA). `user_id` é mantido
  aqui mesmo sendo redundante, para evitar JOINs longos em queries de XP/streak diário.

## 3. Domínio: Gamificação

- **user_stats**: XP, nível, streak atual e recorde — relação 1:1 com `users`.
- **achievements**: catálogo de medalhas possíveis (`required_condition` guarda a regra,
  ex: `"7_day_streak"`).
- **user_achievements**: tabela associativa N:N entre usuários e medalhas conquistadas.

## Como aplicar isso no banco (Neon)

1. Crie o projeto no [Neon](https://neon.tech) e copie a connection string.
2. Copie `backend/.env.example` para `backend/.env` e cole a URL (trocando `sslmode=require` por `ssl=require`, conforme comentário no arquivo).
3. Dentro de `backend/`, instale as dependências e gere a primeira migration:

```bash
pip install -r requirements.txt
alembic revision --autogenerate -m "cria tabelas iniciais"
alembic upgrade head
```

4. Confira no painel do Neon (ou no Table Editor, se preferir Supabase) que as 9 tabelas foram criadas.
