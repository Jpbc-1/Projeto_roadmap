import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography } from '../theme/colors';

type StreakProgressProps = {
  /** Short-term: consecutive days, resets on a real miss */
  currentStreak: number;
  /** Long-term: the next big milestone this streak is building toward */
  nextMilestone: number;
  /** How many "misses" are currently protected — an occasional slip doesn't zero the streak */
  freezesAvailable: number;
};

export default function StreakProgress({ currentStreak, nextMilestone, freezesAvailable }: StreakProgressProps) {
  const progress = Math.min(Math.max(currentStreak / nextMilestone, 0), 1);
  const daysLeft = Math.max(nextMilestone - currentStreak, 0);

  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.streakLabel}>
          <Ionicons name="flame" size={18} color={colors.streak} />
          <Text style={styles.streakText}>{currentStreak} dias seguidos</Text>
        </View>

        {freezesAvailable > 0 && (
          <View style={styles.freezeBadge}>
            <Ionicons name="shield-checkmark" size={14} color={colors.streak} />
            <Text style={styles.freezeText}>
              {freezesAvailable} proteção{freezesAvailable > 1 ? 'ões' : ''}
            </Text>
          </View>
        )}
      </View>

      <View style={styles.track}>
        <View style={[styles.fill, { width: `${progress * 100}%` }]} />
        <View style={[styles.marker, { left: `${progress * 100}%` }]}>
          <View style={styles.markerCircle}>
            <Ionicons name="flame" size={12} color={colors.textOnPrimary} />
          </View>
        </View>
      </View>

      <View style={styles.milestoneRow}>
        <Text style={styles.milestoneText}>0</Text>
        <Text style={styles.milestoneText}>{nextMilestone} dias</Text>
      </View>

      <Text style={styles.caption}>
        {daysLeft > 0
          ? `Faltam ${daysLeft} dias para a sua próxima meta`
          : 'Meta alcançada! Uma nova está a caminho'}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  streakLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  streakText: {
    ...typography.h2,
    color: colors.textPrimary,
  },
  freezeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.streakTint,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
  },
  freezeText: {
    ...typography.caption,
    color: colors.textPrimary,
  },
  track: {
    height: spacing.sm,
    backgroundColor: colors.border,
    borderRadius: radius.pill,
    justifyContent: 'center',
  },
  fill: {
    position: 'absolute',
    left: 0,
    top: 0,
    bottom: 0,
    backgroundColor: colors.streak,
    borderRadius: radius.pill,
  },
  marker: {
    position: 'absolute',
    // Not a spacing value — this is -1 * (markerCircle width / 2), which
    // centers the 24px circle exactly on the fill's edge. It's derived
    // from the marker's own size, so it's exempt from the 8px grid the
    // same way a border-radius half-width would be.
    marginLeft: -12,
  },
  markerCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.streak,
    borderWidth: 2,
    borderColor: colors.surface,
    justifyContent: 'center',
    alignItems: 'center',
  },
  milestoneRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  milestoneText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  caption: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
});