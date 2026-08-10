import React from 'react';
import { Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';
import { AgendaItem } from '../hooks/useAgenda';
import { formatDurationMinutes, formatHM } from '../utils/dateUtils';

type AgendaEventCardProps = {
  item: AgendaItem;
  onPress?: () => void;
};

// Reminder and CalendarEvent aren't a new 6th color system — they're
// "planning" (reuses primary, same meaning colors.ts already gives it)
// vs the neutral bucket (reminders are closer to a utility tag than a
// brand moment). Picking a brand-new hex here would mean a brand-new
// unverified contrast ratio, which is exactly what colors.ts's header
// comment says not to do.
function accentFor(kind: AgendaItem['kind']) {
  if (kind === 'reminder') {
    return { border: colors.neutralIcon, iconBg: colors.neutralTint, icon: colors.neutralIcon };
  }
  return { border: colors.primaryText, iconBg: colors.primaryTint, icon: colors.primaryText };
}

export default function AgendaEventCard({ item, onPress }: AgendaEventCardProps) {
  const accent = accentFor(item.kind);
  const icon = item.kind === 'reminder' ? 'notifications' : 'calendar-clear';
  const timeLabel =
    item.durationMinutes != null
      ? `${formatHM(item.time)} · ${formatDurationMinutes(item.durationMinutes)}`
      : formatHM(item.time);

  return (
    <TouchableOpacity
      style={[styles.card, { borderLeftColor: accent.border }]}
      onPress={onPress}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={`${item.title}, ${timeLabel}`}
    >
      <View style={[styles.iconBadge, { backgroundColor: accent.iconBg }]}>
        <Ionicons name={icon} size={14} color={accent.icon} />
      </View>
      <View style={styles.textBlock}>
        <Text style={styles.title} numberOfLines={1}>
          {item.title}
        </Text>
        <Text style={[styles.time, { color: accent.icon }]}>{timeLabel}</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    borderLeftWidth: 3,
    padding: spacing.sm,
    // Same flat, physical-object shadow as MissionCard's post-it, at a
    // much smaller scale — enough to read as "a card sitting on the
    // board", not enough to compete with the hero card on Home.
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.14,
    shadowRadius: 3,
    elevation: 3,
  },
  iconBadge: {
    width: 26,
    height: 26,
    borderRadius: radius.sm,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textBlock: {
    flex: 1,
  },
  title: {
    ...typography.cardTitle,
    fontSize: 13,
    color: colors.textPrimary,
  },
  time: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
    marginTop: 2,
  },
});
