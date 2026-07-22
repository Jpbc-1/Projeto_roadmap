import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, touchTarget } from '../theme/colors';

type TodayItemProps = {
  icon: keyof typeof Ionicons.glyphMap;
  title: string;
  meta: string;
  onPress?: () => void;
};


export default function TodayItem({ icon, title, meta, onPress }: TodayItemProps) {
  return (
    <TouchableOpacity
      style={styles.row}
      onPress={onPress}
      activeOpacity={0.8}
      accessibilityRole="button"
      accessibilityLabel={`${title}, ${meta}`}
    >
      <View style={styles.iconBadge}>
        <Ionicons name={icon} size={18} color={colors.neutralIcon} />
      </View>
      <View style={styles.textBlock}>
        <Text style={styles.title} numberOfLines={1}>
          {title}
        </Text>
        <Text style={styles.meta} numberOfLines={1}>
          {meta}
        </Text>
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
    borderRadius: radius.lg,
    borderWidth: 1,
    borderColor: colors.border,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  iconBadge: {
    width: 32,
    height: 32,
    borderRadius: radius.sm,
    backgroundColor: colors.neutralTint,
    justifyContent: 'center',
    alignItems: 'center',
  },
  textBlock: {
    flex: 1,
  },
  title: {
    ...typography.h2,
    fontSize: 13,
    color: colors.textPrimary,
  },
  meta: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
});