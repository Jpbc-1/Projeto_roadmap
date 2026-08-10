import React, { useCallback, useState } from 'react';
import GoalIntakeScreen from '../screens/GoalIntakeScreen';
import GoalProcessingScreen from '../screens/GoalProcessingScreen';

type OnboardingFlowProps = {
  /** Chamado quando o primeiro objetivo termina de ser gerado — quem usa
   * isso decide o que "terminou onboarding" significa (normalmente:
   * mostrar as abas principais). */
  onComplete: () => void;
};

export default function OnboardingFlow({ onComplete }: OnboardingFlowProps) {
  const [goalId, setGoalId] = useState<number | null>(null);

  const handleCreated = useCallback((id: number) => setGoalId(id), []);

  if (goalId === null) {
    return <GoalIntakeScreen onCreated={handleCreated} />;
  }

  // onComplete precisa ser uma referência estável (useCallback lá em
  // cima na tela pai) -- GoalProcessingScreen usa essa prop como
  // dependência do efeito de polling, então uma função nova a cada
  // render reiniciaria o ciclo sem necessidade.
  return <GoalProcessingScreen goalId={goalId} onComplete={onComplete} />;
}
