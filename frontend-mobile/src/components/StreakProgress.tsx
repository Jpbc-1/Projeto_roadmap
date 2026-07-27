import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

type StreakProgressProps = {
  /** Short-term: consecutive days, resets on a real miss */
  currentStreak: number;
  /** Long-term: the next big milestone this streak is building toward */
  nextMilestone: number;
  /** How many "misses" are currently protected — an occasional slip doesn't zero the streak */
  freezesAvailable: number;
};

// Deliberately quiet — a thin strip, not a card: no shadow, no border,
// minimal padding. Keeps a flat cream backing (not sitting bare on the
// wood) because the streak-orange text/icon only holds contrast on a
// light surface, not directly on the wood tone — verified, not assumed.
// Still carries both the short-term count and the long-term milestone
// (per "streak + marcos coexistem"), just as compact as that pairing
// can get: one row, one thin bar.
export default function StreakProgress({ currentStreak, nextMilestone, freezesAvailable }: StreakProgressProps) {
  const progress = Math.min(Math.max(currentStreak / nextMilestone, 0), 1);

  return (
    <View style={styles.row}>
      <View style={styles.headerRow}>
        <View style={styles.streakLabel}>
          <Ionicons name="flame" size={15} color={colors.streak} />
          <Text style={styles.streakNumber}>{currentStreak}</Text>
          <Text style={styles.streakText}>dias · meta {nextMilestone}</Text>
        </View>

        {freezesAvailable > 0 && (
          <View style={styles.freezeBadge}>
            <Ionicons name="shield-checkmark" size={12} color={colors.streak} />
            <Text style={styles.freezeText}>{freezesAvailable}</Text>
          </View>
        )}
      </View>

      <View style={styles.track}>
        <View style={[styles.fill, { width: `${progress * 100}%` }]} />
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginTop: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  streakLabel: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  streakNumber: {
    fontFamily: fonts.display,
    fontSize: 16,
    color: colors.streakText,
  },
  streakText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  freezeBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.streakTint,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.pill,
  },
  freezeText: {
    ...typography.caption,
    fontSize: 11,
    color: colors.streakText,
  },
  track: {
    height: spacing.sm,
    backgroundColor: colors.border,
    borderRadius: radius.pill,
  },
  fill: {
    height: spacing.sm,
    backgroundColor: colors.streak,
    borderRadius: radius.pill,
  },
});