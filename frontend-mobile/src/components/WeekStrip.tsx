import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import { WEEKDAY_SHORT, isSameDay, weekDays } from '../utils/dateUtils';

type WeekStripProps = {
  anchor: Date;
  selectedDate: Date;
  onSelectDate: (date: Date) => void;
  /** Days (within this week) that have at least one calendar event —
   * drawn as a small dot, same idea as MonthHeatmap's activeDot but for
   * "has something scheduled" instead of "completed a mission". */
  daysWithEvents?: Date[];
};

export default function WeekStrip({ anchor, selectedDate, onSelectDate, daysWithEvents = [] }: WeekStripProps) {
  const days = weekDays(anchor);
  const today = new Date();

  return (
    <View style={styles.row}>
      {days.map((day) => {
        const isSelected = isSameDay(day, selectedDate);
        const isToday = isSameDay(day, today);
        const hasEvent = daysWithEvents.some((d) => isSameDay(d, day));

        return (
          <TouchableOpacity
            key={day.toISOString()}
            style={styles.cell}
            onPress={() => onSelectDate(day)}
            activeOpacity={0.75}
            accessibilityRole="button"
            accessibilityLabel={`${WEEKDAY_SHORT[day.getDay()]}, dia ${day.getDate()}`}
            accessibilityState={{ selected: isSelected }}
          >
            <Text style={styles.weekdayLabel}>{WEEKDAY_SHORT[day.getDay()]}</Text>
            <View
              style={[
                styles.dayCircle,
                isSelected && styles.dayCircleSelected,
                !isSelected && isToday && styles.dayCircleToday,
              ]}
            >
              <Text
                style={[
                  styles.dayNumber,
                  isSelected && styles.dayNumberSelected,
                  !isSelected && isToday && styles.dayNumberToday,
                ]}
              >
                {day.getDate()}
              </Text>
            </View>
            <View style={[styles.dot, hasEvent && !isSelected && styles.dotVisible]} />
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const CIRCLE_SIZE = 36;

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: spacing.md,
  },
  cell: {
    flex: 1,
    minHeight: touchTarget,
    alignItems: 'center',
    gap: spacing.sm,
  },
  weekdayLabel: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
  },
  dayCircle: {
    width: CIRCLE_SIZE,
    height: CIRCLE_SIZE,
    borderRadius: CIRCLE_SIZE / 2,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dayCircleSelected: {
    backgroundColor: colors.textPrimary,
  },
  dayCircleToday: {
    borderWidth: 1.5,
    borderColor: colors.primaryText,
  },
  dayNumber: {
    fontFamily: fonts.displayMedium,
    fontSize: 15,
    color: colors.textSecondary,
  },
  dayNumberSelected: {
    color: colors.surface,
    fontFamily: fonts.display,
  },
  dayNumberToday: {
    color: colors.primaryText,
    fontFamily: fonts.displaySemiBold,
  },
  dot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: 'transparent',
  },
  dotVisible: {
    backgroundColor: colors.primary,
  },
});
