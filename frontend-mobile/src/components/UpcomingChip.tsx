import React from 'react';
import { Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, touchTarget } from '../theme/colors';
import { AgendaItem } from '../hooks/useAgenda';
import { relativeDayLabel } from '../utils/dateUtils';

type UpcomingChipProps = {
  item: AgendaItem;
  colorIndex: number;
  onDismiss: () => void;
};

// Same postIt palette as "Suas outras missões" on Home — colors.ts is
// explicit that this set is decorative variety with no fixed meaning
// (unlike the 5 semantic colors), which is exactly the job here: tell
// consecutive chips apart at a glance, nothing more.
const CHIP_COLORS = [colors.postIt.yellow, colors.postIt.blue, colors.postIt.pink, colors.postIt.green, colors.postIt.peach];

export default function UpcomingChip({ item, colorIndex, onDismiss }: UpcomingChipProps) {
  const backgroundColor = CHIP_COLORS[colorIndex % CHIP_COLORS.length];

  return (
    <View style={[styles.chip, { backgroundColor }]}>
      <Ionicons name="calendar-clear-outline" size={14} color={colors.textSecondaryOnPastel} />
      <Text style={styles.label} numberOfLines={1}>
        {item.title} · {relativeDayLabel(item.time)}
      </Text>
      <TouchableOpacity
        onPress={onDismiss}
        hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
        accessibilityRole="button"
        accessibilityLabel={`Remover ${item.title}`}
      >
        <Ionicons name="close" size={14} color={colors.textSecondaryOnPastel} />
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: 36,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    marginRight: spacing.sm,
    maxWidth: 220,
  },
  label: {
    ...typography.caption,
    color: colors.textSecondaryOnPastel,
    flexShrink: 1,
  },
});
