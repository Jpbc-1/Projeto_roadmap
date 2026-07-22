import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography } from '../theme/colors';

type MissionCardProps = {
  /** Short breadcrumb, e.g. "Capítulo 2 · Rumo ao Primeiro Estágio" */
  context: string;
  /** 0 to 1 — chapter completion, shown as "% do capítulo" instead of a mission count */
  chapterProgress: number;
  /** The big, personality-driven line — an invitation, never a guilt trip */
  message: string;
  xp: number;
  minutes: number;
  onFinish: () => void;
};

export default function MissionCard({
  context,
  chapterProgress,
  message,
  xp,
  minutes,
  onFinish,
}: MissionCardProps) {
  const pct = Math.round(Math.min(Math.max(chapterProgress, 0), 1) * 100);

  return (
    // Gradient goes primary -> primaryDark. Both endpoints (and every point
    // between) hold >=5.3:1 with white text, so text placement anywhere on
    // this card is safe — no part of the card is a "quiet" low-contrast zone.
    <LinearGradient
      colors={[colors.primary, colors.primaryDark]}
      start={{ x: 0, y: 0 }}
      end={{ x: 1, y: 1 }}
      style={styles.card}
    >
      <Text style={styles.eyebrow}>{context.toUpperCase()}</Text>

      <View style={styles.progressRow}>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${pct}%` }]} />
        </View>
        <Text style={styles.progressLabel}>{pct}% do capítulo</Text>
      </View>

      <Text style={styles.message}>{message}</Text>

      <View style={styles.metaRow}>
        <View style={styles.metaItem}>
          <Ionicons name="flash" size={14} color={colors.textOnPrimary} />
          <Text style={styles.metaText}>{xp} XP</Text>
        </View>
        <View style={styles.metaDot} />
        <View style={styles.metaItem}>
          <Ionicons name="time-outline" size={14} color={colors.textOnPrimary} />
          <Text style={styles.metaText}>{minutes} min</Text>
        </View>
      </View>

      <TouchableOpacity
        style={styles.button}
        onPress={onFinish}
        activeOpacity={0.85}
        accessibilityRole="button"
        accessibilityLabel="Finalizar missão"
      >
        <Ionicons name="checkmark-circle" size={18} color={colors.textOnPrimary} />
        <Text style={styles.buttonText}>Finalizar missão</Text>
      </TouchableOpacity>
    </LinearGradient>
  );
}

const styles = StyleSheet.create({
  card: {
    borderRadius: radius.lg,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  eyebrow: {
    ...typography.eyebrow,
    color: colors.textOnPrimary,
    marginBottom: spacing.sm,
  },
  progressRow: {
    marginBottom: spacing.md,
  },
  progressTrack: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.overlayOnPrimary,
    marginBottom: spacing.sm,
  },
  progressFill: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.textOnPrimary,
  },
  progressLabel: {
    ...typography.caption,
    color: colors.textOnPrimary,
  },
  message: {
    ...typography.h1,
    fontSize: 24,
    lineHeight: 30,
    color: colors.textOnPrimary,
    marginBottom: spacing.md,
  },
  metaRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.md,
  },
  metaItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  metaText: {
    ...typography.caption,
    color: colors.textOnPrimary,
  },
  metaDot: {
    width: 3,
    height: 3,
    borderRadius: 2,
    backgroundColor: colors.textOnPrimary,
    marginHorizontal: spacing.sm,
  },
  button: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.success,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    minHeight: 48,
  },
  buttonText: {
    ...typography.h2,
    color: colors.textOnPrimary,
  },
});