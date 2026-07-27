import React from 'react';
import { View, Text, Image, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

type HomeHeaderProps = {
  name: string;
  /** Emoji avatar (animal/fruit) — the zero-asset option */
  avatarEmoji?: string;
  /** Or a real photo (e.g. synced from the person's email account) */
  avatarUri?: string;
  streakDays: number;
  level: number;
  hasUnreadNotification?: boolean;
  onPressNotifications?: () => void;
};

// Greeting stacks to 2 lines on purpose ("Bom dia," / "Lucas") — that's
// what leaves enough width for the streak + level pills to sit on the
// same row without wrapping on a narrow phone.
export default function HomeHeader({
  name,
  avatarEmoji,
  avatarUri,
  streakDays,
  level,
  hasUnreadNotification,
  onPressNotifications,
}: HomeHeaderProps) {
  return (
    <View style={styles.row}>
      <View style={styles.identity}>
        {avatarUri ? (
          <Image source={{ uri: avatarUri }} style={styles.avatar} />
        ) : (
          <View style={styles.avatarEmojiCircle}>
            <Text style={styles.avatarEmoji}>{avatarEmoji ?? '🦊'}</Text>
          </View>
        )}
        <View>
          <Text style={styles.greetingLine}>Bom dia,</Text>
          <Text style={styles.greetingName}>{name} 👋</Text>
        </View>
      </View>

      <View style={styles.stats}>
        <View style={[styles.pill, { backgroundColor: colors.streakTint }]}>
          <Ionicons name="flame" size={14} color={colors.streak} />
          <Text style={[styles.pillValue, { color: colors.streakText }]}>{streakDays}</Text>
        </View>
        <View style={[styles.pill, { backgroundColor: colors.xpTint }]}>
          <Ionicons name="ribbon" size={14} color={colors.xp} />
          <Text style={styles.pillLabel}>Nv.</Text>
          <Text style={[styles.pillValue, { color: colors.xp }]}>{level}</Text>
        </View>
        <TouchableOpacity
          style={styles.bellButton}
          onPress={onPressNotifications}
          hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}
          accessibilityRole="button"
          accessibilityLabel="Notificações"
        >
          <Ionicons name="notifications-outline" size={20} color={colors.textOnWoodMuted} />
          {hasUnreadNotification && <View style={styles.unreadDot} />}
        </TouchableOpacity>
      </View>
    </View>
  );
}

// Visual footprint stays compact (this sits beside the greeting), but the
// touchable area still meets the 44px minimum via hitSlop below.
const touchTargetSmall = 32;

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  identity: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  avatar: {
    width: 48,
    height: 48,
    borderRadius: 24,
  },
  avatarEmojiCircle: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarEmoji: {
    fontSize: 22,
  },
  greetingLine: {
    ...typography.caption,
    fontFamily: fonts.bodyMedium,
    color: colors.textOnWoodMuted,
  },
  greetingName: {
    ...typography.greeting,
    color: colors.textPrimary,
  },
  stats: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
  },
  pill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: 32,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
  },
  pillLabel: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textOnWoodMuted,
  },
  pillValue: {
    fontFamily: fonts.display,
    fontSize: 14,
  },
  bellButton: {
    width: touchTargetSmall,
    height: touchTargetSmall,
    alignItems: 'center',
    justifyContent: 'center',
  },
  unreadDot: {
    position: 'absolute',
    top: 6,
    right: 6,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: colors.streak,
    borderWidth: 1,
    borderColor: colors.background,
  },
});
