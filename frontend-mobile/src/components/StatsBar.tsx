import React from 'react';
import { View, Text, ScrollView, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography } from '../theme/colors';

type StatsBarProps = {
  level: number;
  badgeCount: number;
};

type PillProps = {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
};

// Both neutral — level and badge count are identity/status, not one of
// the app's 5 meaningful accent systems. Text is always textPrimary,
// never an accent color; color-coding (where it exists) lives in icons.
function StatPill({ icon, label }: PillProps) {
  return (
    <View style={styles.pill}>
      <Ionicons name={icon} size={14} color={colors.neutralIcon} />
      <Text style={styles.pillText}>{label}</Text>
    </View>
  );
}

// No raw XP total here on purpose — the product spec is explicit that
// gamification should show evolution, not a running point count. XP still
// shows up as a reward tag on the mission card, right when it's earned.
export default function StatsBar({ level, badgeCount }: StatsBarProps) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.row}>
      <StatPill icon="star" label={`Nível ${level}`} />
      <StatPill icon="trophy" label={`${badgeCount} conquistas`} />
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
    backgroundColor: colors.neutralTint,
  },
  pillText: {
    ...typography.caption,
    color: colors.textPrimary,
  },
});
