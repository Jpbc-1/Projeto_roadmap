from typing import List

from app.application.goals.get_goal import GoalAccessDeniedError, GoalNotFoundError
from app.domain.repositories.goal_repository import GoalRepository


class GoalNotAwaitingInfoError(Exception):
    """Levantado quando esse objetivo não tem nenhuma pergunta pendente
    (já foi respondido, ou nunca teve pergunta nenhuma)."""


class AnswerGoalQuestionsUseCase:
    """Recebe as respostas às perguntas da triagem (IntakeGoalUseCase),
    anexa no improved_prompt como contexto extra, e libera o objetivo pra
    seguir pra geração de verdade (quem enfileira o job "generate_roadmap"
    é o endpoint, depois de chamar este use case)."""

    def __init__(self, goal_repository: GoalRepository):
        self.goal_repository = goal_repository

    async def execute(self, goal_id: int, user_id: int, answers: List[str]) -> None:
        goal = await self.goal_repository.get_by_id(goal_id)
        if goal is None:
            raise GoalNotFoundError(f"Objetivo {goal_id} não encontrado.")
        if goal.user_id != user_id:
            raise GoalAccessDeniedError("Você não tem acesso a este objetivo.")

        if goal.generation_status != "awaiting_info" or not goal.pending_questions:
            raise GoalNotAwaitingInfoError("Este objetivo não tem perguntas pendentes de resposta.")

        questions = goal.pending_questions
        qa_lines = []
        for index, question in enumerate(questions):
            answer = answers[index].strip() if index < len(answers) and answers[index] else ""
            if answer:
                qa_lines.append(f"- {question} {answer}")

        base_prompt = goal.improved_prompt or goal.context_prompt
        if qa_lines:
            base_prompt = base_prompt + "\n\nInformações adicionais fornecidas pelo usuário:\n" + "\n".join(
                qa_lines
            )

        await self.goal_repository.update(
            goal_id,
            improved_prompt=base_prompt,
            pending_questions=None,
            generation_status="pending",
        )
