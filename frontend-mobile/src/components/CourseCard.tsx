import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, touchTarget } from '../theme/colors';

// Accent is a closed set of two theme-defined categories — not a free hex
// prop — so a course card can never accidentally reuse a color that
// already means something else elsewhere in the app.
const ACCENTS = {
  blue: { fg: colors.courseBlue, bg: colors.courseBlueTint },
  teal: { fg: colors.courseTeal, bg: colors.courseTealTint },
} as const;

type CourseCardProps = {
  accent: keyof typeof ACCENTS;
  icon: keyof typeof Ionicons.glyphMap;
  /** Roadmap name, e.g. "Domine o Python" */
  title: string;
  /** That roadmap's specific mission for today, e.g. "Aprenda Dicionário" —
   * NOT a generic course tagline. Each card here already represents "this
   * roadmap's mission for today," the same as the hero MissionCard above,
   * just for a roadmap that isn't the featured one right now. */
  subtitle: string;
  /** 0 to 1 */
  progress: number;
  onPress?: () => void;
};

export default function CourseCard({ accent, icon, title, subtitle, progress, onPress }: CourseCardProps) {
  const { fg, bg } = ACCENTS[accent];

  return (
    <TouchableOpacity
      style={styles.card}
      onPress={onPress}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={`${title}, ${subtitle}`}
    >
      <View style={[styles.iconBadge, { backgroundColor: bg }]}>
        <Ionicons name={icon} size={20} color={fg} />
      </View>
      <Text style={styles.title} numberOfLines={1}>
        {title}
      </Text>
      <Text style={styles.subtitle} numberOfLines={1}>
        {subtitle}
      </Text>
      <View style={styles.progressTrack}>
        <View style={[styles.progressFill, { width: `${Math.min(Math.max(progress, 0), 1) * 100}%`, backgroundColor: fg }]} />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  card: {
    flex: 1,
    minHeight: touchTarget,
    backgroundColor: colors.surface,
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  iconBadge: {
    width: 32,
    height: 32,
    borderRadius: radius.sm,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  title: {
    ...typography.h2,
    fontSize: 14,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginBottom: spacing.md,
  },
  progressTrack: {
    height: spacing.sm,
    backgroundColor: colors.border,
    borderRadius: radius.pill,
  },
  progressFill: {
    height: spacing.sm,
    borderRadius: radius.pill,
  },
});