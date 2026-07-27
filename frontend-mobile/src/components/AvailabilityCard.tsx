import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

const DAYS = [
  { key: 'dom', label: 'D', full: 'Domingo' },
  { key: 'seg', label: 'S', full: 'Segunda' },
  { key: 'ter', label: 'T', full: 'Terça' },
  { key: 'qua', label: 'Q', full: 'Quarta' },
  { key: 'qui', label: 'Q', full: 'Quinta' },
  { key: 'sex', label: 'S', full: 'Sexta' },
  { key: 'sab', label: 'S', full: 'Sábado' },
] as const;

const PERIODS = [
  { key: 'manha', label: 'Manhã' },
  { key: 'tarde', label: 'Tarde' },
  { key: 'noite', label: 'Noite' },
] as const;

type AvailabilityCardProps = {
  selectedDays: string[];
  onToggleDay: (key: string) => void;
  selectedPeriod: string;
  onSelectPeriod: (key: string) => void;
};

export default function AvailabilityCard({
  selectedDays,
  onToggleDay,
  selectedPeriod,
  onSelectPeriod,
}: AvailabilityCardProps) {
  return (
    <View style={styles.card}>
      <Text style={styles.title}>Seus melhores horários</Text>
      <Text style={styles.subtitle}>Usamos isso pra sugerir o melhor momento pras suas missões</Text>

      <View style={styles.dayRow}>
        {DAYS.map((day) => {
          const selected = selectedDays.includes(day.key);
          return (
            <TouchableOpacity
              key={day.key}
              style={styles.dayTouchable}
              hitSlop={{ top: 4, bottom: 4, left: 4, right: 4 }}
              onPress={() => onToggleDay(day.key)}
              accessibilityRole="checkbox"
              accessibilityState={{ checked: selected }}
              accessibilityLabel={day.full}
            >
              <View style={[styles.dayCircle, selected && styles.dayCircleSelected]}>
                <Text style={[styles.dayLabel, selected && styles.dayLabelSelected]}>{day.label}</Text>
              </View>
            </TouchableOpacity>
          );
        })}
      </View>

      <View style={styles.periodRow}>
        {PERIODS.map((period) => {
          const selected = period.key === selectedPeriod;
          return (
            <TouchableOpacity
              key={period.key}
              style={[styles.periodButton, selected && styles.periodButtonSelected]}
              onPress={() => onSelectPeriod(period.key)}
              accessibilityRole="radio"
              accessibilityState={{ checked: selected }}
              accessibilityLabel={period.label}
            >
              <Text style={[styles.periodLabel, selected && styles.periodLabelSelected]}>{period.label}</Text>
            </TouchableOpacity>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  dayRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  dayTouchable: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dayCircle: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: colors.neutralTint,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  dayCircleSelected: {
    backgroundColor: colors.primary,
    borderColor: colors.primary,
  },
  dayLabel: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  dayLabelSelected: {
    color: colors.textOnPrimary,
  },
  periodRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  periodButton: {
    flex: 1,
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: spacing.sm,
  },
  periodButtonSelected: {
    backgroundColor: colors.primaryTint,
    borderColor: colors.primaryText,
  },
  periodLabel: {
    ...typography.body,
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.textSecondary,
  },
  periodLabelSelected: {
    color: colors.primaryText,
  },
});
