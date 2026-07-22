import React, { useState } from 'react';
import { View, Text, Image, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography } from '../theme/colors';
import StatsBar from '../components/StatsBar';
import MissionCard from '../components/MissionCard';
import StreakProgress from '../components/StreakProgress';
import CourseCard from '../components/CourseCard';
import TodayItem from '../components/TodayItem';
import BottomNav from '../components/BottomNav';

export default function DashboardScreen() {
  const [activeTab, setActiveTab] = useState('inicio');

  return (
    // Only the top edge here — the bottom edge's safe-area inset is handled
    // inside BottomNav itself, so the tab bar can sit flush against it
    // instead of leaving a double gap.
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerRow}>
          <Image source={{ uri: 'https://i.pravatar.cc/100?img=47' }} style={styles.avatar} />
          <Text style={styles.greeting}>Bom dia, Helena</Text>
        </View>
        <StatsBar level={12} xp={420} streakDays={8} badgeCount={3} />

        <MissionCard
          context="Capítulo 2 · Rumo ao Primeiro Estágio"
          chapterProgress={0.6}
          message="Bora pra missão de hoje! 👀"
          xp={35}
          minutes={15}
          onFinish={() => {}}
        />

        <StreakProgress currentStreak={8} nextMilestone={30} freezesAvailable={2} />

        {/* Reviews are the one thing here that isn't already a roadmap
            mission — every card under "Crescendo aos poucos" already IS
            that roadmap's mission for today (title = roadmap, subtitle =
            today's specific mission in it), so it doesn't get duplicated
            here too. No section header needed for a single self-explanatory
            row — tapping it goes straight to the review queue. */}
        <View style={styles.todayReview}>
          <TodayItem icon="repeat-outline" title="Revisão espaçada" meta="3 itens pendentes" />
        </View>

        <View style={styles.sectionHeader}>
          <Text style={styles.sectionTitle}>Crescendo aos poucos</Text>
          <TouchableOpacity
            style={styles.sectionLinkButton}
            hitSlop={{ top: 12, bottom: 12, left: 8, right: 8 }}
            accessibilityRole="button"
            accessibilityLabel="Ver todas as trilhas"
          >
            <Text style={styles.sectionLink}>Ver todos</Text>
            <Ionicons name="chevron-forward" size={14} color={colors.primary} />
          </TouchableOpacity>
        </View>
        <View style={styles.courseRow}>
          <CourseCard
            accent="blue"
            icon="code-slash-outline"
            title="Domine o Python"
            subtitle="Aprenda Dicionário"
            progress={0.4}
          />
          <CourseCard
            accent="teal"
            icon="trending-up-outline"
            title="Aprenda a investir"
            subtitle="Aprenda sobre CDB"
            progress={0.2}
          />
        </View>
      </ScrollView>

      <BottomNav active={activeTab} onSelect={setActiveTab} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
  },
  greeting: {
    ...typography.greeting,
    color: colors.textPrimary,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  sectionTitle: {
    ...typography.h1,
    fontSize: 18,
    color: colors.textPrimary,
  },
  sectionLinkButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  sectionLink: {
    ...typography.caption,
    color: colors.primary,
    fontWeight: '700',
  },
  courseRow: {
    flexDirection: 'row',
    gap: spacing.md,
  },
  todayReview: {
    marginTop: spacing.md,
  },
});