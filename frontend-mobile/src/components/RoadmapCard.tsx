import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';

type RoadmapCardProps = {
  /** Roadmap name, e.g. "SQL para Iniciantes" — context, not the headline */
  roadmapTitle: string;
  /** This roadmap's own mission for today */
  todayMission: string;
  description: string;
  minutes: number;
  /** 0 to 1 — overall progress through the roadmap */
  progress: number;
  onPress?: () => void;
};

// Plain cards, on purpose — the post-it treatment (color, tilt, pins)
// belongs to the hero mission alone. A whole list of colorful tilted
// notes read as a stationery display, not a hierarchy; these just need
// to be clean and quick to scan.
export default function RoadmapCard({
  roadmapTitle,
  todayMission,
  description,
  minutes,
  progress,
  onPress,
}: RoadmapCardProps) {
  const pct = Math.round(Math.min(Math.max(progress, 0), 1) * 100);

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={`${roadmapTitle}, missão de hoje: ${todayMission}`}
    >
      <View style={styles.topRow}>
        <Text style={styles.eyebrow} numberOfLines={1}>
          {roadmapTitle}
        </Text>
        <Text style={styles.percent}>{pct}%</Text>
      </View>
      <View style={styles.track}>
        <View style={[styles.fill, { width: `${pct}%` }]} />
      </View>

      <Text style={styles.mission}>{todayMission}</Text>
      <Text style={styles.description} numberOfLines={2}>
        {description}
      </Text>
      <Text style={styles.time}>{minutes} min</Text>
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
    padding: spacing.md,
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
    fontSize: 14,
    color: colors.success,
  },
  track: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.border,
    marginBottom: spacing.sm,
  },
  fill: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.success,
  },
  mission: {
    ...typography.cardTitle,
    fontSize: 15,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  description: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  time: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
  },
});