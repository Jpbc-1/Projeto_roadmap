import React from 'react';
import { View, Text, TouchableOpacity, ScrollView, StyleSheet } from 'react-native';
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

// Other active roadmaps, each with its own mission for today. The
// featured roadmap (Python) already has the spotlight via the hero
// MissionCard above — it doesn't get a second, redundant card down here.
// Capped at 2: enough to show there's more to do today without it
// reading like a to-do list.
const OTHER_ROADMAPS = [
  {
    key: 'sql',
    roadmapTitle: 'SQL para Iniciantes',
    todayMission: 'Joins e relacionamentos',
    description: 'Una tabelas e cruze informações com SQL.',
    minutes: 14,
    progress: 0.72,
  },
  {
    key: 'estatistica',
    roadmapTitle: 'Estatística Básica',
    todayMission: 'Média, mediana e moda',
    description: 'Entenda as medidas de tendência central na prática.',
    minutes: 10,
    progress: 0.3,
  },
];

export default function DashboardScreen() {
  return (
    <WoodBackground>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <HomeHeader
        name="Helena"
        avatarEmoji="🦊"
        streakDays={8}
        level={12}
        hasUnreadNotification
      />

      {/* The one question this screen answers: "qual é minha próxima
          missão?" — everything below is supporting context, deliberately
          quieter than this card. */}
      <MissionCard
        context="Cap. 3 · Python para Dados"
        chapterProgress={0.45}
        missionName="Carregar e explorar seu primeiro DataFrame"
        description="Abra um CSV real com pandas e descubra o que está escondido nos dados."
        xp={80}
        minutes={15}
        onFinish={() => {}}
      />

      <StreakProgress currentStreak={8} nextMilestone={30} freezesAvailable={2} />

      <StudyReminder time="19:00" label="Sessão de estudos" />

      {/* Reviews aren't tied to any single roadmap — they pull from
          everything the person has learned across all of them. */}
      <View style={styles.reviewWrapper}>
        <ReviewCard pendingCount={2} />
      </View>

      <MilestoneCard title="Concluir o Capítulo 3" missionsDone={4} missionsTotal={9} xpReward={500} />

      <View style={styles.sectionHeader}>
        <Text style={styles.sectionTitle}>Suas outras missões</Text>
      </View>
      {OTHER_ROADMAPS.map((roadmap) => (
        <RoadmapCard
          key={roadmap.key}
          roadmapTitle={roadmap.roadmapTitle}
          todayMission={roadmap.todayMission}
          description={roadmap.description}
          minutes={roadmap.minutes}
          progress={roadmap.progress}
        />
      ))}

      <TouchableOpacity
        style={styles.viewAllButton}
        accessibilityRole="button"
        accessibilityLabel="Ver todos os seus roadmaps"
      >
        <Text style={styles.viewAllText}>Ver todos os roadmaps</Text>
        <Ionicons name="arrow-forward" size={16} color={colors.textPrimary} />
      </TouchableOpacity>
      </ScrollView>
    </WoodBackground>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
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