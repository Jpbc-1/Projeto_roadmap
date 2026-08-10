import React, { useEffect, useState } from 'react';
import { ActivityIndicator, Text, TouchableOpacity, View, ScrollView, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useQueryClient } from '@tanstack/react-query';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import NotebookBackground from '../components/NotebookBackground';
import JourneyPath from '../components/JourneyPath';
import ReviewPostIt from '../components/ReviewPostIt';
import FlashcardReview from '../components/FlashcardReview';
import ChapterDetailScreen from './ChapterDetailScreen';
import GoalIntakeScreen from './GoalIntakeScreen';
import GoalProcessingScreen from './GoalProcessingScreen';
import { useGoals, useRoadmap, useDueReviews, useAnswerReview } from '../hooks/useObjetivos';
import { roadmapService } from '../services/roadmapService';

// Mesma ideia do UpcomingChip na Rotina: cores puramente decorativas pra
// diferenciar objetivos lado a lado, sem inventar um significado novo
// pros 5 tons semânticos que colors.ts já define.
const GOAL_TINTS = [colors.postIt.yellow, colors.postIt.blue, colors.postIt.pink, colors.postIt.green, colors.postIt.peach];

export default function ObjetivosScreen() {
  const goalsQuery = useGoals();
  const goals = goalsQuery.data ?? [];

  const [selectedGoalId, setSelectedGoalId] = useState<number | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<number | null>(null);
  const [reviewing, setReviewing] = useState(false);
  const [creatingGoal, setCreatingGoal] = useState(false);
  const [pendingNewGoalId, setPendingNewGoalId] = useState<number | null>(null);

  // Seleciona o primeiro objetivo assim que a lista chega -- só na
  // primeira vez (não força de volta pro primeiro se o usuário trocar
  // de aba manualmente depois).
  useEffect(() => {
    if (selectedGoalId === null && goals.length > 0) {
      setSelectedGoalId(goals[0].id);
    }
  }, [goals, selectedGoalId]);

  const goalIndex = Math.max(goals.findIndex((g) => g.id === selectedGoalId), 0);
  const accentTint = GOAL_TINTS[goalIndex % GOAL_TINTS.length];

  const roadmapQuery = useRoadmap(selectedGoalId);
  const dueReviewsQuery = useDueReviews();
  const answerReview = useAnswerReview();

  // Trocar de marcador deveria parecer abrir outro caderno que já
  // estava ali na mesa, não carregar algo novo -- então, assim que o
  // roadmap que a pessoa está OLHANDO termina de carregar, aproveita a
  // deixa e vai esquentando o cache dos outros objetivos em segundo
  // plano (com um respiro entre cada um, pra não competir por banda com
  // o que importa agora). Se a pessoa nunca tocar noutro marcador, esse
  // trabalho não custou nada além de uns bytes; se tocar, a troca é
  // instantânea.
  const queryClient = useQueryClient();
  useEffect(() => {
    if (roadmapQuery.isLoading || goals.length < 2) return;
    const others = goals.filter((g) => g.id !== selectedGoalId);
    const timeouts = others.map((goal, i) =>
      setTimeout(() => {
        queryClient.prefetchQuery({
          queryKey: ['roadmap', goal.id],
          queryFn: () => roadmapService.getRoadmap(goal.id),
        });
      }, 350 + i * 300)
    );
    return () => timeouts.forEach(clearTimeout);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [goals, selectedGoalId, roadmapQuery.isLoading]);

  const chapters = roadmapQuery.data?.chapters ?? [];
  const chaptersDone = chapters.filter((c) => c.status === 'completed').length;
  const overallProgress = chapters.length > 0 ? Math.round((chaptersDone / chapters.length) * 100) : 0;

  // --- criando um novo objetivo (reaproveita o mesmo fluxo do onboarding) ---
  if (pendingNewGoalId !== null) {
    return (
      <GoalProcessingScreen
        goalId={pendingNewGoalId}
        onComplete={() => {
          setPendingNewGoalId(null);
          setSelectedGoalId(pendingNewGoalId);
        }}
      />
    );
  }
  if (creatingGoal) {
    return <GoalIntakeScreen onCreated={(id) => { setCreatingGoal(false); setPendingNewGoalId(id); }} />;
  }

  // --- olhando o capítulo de um objetivo ---
  const selectedChapter = roadmapQuery.data?.chapters.find((c) => c.id === selectedChapterId) ?? null;
  if (selectedChapter && selectedGoalId !== null) {
    return <ChapterDetailScreen chapter={selectedChapter} goalId={selectedGoalId} onBack={() => setSelectedChapterId(null)} />;
  }

  return (
    <NotebookBackground>
      <View style={styles.header}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.tabsScroll} contentContainerStyle={styles.tabsContent}>
          {goals.map((goal, i) => {
            const active = goal.id === selectedGoalId;
            return (
              <TouchableOpacity
                key={goal.id}
                style={[
                  styles.tab,
                  active && styles.tabActive,
                  { backgroundColor: active ? GOAL_TINTS[i % GOAL_TINTS.length] : 'transparent' },
                ]}
                onPress={() => setSelectedGoalId(goal.id)}
                accessibilityRole="tab"
                accessibilityState={{ selected: active }}
              >
                <Text style={[styles.tabText, active && styles.tabTextActive]} numberOfLines={1}>
                  {goal.title ?? 'Sem título'}
                </Text>
              </TouchableOpacity>
            );
          })}
          <TouchableOpacity style={styles.newTab} onPress={() => setCreatingGoal(true)} accessibilityRole="button" accessibilityLabel="Novo objetivo">
            <Ionicons name="add" size={18} color={colors.textPrimary} />
          </TouchableOpacity>
        </ScrollView>

        {(dueReviewsQuery.data?.length ?? 0) > 0 && (
          <ReviewPostIt count={dueReviewsQuery.data!.length} onPress={() => setReviewing(true)} />
        )}
      </View>

      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        {goalsQuery.isLoading ? (
          <ActivityIndicator style={styles.loading} color={colors.graphite} />
        ) : goals.length === 0 ? (
          <View style={styles.emptyState}>
            <Text style={styles.emptyText}>Você ainda não tem nenhum objetivo por aqui.</Text>
            <TouchableOpacity style={styles.emptyButton} onPress={() => setCreatingGoal(true)}>
              <Text style={styles.emptyButtonText}>Criar meu primeiro objetivo</Text>
            </TouchableOpacity>
          </View>
        ) : selectedGoalId === null || roadmapQuery.isLoading ? (
          // selectedGoalId === null cobre o instante entre "a lista de
          // objetivos chegou" e "o efeito que seleciona o primeiro deles
          // rodou" -- sem isso, o JourneyPath chegava a piscar por um
          // frame com "ainda sendo desenhada" antes do spinner de
          // verdade assumir.
          <ActivityIndicator style={styles.loading} color={colors.graphite} />
        ) : (
          <>
            {roadmapQuery.data && (
              <View style={styles.goalHeaderRow}>
                <Text style={styles.goalHeaderTitle} numberOfLines={2}>
                  {goals.find((g) => g.id === selectedGoalId)?.title ?? 'Seu objetivo'}
                </Text>
                {chapters.length > 0 && (
                  <View style={[styles.goalProgressPill, { backgroundColor: accentTint }]}>
                    <Text style={styles.goalProgressPillText}>{overallProgress}%</Text>
                  </View>
                )}
              </View>
            )}
            <JourneyPath chapters={chapters} accentTint={accentTint} onSelectChapter={setSelectedChapterId} />
          </>
        )}
      </ScrollView>

      {reviewing && (dueReviewsQuery.data?.length ?? 0) > 0 && (
        <FlashcardReview
          cards={dueReviewsQuery.data!}
          onClose={() => setReviewing(false)}
          onAnswer={async (nodeId, difficulty) => {
            await answerReview.mutateAsync({ nodeId, difficulty });
          }}
        />
      )}
    </NotebookBackground>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    gap: spacing.sm,
  },
  tabsScroll: {
    flex: 1,
  },
  tabsContent: {
    gap: spacing.sm,
    paddingRight: spacing.sm,
  },
  tab: {
    minHeight: touchTarget - 8,
    borderWidth: 1.5,
    borderColor: colors.graphite,
    // Topo reto, base arredondada -- lê como um marcador pendurado do
    // topo da página, não como um botão solto. A aba ativa ganha uma
    // leve sombra (ver tabActive) pra parecer "levantada" sobre as
    // outras, feito uma aba de fato selecionada num fichário.
    borderTopWidth: 0,
    borderTopLeftRadius: 0,
    borderTopRightRadius: 0,
    borderBottomLeftRadius: radius.sm,
    borderBottomRightRadius: radius.sm,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    justifyContent: 'center',
    maxWidth: 140,
  },
  tabActive: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.18,
    shadowRadius: 4,
    elevation: 3,
  },
  tabText: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    color: colors.textSecondary,
  },
  tabTextActive: {
    color: colors.textPrimary,
  },
  newTab: {
    width: touchTarget - 8,
    height: touchTarget - 8,
    borderRadius: radius.sm,
    borderWidth: 1.5,
    borderColor: colors.graphite,
    borderStyle: 'dashed',
    alignItems: 'center',
    justifyContent: 'center',
  },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  goalHeaderRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  goalHeaderTitle: {
    ...typography.screenTitle,
    flex: 1,
    color: colors.textPrimary,
  },
  goalProgressPill: {
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: 4,
  },
  goalProgressPillText: {
    fontFamily: fonts.display,
    fontSize: 13,
    color: colors.textPrimary,
  },
  loading: {
    marginTop: spacing.xl,
  },
  emptyState: {
    alignItems: 'center',
    marginTop: spacing.xl,
    gap: spacing.md,
  },
  emptyText: {
    ...typography.body,
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  emptyButton: {
    minHeight: touchTarget,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    borderRadius: radius.md,
    backgroundColor: colors.textPrimary,
  },
  emptyButtonText: {
    ...typography.body,
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.surface,
  },
});
