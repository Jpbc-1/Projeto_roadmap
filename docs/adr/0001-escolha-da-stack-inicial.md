# ADR-0001: Escolha da Stack Inicial (Backend, Banco de Dados e Arquitetura)

**Status:** Aceito
**Data:** 2026-07-10

## Problema

Precisamos definir a stack tecnológica inicial do Roadmap AI, equilibrando produtividade de desenvolvimento, robustez para lidar com dados de IA/roadmaps personalizados, e simplicidade para o MVP.

## Alternativas Consideradas

1. **Node.js + NestJS + PostgreSQL** — bom ecossistema, mas menor afinidade com bibliotecas de IA/ML.
2. **Python + Django + PostgreSQL** — robusto, porém mais "opinativo" e pesado para uma API que será majoritariamente consumida por front-ends separados.
3. **Python + FastAPI + PostgreSQL** — leve, assíncrono nativo, forte tipagem via Pydantic, ótima integração com bibliotecas de IA/ML e geração automática de documentação (Swagger).

## Solução Escolhida

Python + FastAPI como backend, PostgreSQL como banco relacional principal, seguindo Clean Architecture (camadas `api` / `domain` / `infrastructure` / `core`).

## Motivo da Escolha

- Python tem o ecossistema mais maduro para features futuras de IA (LLMs, agentes, processamento de linguagem).
- FastAPI oferece alta produtividade, tipagem forte com Pydantic e performance assíncrona, essencial para chamadas a APIs de IA externas sem bloquear a aplicação.
- PostgreSQL é maduro, confiável, suporta bem dados relacionais (usuários, roadmaps, missões) e tem bom suporte a JSONB para dados semi-estruturados (útil para armazenar respostas de IA).
- Clean Architecture separa regras de negócio de detalhes de infraestrutura, facilitando trocar/testar componentes conforme o projeto evolui (ex: trocar o provedor de IA sem afetar o domínio).

## Consequências

**Positivas**
- Facilidade para evoluir para um sistema multiagente no futuro sem reescrever a base.
- Documentação de API automática (Swagger/OpenAPI) desde o início.
- Testabilidade alta pela separação de camadas.

**Negativas**
- Estrutura em camadas adiciona um pouco de boilerplate mesmo para features simples do MVP — aceitável, pois o projeto é de longo prazo.
- Equipe precisa manter disciplina para não misturar regras de negócio com detalhes de infraestrutura (ex: SQLAlchemy) dentro do domínio.
