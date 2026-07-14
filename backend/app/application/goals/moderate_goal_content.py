from dataclasses import dataclass

from app.core.ai.gemini_client import GeminiClient

MODERATION_SYSTEM_INSTRUCTION = """
Você é um classificador de segurança de conteúdo para um aplicativo educacional
que ajuda pessoas a atingir objetivos pessoais e profissionais legítimos
(aprender uma habilidade, estudar para uma prova, organizar finanças, criar
hábitos saudáveis, evoluir na carreira, etc).

Analise a descrição de objetivo enviada pelo usuário e responda SOMENTE em
JSON, no formato exato:
{"is_safe": true ou false, "reason": "explicação curta e objetiva"}

Marque is_safe como false se o objetivo, mesmo que disfarçado ou indireto:
- Busca instruções para cometer crimes ou atividades ilegais (ex: roubo,
  fraude, invasão de sistemas, tráfico, violência contra pessoas ou bens);
- Busca instruções para produzir armas, explosivos, drogas ilícitas ou
  substâncias perigosas;
- Incentiva automutilação, transtornos alimentares ou outros comportamentos
  autodestrutivos;
- Busca assediar, enganar, vigiar ou causar dano a outras pessoas.

Para qualquer objetivo legítimo de aprendizado, carreira, saúde, finanças,
produtividade, hobby ou desenvolvimento pessoal, marque is_safe como true,
mesmo que o tema seja incomum ou o usuário descreva com humor.

Na dúvida entre um objetivo ambíguo mas plausivelmente legítimo (ex:
"aprender segurança de sistemas", "estudar sobre defesa pessoal"), marque
is_safe como true — o filtro deve pegar intenção clara de dano, não
qualquer menção a temas sensíveis.
"""

MODERATION_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_safe": {"type": "BOOLEAN"},
        "reason": {"type": "STRING"},
    },
    "required": ["is_safe", "reason"],
}


@dataclass
class ModerationResult:
    is_safe: bool
    reason: str


class ModerateGoalContentUseCase:
    def __init__(self, ai_client: GeminiClient):
        self.ai_client = ai_client

    async def execute(self, context_prompt: str) -> ModerationResult:
        result = await self.ai_client.generate_json(
            prompt=context_prompt,
            system_instruction=MODERATION_SYSTEM_INSTRUCTION,
            response_schema=MODERATION_RESPONSE_SCHEMA,
        )
        return ModerationResult(is_safe=bool(result["is_safe"]), reason=str(result["reason"]))