from dataclasses import dataclass

from app.core.ai.gemini_client import GeminiClient

GOAL_CATEGORIES = ["LEARNING", "PROJECT", "FITNESS", "FINANCE", "HABIT", "CAREER", "OTHER"]

MODERATION_SYSTEM_INSTRUCTION = """
Você é um classificador de conteúdo e categoria para um aplicativo educacional
que ajuda pessoas a atingir objetivos pessoais e profissionais legítimos
(aprender uma habilidade, estudar para uma prova, organizar finanças, criar
hábitos saudáveis, evoluir na carreira, etc).

Analise a descrição de objetivo enviada pelo usuário e responda SOMENTE em
JSON, no formato exato:
{"is_safe": true ou false, "reason": "explicação curta e objetiva", "category": "uma das categorias abaixo", "involves_learning": true ou false}

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

Classifique também o objetivo em UMA destas categorias:
- LEARNING: aprender uma habilidade, matéria, idioma, tecnologia, ou
  estudar para uma prova/concurso.
- PROJECT: construir algo concreto com etapas e entregas (um app, um
  livro, um negócio, uma reforma).
- FITNESS: saúde física, exercício, treino, esporte, perda ou ganho de peso.
- FINANCE: dinheiro, investimentos, orçamento, dívidas, economia pessoal.
- HABIT: criar ou abandonar um hábito comportamental (dormir cedo, meditar,
  parar de fumar, beber mais água).
- CAREER: carreira profissional, busca de emprego, promoção, networking.
- OTHER: qualquer coisa que não se encaixe claramente nas anteriores.

Além da categoria, avalie SEPARADAMENTE involves_learning: marque true se
alcançar esse objetivo exige adquirir e reter conhecimento conceitual/
teórico real (fatos, conceitos, terminologia, habilidades técnicas) como
parte central da jornada -- mesmo que a categoria não seja LEARNING. Por
exemplo: "conseguir estágio em Machine Learning" é CAREER, mas
involves_learning é true (tem muita base teórica pra estudar). "Aprender a
investir" é FINANCE, mas involves_learning também é true. Já "ficar com
corpo estético" (FITNESS) normalmente é involves_learning false -- é mais
consistência de execução do que retenção de conceito.

Se is_safe for false, ainda assim tente classificar a categoria da melhor
forma possível (ou use OTHER).
"""

MODERATION_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "is_safe": {"type": "BOOLEAN"},
        "reason": {"type": "STRING"},
        "category": {"type": "STRING", "enum": GOAL_CATEGORIES},
        "involves_learning": {"type": "BOOLEAN"},
    },
    "required": ["is_safe", "reason", "category", "involves_learning"],
}


@dataclass
class ModerationResult:
    is_safe: bool
    reason: str
    category: str
    involves_learning: bool


class ModerateGoalContentUseCase:
    def __init__(self, ai_client: GeminiClient):
        self.ai_client = ai_client

    async def execute(self, context_prompt: str) -> ModerationResult:
        result = await self.ai_client.generate_json(
            prompt=context_prompt,
            system_instruction=MODERATION_SYSTEM_INSTRUCTION,
            response_schema=MODERATION_RESPONSE_SCHEMA,
        )

        category = str(result.get("category", "")).upper()
        if category not in GOAL_CATEGORIES:
            category = "OTHER"  

        return ModerationResult(
            is_safe=bool(result["is_safe"]),
            reason=str(result["reason"]),
            category=category,
            involves_learning=bool(result.get("involves_learning", False)),
        )