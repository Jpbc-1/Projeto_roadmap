import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

type StudyReminderProps = {
  time: string;
  label: string;
};

// Same flat, no-shadow tier as StreakProgress/MilestoneCard — a light
// cream strip with a small colored icon badge. Went too quiet as a bare
// text line on wood (barely noticeable); this brings back enough
// presence to actually register at a glance without turning into a
// full saturated banner again.
export default function StudyReminder({ time, label }: StudyReminderProps) {
  return (
    <View style={styles.row}>
      <View style={styles.iconBadge}>
        <Ionicons name="notifications" size={14} color={colors.xp} />
      </View>
      <Text style={styles.text}>
        Hoje às <Text style={styles.time}>{time}</Text> — {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    padding: spacing.sm,
    marginTop: spacing.md,
  },
  iconBadge: {
    width: 28,
    height: 28,
    borderRadius: radius.sm,
    backgroundColor: colors.xpTint,
    alignItems: 'center',
    justifyContent: 'center',
  },
  text: {
    ...typography.caption,
    color: colors.textPrimary,
    flex: 1,
  },
  time: {
    fontFamily: fonts.bodySemiBold,
    color: colors.xp,
  },
});