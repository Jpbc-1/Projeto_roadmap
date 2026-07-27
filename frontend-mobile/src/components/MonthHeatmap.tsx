import React, { useMemo } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

const MONTH_NAMES = [
  'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
  'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro',
];
const WEEKDAY_HEADERS = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S'];

type MonthHeatmapProps = {
  /** Days of the current month (1-31) that had at least one completed mission */
  activeDays: number[];
};

type Cell = { day: number | null };

export default function MonthHeatmap({ activeDays }: MonthHeatmapProps) {
  const today = new Date();

  const { weeks, monthLabel } = useMemo(() => {
    const year = today.getFullYear();
    const month = today.getMonth();
    const daysInMonth = new Date(year, month + 1, 0).getDate();
    const firstWeekday = new Date(year, month, 1).getDay(); // 0 = Sunday

    const cells: Cell[] = [
      ...Array.from({ length: firstWeekday }, () => ({ day: null })),
      ...Array.from({ length: daysInMonth }, (_, i) => ({ day: i + 1 })),
    ];
    while (cells.length % 7 !== 0) cells.push({ day: null });

    const weekRows: Cell[][] = [];
    for (let i = 0; i < cells.length; i += 7) {
      weekRows.push(cells.slice(i, i + 7));
    }

    return { weeks: weekRows, monthLabel: `${MONTH_NAMES[month]} de ${year}` };
    // today is read once per mount/day, not a reactive dependency here
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const activeSet = new Set(activeDays);
  const todayNum = today.getDate();

  return (
    <View style={styles.card}>
      <Text style={styles.title}>Consistência do mês</Text>
      <Text style={styles.monthLabel}>{monthLabel}</Text>

      <View style={styles.weekdayRow}>
        {WEEKDAY_HEADERS.map((label, i) => (
          <Text key={i} style={styles.weekdayLabel}>
            {label}
          </Text>
        ))}
      </View>

      {weeks.map((week, wi) => (
        <View key={wi} style={styles.weekRow}>
          {week.map((cell, ci) => {
            if (cell.day === null) return <View key={ci} style={styles.dayCell} />;
            const isToday = cell.day === todayNum;
            const isActive = activeSet.has(cell.day);
            return (
              <View key={ci} style={styles.dayCell}>
                <View style={[styles.dayInner, isToday && styles.dayInnerToday]}>
                  <Text style={[styles.dayNumber, isToday && styles.dayNumberToday]}>{cell.day}</Text>
                  {isActive && <View style={styles.activeDot} />}
                </View>
              </View>
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
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary,
  },
  monthLabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  weekdayRow: {
    flexDirection: 'row',
    marginBottom: spacing.sm,
  },
  weekdayLabel: {
    width: CELL_SIZE,
    textAlign: 'center',
    ...typography.caption,
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
  dayInnerToday: {
    borderWidth: 1,
    borderColor: colors.primaryText,
  },
  dayNumber: {
    ...typography.caption,
    color: colors.textPrimary,
  },
  dayNumberToday: {
    fontFamily: fonts.bodySemiBold,
    color: colors.primaryText,
  },
  activeDot: {
    position: 'absolute',
    bottom: 2,
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: colors.streak,
  },
});
