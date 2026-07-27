import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, touchTarget } from '../theme/colors';

type ReviewCardProps = {
  pendingCount: number;
  onPress?: () => void;
};

// Purple = reviews/knowledge, the one accent this row gets. Still calm —
// a single tinted icon badge, not a saturated full-card treatment — this
// is a supporting action, not something competing with the hero mission.
export default function ReviewCard({ pendingCount, onPress }: ReviewCardProps) {
  return (
    <TouchableOpacity
      style={styles.row}
      onPress={onPress}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={`Revisão, ${pendingCount} itens pendentes`}
    >
      <View style={styles.iconBadge}>
        <Ionicons name="repeat-outline" size={18} color={colors.reviews} />
      </View>
      <View style={styles.textBlock}>
        <Text style={styles.title}>Revisão</Text>
        <Text style={styles.meta}>{pendingCount} itens pendentes</Text>
      </View>
      <Ionicons name="chevron-forward" size={16} color={colors.textSecondary} />
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  row: {
    minHeight: touchTarget,
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  iconBadge: {
    width: 32,
    height: 32,
    borderRadius: radius.sm,
    backgroundColor: colors.reviewsTint,
    justifyContent: 'center',
    alignItems: 'center',
  },
  textBlock: {
    flex: 1,
  },
  title: {
    ...typography.cardTitle,
    fontSize: 14,
    color: colors.textPrimary,
  },
  meta: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
});