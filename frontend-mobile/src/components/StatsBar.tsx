import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography } from '../theme/colors';

type StatsBarProps = {
  level: number;
  xp: number;
  streakDays: number;
  badgeCount: number;
};

type PillProps = {
  icon: keyof typeof Ionicons.glyphMap;
  iconColor: string;
  tint: string;
  label: string;
};

// Text is ALWAYS textPrimary, never the accent color — color-coding lives
// entirely in the icon. This keeps every pill readable regardless of hue,
// and means no stat "loses" its color story to a contrast fix later.
function StatPill({ icon, iconColor, tint, label }: PillProps) {
  return (
    <View style={[styles.pill, { backgroundColor: tint }]}>
      <Ionicons name={icon} size={14} color={iconColor} />
      <Text style={styles.pillText}>{label}</Text>
    </View>
  );
}

// Level and badge count are neutral on purpose (see theme/colors.ts) —
// only streak and XP get a reserved accent color, since those are the two
// mechanics this app actively wants to reinforce every day.
export default function StatsBar({ level, xp, streakDays, badgeCount }: StatsBarProps) {
  return (
    <ScrollView
      horizontal
      showsHorizontalScrollIndicator={false}
      contentContainerStyle={styles.row}
    >
      <StatPill icon="star" iconColor={colors.neutralIcon} tint={colors.neutralTint} label={`Nível ${level}`} />
      <StatPill icon="flash" iconColor={colors.xp} tint={colors.xpTint} label={`${xp} XP`} />
      <StatPill icon="flame" iconColor={colors.streak} tint={colors.streakTint} label={`${streakDays} dias`} />
      <StatPill icon="trophy" iconColor={colors.neutralIcon} tint={colors.neutralTint} label={`${badgeCount}`} />
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
    paddingRight: spacing.sm,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
  },
  pillText: {
    ...typography.caption,
    color: colors.textPrimary,
  },
});