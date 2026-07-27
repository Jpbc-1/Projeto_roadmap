import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';

type ReviewStackProps = {
  pendingCount: number;
  onStart: () => void;
};

const FAN = [
  { bg: colors.postIt.blue, rotate: '-6deg', offset: 6 },
  { bg: colors.postIt.pink, rotate: '4deg', offset: 3 },
  { bg: colors.reviewsTint, rotate: '-1deg', offset: 0 },
];

export default function ReviewStack({ pendingCount, onStart }: ReviewStackProps) {
  return (
    <TouchableOpacity
      style={styles.wrap}
      onPress={onStart}
      activeOpacity={0.85}
      accessibilityRole="button"
      accessibilityLabel={`Começar revisão, ${pendingCount} cartões`}
    >
      <View style={styles.stack}>
        {FAN.map((card, i) => (
          <View
            key={i}
            style={[
              styles.card,
              {
                backgroundColor: card.bg,
                transform: [{ rotate: card.rotate }, { translateX: card.offset }],
              },
            ]}
          />
        ))}
        <View style={styles.topCard}>
          <Ionicons name="repeat" size={20} color={colors.reviews} />
        </View>
      </View>

      <View style={styles.textBlock}>
        <Text style={styles.title}>Revisão</Text>
        <Text style={styles.subtitle}>{pendingCount} cartões esperando</Text>
      </View>

      <View style={styles.startButton}>
        <Text style={styles.startText}>Revisar</Text>
        <Ionicons name="arrow-forward" size={14} color={colors.textOnPrimary} />
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  wrap: {
    minHeight: touchTarget,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    marginTop: spacing.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    elevation: 3,
  },
  stack: {
    width: 48,
    height: 48,
    marginRight: spacing.md,
    alignItems: 'center',
    justifyContent: 'center',
  },
  card: {
    position: 'absolute',
    width: 36,
    height: 36,
    borderRadius: radius.sm,
  },
  topCard: {
    width: 36,
    height: 36,
    borderRadius: radius.sm,
    backgroundColor: colors.reviewsTint,
    borderWidth: 1,
    borderColor: colors.reviews,
    alignItems: 'center',
    justifyContent: 'center',
  },
  textBlock: {
    flex: 1,
  },
  title: {
    ...typography.cardTitle,
    fontSize: 15,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.sm,
  },
  startButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.primary,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    minHeight: touchTarget,
  },
  startText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 13,
    color: colors.textOnPrimary,
  },
});
