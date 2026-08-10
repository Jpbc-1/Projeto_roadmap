import React, { useEffect, useRef, useState } from 'react';
import { Text, TextInput, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import DeskBackground from '../components/DeskBackground';
import NotepadCard from '../components/NotepadCard';
import { PrimaryButton } from '../components/AuthButton';
import { goalService, Goal } from '../services/goalService';

type GoalProcessingScreenProps = {
  goalId: number;
  onComplete: () => void;
};

const POLL_INTERVAL_MS = 2500;
const POLL_RETRY_AFTER_ERROR_MS = 4500;

export default function GoalProcessingScreen({ goalId, onComplete }: GoalProcessingScreenProps) {
  const [goal, setGoal] = useState<Goal | null>(null);
  const [pollError, setPollError] = useState(false);
  const [answers, setAnswers] = useState<string[]>([]);
  const [questionIndex, setQuestionIndex] = useState(0);
  const [submittingAnswers, setSubmittingAnswers] = useState(false);
  const [answerError, setAnswerError] = useState<string | null>(null);

  // pollToken muda toda vez que a gente precisa (re)começar a sondar --
  // no mount, e de novo depois que as perguntas de esclarecimento são
  // respondidas. isMounted evita setState depois que a tela sai de tela
  // (o polling é recursivo via setTimeout, então precisa desse cuidado).
  const [pollToken, setPollToken] = useState(0);
  const isMountedRef = useRef(true);

  useEffect(() => {
    isMountedRef.current = true;
    return () => {
      isMountedRef.current = false;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    let timeoutId: ReturnType<typeof setTimeout>;

    async function tick() {
      try {
        const fetched = await goalService.get(goalId);
        if (cancelled || !isMountedRef.current) return;
        setGoal(fetched);
        setPollError(false);

        if (fetched.generation_status === 'completed') {
          onComplete();
          return;
        }
        // "failed" e "awaiting_info" são terminais PRA ESSE ciclo de
        // polling: failed espera a pessoa tentar de novo, awaiting_info
        // espera as respostas dela. Só "pending"/"processing" continuam
        // sondando sozinhos.
        if (fetched.generation_status === 'failed' || fetched.generation_status === 'awaiting_info') {
          return;
        }
        timeoutId = setTimeout(tick, POLL_INTERVAL_MS);
      } catch {
        if (cancelled || !isMountedRef.current) return;
        setPollError(true);
        timeoutId = setTimeout(tick, POLL_RETRY_AFTER_ERROR_MS);
      }
    }

    tick();
    return () => {
      cancelled = true;
      clearTimeout(timeoutId);
    };
  }, [goalId, pollToken, onComplete]);

  async function handleAnswerSubmitAll(finalAnswers: string[]) {
    setSubmittingAnswers(true);
    setAnswerError(null);
    try {
      // Pergunta pulada = slot nunca escrito em `answers` = buraco
      // `undefined` no array. JSON.stringify serializa isso como `null`
      // (diferente de um buraco em um objeto, que some) -- e o back
      // espera List[str], não List[str | None]. Normaliza pra string
      // vazia em vez de arriscar um 422.
      const questionCount = goal?.pending_questions?.length ?? finalAnswers.length;
      const normalized = Array.from({ length: questionCount }, (_, i) => finalAnswers[i] ?? '');
      await goalService.answerQuestions(goalId, normalized);
      setQuestionIndex(0);
      setAnswers([]);
      setPollToken((t) => t + 1); // retoma o polling — o back já enfileirou a geração de verdade
    } catch {
      setAnswerError('Não foi possível enviar suas respostas agora. Tente de novo.');
    } finally {
      setSubmittingAnswers(false);
    }
  }

  function handleRetry() {
    setPollToken((t) => t + 1);
  }

  // --- estado: respondendo perguntas de esclarecimento ---
  if (goal?.generation_status === 'awaiting_info' && goal.pending_questions?.length) {
    const questions = goal.pending_questions;
    const currentAnswer = answers[questionIndex] ?? '';
    const isLast = questionIndex === questions.length - 1;

    function setCurrentAnswer(text: string) {
      setAnswers((prev) => {
        const next = [...prev];
        next[questionIndex] = text;
        return next;
      });
    }

    function goNext() {
      if (isLast) {
        handleAnswerSubmitAll(answers);
      } else {
        setQuestionIndex((i) => i + 1);
      }
    }

    return (
      <DeskBackground>
        <View style={styles.centeredWrap}>
          <NotepadCard pinCount={3}>
            <View style={styles.progressRow}>
              {questions.map((_, i) => (
                <View key={i} style={[styles.progressDash, i <= questionIndex && styles.progressDashDone]} />
              ))}
            </View>
            <Text style={styles.questionEyebrow}>
              pergunta {questionIndex + 1} de {questions.length}
            </Text>
            <Text style={styles.questionTitle}>{questions[questionIndex]}</Text>

            <TextInput
              style={styles.answerInput}
              placeholder="Sua resposta..."
              placeholderTextColor={colors.textSecondary}
              value={currentAnswer}
              onChangeText={setCurrentAnswer}
              multiline
              autoFocus
            />

            {answerError && <Text style={styles.errorText}>{answerError}</Text>}

            <View style={styles.questionNavRow}>
              {questionIndex > 0 && (
                <TouchableOpacity
                  style={styles.backButton}
                  onPress={() => setQuestionIndex((i) => i - 1)}
                  accessibilityRole="button"
                  accessibilityLabel="Pergunta anterior"
                >
                  <Ionicons name="arrow-back" size={18} color={colors.textPrimary} />
                </TouchableOpacity>
              )}
              <View style={styles.nextButtonWrap}>
                <PrimaryButton
                  label={isLast ? 'Concluir →' : 'Próxima →'}
                  onPress={goNext}
                  loading={submittingAnswers}
                />
              </View>
            </View>
            <TouchableOpacity onPress={goNext} accessibilityRole="button" style={styles.skipLink}>
              <Text style={styles.skipText}>Pular esta pergunta</Text>
            </TouchableOpacity>
          </NotepadCard>
        </View>
      </DeskBackground>
    );
  }

  // --- estado: falhou ---
  if (goal?.generation_status === 'failed') {
    return (
      <DeskBackground>
        <View style={styles.centeredWrap}>
          <NotepadCard pinCount={3}>
            <View style={[styles.iconCircle, styles.iconCircleError]}>
              <Ionicons name="close" size={26} color={colors.ratingAgain} />
            </View>
            <Text style={styles.statusTitle}>Algo deu errado</Text>
            <Text style={styles.statusSubtitle}>
              Não conseguimos montar seu plano dessa vez. Nenhum crédito foi perdido — pode tentar de novo.
            </Text>
            <PrimaryButton label="Tentar de novo" onPress={handleRetry} />
          </NotepadCard>
        </View>
      </DeskBackground>
    );
  }

  // --- estado padrão: aguardando (pending/processing), com indicador
  // discreto se o polling em si estiver falhando (sem assustar a pessoa
  // com um erro técnico por causa de uma soneca momentânea de rede) ---
  return (
    <DeskBackground>
      <View style={styles.centeredWrap}>
        <NotepadCard pinCount={3}>
          <View style={styles.iconCircle}>
            <Ionicons name="checkmark" size={26} color={colors.primaryText} />
          </View>
          <Text style={styles.statusTitle}>Tudo pronto!</Text>
          <Text style={styles.statusSubtitle}>
            Sua jornada está sendo preparada. Em instantes você terá seu plano personalizado.
          </Text>
          <View style={styles.dotsRow}>
            <PulsingDot delay={0} />
            <PulsingDot delay={160} />
            <PulsingDot delay={320} />
          </View>
          {pollError && <Text style={styles.reconnecting}>Reconectando...</Text>}
        </NotepadCard>
      </View>
    </DeskBackground>
  );
}

function PulsingDot({ delay }: { delay: number }) {
  // Decorativo e simples de propósito -- três pontos com opacidade fixa
  // já comunicam "processando" o bastante aqui; uma animação de verdade
  // é um ajuste de polimento, não essencial pro fluxo funcionar.
  return <View style={[styles.dot, { opacity: 0.4 + (delay / 320) * 0.3 }]} />;
}

const styles = StyleSheet.create({
  centeredWrap: {
    flex: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
  },
  iconCircle: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: spacing.md,
  },
  iconCircleError: {
    backgroundColor: 'rgba(200,80,70,0.12)',
  },
  statusTitle: {
    fontFamily: fonts.handwritten,
    fontSize: 34,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  statusSubtitle: {
    ...typography.caption,
    fontSize: 13,
    lineHeight: 18,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.sm,
    paddingHorizontal: spacing.sm,
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 6,
    marginTop: spacing.lg,
  },
  dot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: colors.primaryText,
  },
  reconnecting: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.md,
  },
  progressRow: {
    flexDirection: 'row',
    gap: 6,
    marginBottom: spacing.md,
  },
  progressDash: {
    flex: 1,
    height: 3,
    borderRadius: 1.5,
    backgroundColor: colors.notebookRuleLine,
  },
  progressDashDone: {
    backgroundColor: colors.primary,
  },
  questionEyebrow: {
    ...typography.eyebrow,
    fontSize: 10,
    color: colors.textSecondary,
  },
  questionTitle: {
    ...typography.screenTitle,
    fontSize: 20,
    lineHeight: 25,
    color: colors.textPrimary,
    marginTop: 4,
    marginBottom: spacing.md,
  },
  answerInput: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    minHeight: 80,
  },
  errorText: {
    ...typography.caption,
    fontSize: 12,
    color: colors.ratingAgain,
    marginTop: spacing.sm,
  },
  questionNavRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  backButton: {
    width: touchTarget,
    height: touchTarget,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  nextButtonWrap: {
    flex: 1,
  },
  skipLink: {
    alignSelf: 'center',
    marginTop: spacing.sm,
  },
  skipText: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondary,
  },
});
