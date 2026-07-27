import React from 'react';
import { View, Text, Switch, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

const FREQUENCIES = [
  { key: 'poucas', label: 'Poucas' },
  { key: 'moderadas', label: 'Moderadas' },
  { key: 'frequentes', label: 'Frequentes' },
] as const;

const QUIET_HOURS = [
  { key: 'noite', label: '22h – 8h' },
  { key: 'trabalho', label: '9h – 18h' },
  { key: 'nenhum', label: 'Nenhum' },
] as const;

type NotificationCardProps = {
  enabled: boolean;
  onToggleEnabled: (value: boolean) => void;
  frequency: string;
  onSelectFrequency: (key: string) => void;
  quietHours: string;
  onSelectQuietHours: (key: string) => void;
};

export default function NotificationCard({
  enabled,
  onToggleEnabled,
  frequency,
  onSelectFrequency,
  quietHours,
  onSelectQuietHours,
}: NotificationCardProps) {
  return (
    <View style={styles.card}>
      <View style={styles.headerRow}>
        <View style={styles.headerText}>
          <Text style={styles.title}>Notificações</Text>
          <Text style={styles.subtitle}>Por comportamento, nunca por cobrança</Text>
        </View>
        <Switch
          value={enabled}
          onValueChange={onToggleEnabled}
          trackColor={{ false: colors.border, true: colors.primaryText }}
          thumbColor={colors.iconOnDark}
          accessibilityLabel="Ativar notificações"
        />
      </View>

      <View style={[styles.section, !enabled && styles.sectionDisabled]} pointerEvents={enabled ? 'auto' : 'none'}>
        <Text style={styles.label}>Frequência</Text>
        <View style={styles.chipRow}>
          {FREQUENCIES.map((item) => {
            const selected = item.key === frequency;
            return (
              <TouchableOpacity
                key={item.key}
                style={[styles.chip, selected && styles.chipSelected]}
                onPress={() => onSelectFrequency(item.key)}
                accessibilityRole="radio"
                accessibilityState={{ checked: selected, disabled: !enabled }}
              >
                <Text style={[styles.chipLabel, selected && styles.chipLabelSelected]}>{item.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <Text style={[styles.label, styles.labelSpaced]}>Não perturbe</Text>
        <View style={styles.chipRow}>
          {QUIET_HOURS.map((item) => {
            const selected = item.key === quietHours;
            return (
              <TouchableOpacity
                key={item.key}
                style={[styles.chip, selected && styles.chipSelected]}
                onPress={() => onSelectQuietHours(item.key)}
                accessibilityRole="radio"
                accessibilityState={{ checked: selected, disabled: !enabled }}
              >
                <Text style={[styles.chipLabel, selected && styles.chipLabelSelected]}>{item.label}</Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.exampleRow}>
          <Ionicons name="chatbubble-ellipses-outline" size={16} color={colors.textSecondary} />
          <Text style={styles.exampleText}>"Sua missão de hoje tá te esperando 👋"</Text>
        </View>
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
    marginTop: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  headerText: {
    flex: 1,
    marginRight: spacing.md,
  },
  title: {
    ...typography.cardTitle,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  section: {
    marginTop: spacing.md,
  },
  sectionDisabled: {
    opacity: 0.4,
  },
  label: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.sm,
  },
  labelSpaced: {
    marginTop: spacing.md,
  },
  chipRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  chip: {
    minHeight: 44,
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.sm,
  },
  chipSelected: {
    backgroundColor: colors.primaryTint,
    borderColor: colors.primaryText,
  },
  chipLabel: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    color: colors.textSecondary,
  },
  chipLabelSelected: {
    color: colors.primaryText,
  },
  exampleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
    padding: spacing.sm,
    backgroundColor: colors.neutralTint,
    borderRadius: radius.md,
  },
  exampleText: {
    ...typography.caption,
    color: colors.textSecondary,
    flex: 1,
  },
});
