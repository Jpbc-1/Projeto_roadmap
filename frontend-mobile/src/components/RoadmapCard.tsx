import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';

type RoadmapCardProps = {
  /** Roadmap name, e.g. "SQL para Iniciantes" — context, not the headline */
  roadmapTitle: string;
  /** This roadmap's own mission for today */
  todayMission: string;
  minutes: number;
  /** 0 to 1 — overall progress through the roadmap */
  progress: number;
  onPress?: () => void;
};

// Condensed further: dropped the description line entirely (the hero
// card already carries a full description — these just need to say
// "here's the roadmap, here's today's mission, tap for more") and tucked
// the time onto the same row as the progress bar instead of its own line.
export default function RoadmapCard({ roadmapTitle, todayMission, minutes, progress, onPress }: RoadmapCardProps) {
  const pct = Math.round(Math.min(Math.max(progress, 0), 1) * 100);

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={`${roadmapTitle}, missão de hoje: ${todayMission}, ${minutes} minutos`}
    >
      <View style={styles.topRow}>
        <Text style={styles.eyebrow} numberOfLines={1}>
          {roadmapTitle}
        </Text>
        <Text style={styles.percent}>{pct}%</Text>
      </View>

      <Text style={styles.mission} numberOfLines={1}>
        {todayMission}
      </Text>

      <View style={styles.bottomRow}>
        <View style={styles.track}>
          <View style={[styles.fill, { width: `${pct}%` }]} />
        </View>
        <Text style={styles.time}>{minutes} min</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    minHeight: touchTarget,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.sm,
    marginTop: spacing.sm,
  },
  topRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  eyebrow: {
    ...typography.eyebrow,
    color: colors.textSecondary,
    flexShrink: 1,
    marginRight: spacing.sm,
  },
  percent: {
    fontFamily: fonts.display,
    fontSize: 13,
    color: colors.success,
  },
  mission: {
    ...typography.cardTitle,
    fontSize: 14,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  bottomRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  track: {
    flex: 1,
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.border,
  },
  fill: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.success,
  },
  time: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
  },
});