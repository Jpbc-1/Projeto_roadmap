import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

type MilestoneCardProps = {
  title: string;
  missionsDone: number;
  missionsTotal: number;
  xpReward: number;
};

// Quiet by design, same as StreakProgress — flat, no pin, no shadow.
// Troféus/achievement = green everywhere else in the app; the trophy
// glyph stays gold because a literal trophy reads as gold regardless of
// the color system, and it's an icon, not a fill.
export default function MilestoneCard({ title, missionsDone, missionsTotal, xpReward }: MilestoneCardProps) {
  const progress = missionsTotal > 0 ? missionsDone / missionsTotal : 0;
  const pct = Math.round(Math.min(Math.max(progress, 0), 1) * 100);

  return (
    <View style={styles.card}>
      <View style={styles.titleRow}>
        <Ionicons name="trophy" size={13} color={colors.xp} />
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>
        <Text style={styles.percent}>{pct}%</Text>
      </View>

      <View style={styles.track}>
        <View style={[styles.fill, { width: `${pct}%` }]} />
      </View>

      <Text style={styles.metaText}>
        {missionsDone}/{missionsTotal} missões · +{xpReward} XP
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginTop: spacing.md,
  },
  titleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  title: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    color: colors.textPrimary,
    flex: 1,
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
  metaText: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
  },
});