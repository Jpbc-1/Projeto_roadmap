import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography, fonts } from '../theme/colors';

type StudyReminderProps = {
  time: string;
  label: string;
};

// Neutral surface instead of a colored tint fill — this is a passing
// note, not something competing for attention.
export default function StudyReminder({ time, label }: StudyReminderProps) {
  return (
    <View style={styles.banner}>
      <Ionicons name="notifications-outline" size={13} color={colors.textOnWoodMuted} />
      <Text style={styles.text}>
        Hoje às <Text style={styles.time}>{time}</Text> — {label}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    marginTop: spacing.sm,
  },
  text: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textOnWoodMuted,
    flex: 1,
  },
  time: {
    fontFamily: fonts.bodySemiBold,
  },
});