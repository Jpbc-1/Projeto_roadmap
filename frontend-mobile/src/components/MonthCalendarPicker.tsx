import React, { useMemo, useState } from 'react';
import { Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import { WEEKDAY_SHORT, formatMonthYear, isSameDay } from '../utils/dateUtils';

type MonthCalendarPickerProps = {
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
};

type Cell = { date: Date | null };

// Same weekday-offset-then-chunk-into-7 approach as MonthHeatmap on the
// Home tab — proven date-grid math, just adapted for tap-to-select
// instead of a completion heatmap.
function buildMonthGrid(monthAnchor: Date): Cell[][] {
  const year = monthAnchor.getFullYear();
  const month = monthAnchor.getMonth();
  const daysInMonth = new Date(year, month + 1, 0).getDate();
  const firstWeekday = new Date(year, month, 1).getDay();

  const cells: Cell[] = [
    ...Array.from({ length: firstWeekday }, () => ({ date: null })),
    ...Array.from({ length: daysInMonth }, (_, i) => ({ date: new Date(year, month, i + 1) })),
  ];
  while (cells.length % 7 !== 0) cells.push({ date: null });

  const weeks: Cell[][] = [];
  for (let i = 0; i < cells.length; i += 7) weeks.push(cells.slice(i, i + 7));
  return weeks;
}

export default function MonthCalendarPicker({ selectedDate, onSelectDate }: MonthCalendarPickerProps) {
  // The visible month can differ from the selected date (browsing to a
  // future month before picking a day in it), so it's its own state.
  const [visibleMonth, setVisibleMonth] = useState(() => new Date(selectedDate.getFullYear(), selectedDate.getMonth(), 1));
  const today = new Date();

  const weeks = useMemo(() => buildMonthGrid(visibleMonth), [visibleMonth]);

  function goToMonth(delta: number) {
    setVisibleMonth((prev) => new Date(prev.getFullYear(), prev.getMonth() + delta, 1));
  }

  return (
    <View style={styles.card}>
      <View style={styles.header}>
        <TouchableOpacity
          onPress={() => goToMonth(-1)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          accessibilityRole="button"
          accessibilityLabel="Mês anterior"
        >
          <Ionicons name="chevron-back" size={18} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.monthLabel}>{formatMonthYear(visibleMonth)}</Text>
        <TouchableOpacity
          onPress={() => goToMonth(1)}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          accessibilityRole="button"
          accessibilityLabel="Próximo mês"
        >
          <Ionicons name="chevron-forward" size={18} color={colors.textPrimary} />
        </TouchableOpacity>
      </View>

      <View style={styles.weekdayRow}>
        {WEEKDAY_SHORT.map((label, i) => (
          <Text key={i} style={styles.weekdayLabel}>
            {label}
          </Text>
        ))}
      </View>

      {weeks.map((week, wi) => (
        <View key={wi} style={styles.weekRow}>
          {week.map((cell, ci) => {
            if (!cell.date) return <View key={ci} style={styles.dayCell} />;
            const date = cell.date;
            const isSelected = isSameDay(date, selectedDate);
            const isToday = isSameDay(date, today);
            return (
              <TouchableOpacity
                key={ci}
                style={styles.dayCell}
                onPress={() => onSelectDate(date)}
                accessibilityRole="button"
                accessibilityLabel={`${date.getDate()} de ${formatMonthYear(date)}`}
                accessibilityState={{ selected: isSelected }}
              >
                <View style={[styles.dayInner, isSelected && styles.dayInnerSelected, !isSelected && isToday && styles.dayInnerToday]}>
                  <Text style={[styles.dayNumber, isSelected && styles.dayNumberSelected]}>{date.getDate()}</Text>
                </View>
              </TouchableOpacity>
            );
          })}
        </View>
      ))}
    </View>
  );
}

const CELL_SIZE = 40;

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.sm,
    marginTop: spacing.sm,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: touchTarget - 8,
    paddingHorizontal: spacing.sm,
  },
  monthLabel: {
    ...typography.cardTitle,
    color: colors.textPrimary,
  },
  weekdayRow: {
    flexDirection: 'row',
    marginTop: spacing.sm,
  },
  weekdayLabel: {
    width: CELL_SIZE,
    textAlign: 'center',
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
  },
  weekRow: {
    flexDirection: 'row',
  },
  dayCell: {
    width: CELL_SIZE,
    height: CELL_SIZE,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dayInner: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dayInnerSelected: {
    backgroundColor: colors.textPrimary,
  },
  dayInnerToday: {
    borderWidth: 1,
    borderColor: colors.primaryText,
  },
  dayNumber: {
    ...typography.caption,
    color: colors.textPrimary,
  },
  dayNumberSelected: {
    fontFamily: fonts.bodySemiBold,
    color: colors.surface,
  },
});
