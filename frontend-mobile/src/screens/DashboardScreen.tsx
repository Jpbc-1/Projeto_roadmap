import React, { useMemo } from 'react';
import { View, Text, TouchableOpacity, ScrollView, ActivityIndicator, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import HomeHeader from '../components/HomeHeader';
import MissionCard from '../components/MissionCard';
import StreakProgress from '../components/StreakProgress';
import StudyReminder from '../components/StudyReminder';
import ReviewCard from '../components/ReviewCard';
import MilestoneCard from '../components/MilestoneCard';
import RoadmapCard from '../components/RoadmapCard';
import WoodBackground from '../components/WoodBackground';
import { useDashboardData } from '../hooks/useDashboard';
import { useCompleteMission } from '../hooks/useObjetivos';
import { timeStringToDate, formatHM } from '../utils/dateUtils';

const STREAK_MILESTONES = [7, 14, 30, 60, 100, 180, 365, 500, 1000];
function nextMilestoneFor(streak: number): number {
  return STREAK_MILESTONES.find((m) => m > streak) ?? streak + 100;
}

function missionXp(estimatedMinutes: number | null): number {
  // Mesma fórmula do back (10 + minutos estimados) -- é só um número
  // pra mostrar antes de completar; o valor real é calculado e
  // persistido no servidor no momento da conclusão.
  return 10 + (estimatedMinutes ?? 0);
}

export default function DashboardScreen() {
  const { profile, featured, others, dueReviewCount, nextReminder, isLoading, roadmapsLoading } = useDashboardData();
  const completeMission = useCompleteMission(featured?.goalId ?? null);

  const chapterXpRemaining = useMemo(() => {
    // Não temos a lista de missões restantes aqui (só a atual) -- uma
    // estimativa simples e honesta: a missão de agora conta uma vez;
    // "reward" do MilestoneCard é apresentado como o que falta pra
    // fechar o capítulo, então isso é aproximado por design, não um
    // valor que o back também calcula.
    if (!featured) return 0;
    const remaining = featured.chapterMissionsTotal - featured.chapterMissionsDone;
    return remaining * missionXp(featured.estimatedMinutes);
  }, [featured]);

  if (isLoading) {
    // Só profile + lista de objetivos -- rápido; a área da missão em
    // destaque tem seu próprio estado de carregamento logo abaixo
    // (`roadmapsLoading`), pra não segurar cabeçalho/ofensiva/lembrete
    // esperando o roadmap mais lento entre vários objetivos.
    return (
      <WoodBackground>
        <View style={styles.loadingWrap}>
          <ActivityIndicator color={colors.primaryText} />
        </View>
      </WoodBackground>
    );
  }

  const displayName = profile?.username ?? profile?.email.split('@')[0] ?? 'por aí';

  return (
    <WoodBackground>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <HomeHeader
          name={displayName}
          avatarEmoji="🦅"
          streakDays={profile?.current_streak ?? 0}
          level={profile?.current_level ?? 1}
          hasUnreadNotification={dueReviewCount > 0}
        />

        {roadmapsLoading ? (
          <View style={styles.missionSkeleton}>
            <ActivityIndicator color={colors.primaryText} />
          </View>
        ) : featured ? (
          <MissionCard
            context={`Cap. ${featured.chapterOrderIndex + 1} · ${featured.goalTitle}`}
            chapterProgress={featured.chapterMissionsTotal > 0 ? featured.chapterMissionsDone / featured.chapterMissionsTotal : 0}
            missionName={featured.missionTitle}
            description={featured.missionDescription ?? 'Sua próxima missão nessa jornada.'}
            xp={missionXp(featured.estimatedMinutes)}
            minutes={featured.estimatedMinutes ?? 0}
            onFinish={() => {
              if (completeMission.isPending) return;
              completeMission.mutate({ missionId: featured.missionId });
            }}
          />
        ) : (
          <View style={styles.noFeatured}>
            <Text style={styles.noFeaturedText}>
              {others.length > 0
                ? 'Seus roadmaps estão sendo preparados pela IA — volte em instantes.'
                : 'Crie seu primeiro objetivo na aba Objetivos pra começar.'}
            </Text>
          </View>
        )}

        <StreakProgress
          currentStreak={profile?.current_streak ?? 0}
          nextMilestone={nextMilestoneFor(profile?.current_streak ?? 0)}
          freezesAvailable={0}
        />

        {nextReminder && <StudyReminder time={formatHM(timeStringToDate(nextReminder.time_of_day))} label={nextReminder.label} />}

        {dueReviewCount > 0 && (
          <View style={styles.reviewWrapper}>
            <ReviewCard pendingCount={dueReviewCount} />
          </View>
        )}

        {featured && (
          <MilestoneCard
            title={`Concluir ${featured.chapterTitle}`}
            missionsDone={featured.chapterMissionsDone}
            missionsTotal={featured.chapterMissionsTotal}
            xpReward={chapterXpRemaining}
          />
        )}

        {others.length > 0 && (
          <>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Suas outras missões</Text>
            </View>
            {others.slice(0, 2).map((goal) => (
              <RoadmapCard
                key={goal.goalId}
                roadmapTitle={goal.goalTitle}
                todayMission={goal.isComplete ? 'Jornada concluída 🎉' : goal.currentMissionTitle ?? 'Preparando seu roadmap...'}
                minutes={0}
                progress={goal.overallProgress}
              />
            ))}
          </>
        )}

        {others.length > 2 && (
          <TouchableOpacity style={styles.viewAllButton} accessibilityRole="button" accessibilityLabel="Ver todos os seus roadmaps">
            <Text style={styles.viewAllText}>Ver todos os roadmaps</Text>
            <Ionicons name="arrow-forward" size={16} color={colors.textPrimary} />
          </TouchableOpacity>
        )}
      </ScrollView>
    </WoodBackground>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  loadingWrap: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
  },
  noFeatured: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    padding: spacing.lg,
    marginTop: spacing.sm,
  },
  missionSkeleton: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    marginTop: spacing.sm,
    minHeight: 180,
    alignItems: 'center',
    justifyContent: 'center',
  },
  noFeaturedText: {
    ...typography.body,
    fontSize: 14,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  reviewWrapper: {
    marginTop: spacing.md,
  },
  sectionHeader: {
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  sectionTitle: {
    ...typography.sectionTitle,
    fontSize: 16,
    color: colors.textOnWoodMuted,
  },
  viewAllButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: touchTarget,
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    marginTop: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    borderStyle: 'dashed',
  },
  viewAllText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.textPrimary,
  },
});
