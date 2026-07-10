# Roadmap AI 🧭

> Um "Duolingo para a vida" — transforma grandes objetivos em missões diárias personalizadas, usando IA para criar e adaptar roadmaps de aprendizado e evolução pessoal.

## 🎯 Visão do Produto

A maioria das pessoas não desiste dos seus objetivos por falta de capacidade, mas porque não sabe qual é o próximo passo, perde a motivação ou não consegue enxergar a própria evolução.

O Roadmap AI resolve isso com:
- **Roadmaps personalizados** gerados por IA a partir de um objetivo do usuário
- **Missões diárias** que quebram o objetivo em passos pequenos e executáveis
- **Adaptação contínua** do plano conforme o usuário evolui
- **Gamificação** (XP, níveis, streaks, medalhas)
- **Diário da Evolução** e **Mapa do Conhecimento** (curva do esquecimento)

## 🏗️ Arquitetura (MVP)

- **Backend:** Python + FastAPI, Clean Architecture / DDD
- **Banco de dados:** PostgreSQL
- **Frontend:** Web e Mobile (a definir stack)
- **IA:** núcleo inteligente (possível arquitetura multiagente futura)

## 📁 Estrutura do Repositório

```
roadmap-ai/
├── backend/                  # API em FastAPI (Clean Architecture)
│   └── app/
│       ├── api/               # Camada de apresentação (rotas/endpoints)
│       ├── domain/             # Regras de negócio (entidades, casos de uso)
│       ├── infrastructure/     # Banco de dados, repositórios concretos, integrações externas
│       ├── core/               # Configurações, settings, segurança
│       └── tests/              # Testes automatizados
├── frontend-web/             # Aplicação Web (a iniciar)
├── frontend-mobile/          # Aplicação Mobile (a iniciar)
├── docs/
│   ├── adr/                   # Architecture Decision Records
│   └── database/              # Modelagem do banco (diagramas, scripts)
└── .github/workflows/        # Pipelines de CI/CD
```

## 🚀 Como rodar o backend localmente

```bash
cd backend
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000` e a documentação interativa (Swagger) em `http://localhost:8000/docs`.

## 📌 Status do Projeto

MVP em desenvolvimento — foco inicial no nicho de **Educação/Tecnologia**, cobrindo o ciclo:

`Objetivo → Roadmap → Missões Diárias → Execução → Evolução → Adaptação do Roadmap`

## 📄 Documentação

- [ADRs (decisões de arquitetura)](docs/adr)
- [Modelagem do banco de dados](docs/database)
