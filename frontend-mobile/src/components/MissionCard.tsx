import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';
import PushPin from './PushPin';
import WashiTape from './WashiTape';

type MissionCardProps = {
  /** e.g. "Cap. 3 · Python para Dados" — no "3/8": the progress bar below already covers that */
  context: string;
  /** 0 to 1 — chapter completion */
  chapterProgress: number;
  /** The mission's actual name — the single most important text on this screen */
  missionName: string;
  /** One short sentence of context. Not a motivational line — what the mission is */
  description: string;
  xp: number;
  minutes: number;
  onFinish: () => void;
};

// The post-it, tilted slightly like it was actually stuck on by hand —
// not a perfectly aligned card like everything else. Yellow because
// that's what a post-it is, and because it's the one card on the board
// that should visually announce itself as "the important one" before
// you've even read a word of it.
export default function MissionCard({
  context,
  chapterProgress,
  missionName,
  description,
  xp,
  minutes,
  onFinish,
}: MissionCardProps) {
  const pct = Math.round(Math.min(Math.max(chapterProgress, 0), 1) * 100);

  return (
    <View style={styles.wrapper}>
      <PushPin />
      <WashiTape color="rgba(214,58,8,0.55)" rotation={-14} style={{ top: -8, right: 24 }} />

      <View style={styles.card}>
        <View style={styles.progressRow}>
          <Text style={styles.eyebrow}>{context}</Text>
          <Text style={styles.progressNumber}>{pct}%</Text>
        </View>
        <View style={styles.progressTrack}>
          <View style={[styles.progressFill, { width: `${pct}%` }]} />
        </View>

        <View style={styles.tagRow}>
          <View style={[styles.tag, { backgroundColor: colors.xpTint }]}>
            <Text style={[styles.tagText, { color: colors.xp }]}>+{xp} XP</Text>
          </View>
          <View style={[styles.tag, { backgroundColor: 'rgba(31,22,12,0.08)' }]}>
            <Ionicons name="time-outline" size={12} color={colors.textOnWoodMuted} />
            <Text style={[styles.tagText, { color: colors.textOnWoodMuted }]}>{minutes} min</Text>
          </View>
        </View>

        <Text style={styles.missionName}>{missionName}</Text>
        <Text style={styles.description}>{description}</Text>

        <TouchableOpacity
          style={styles.button}
          onPress={onFinish}
          activeOpacity={0.85}
          accessibilityRole="button"
          accessibilityLabel="Começar missão"
        >
          <Ionicons name="rocket" size={18} color={colors.textOnPrimary} />
          <Text style={styles.buttonText}>Começar Missão</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginTop: spacing.lg + spacing.sm,
    transform: [{ rotate: '-1.5deg' }],
  },
  card: {
    backgroundColor: colors.postIt.yellow,
    borderRadius: radius.sm,
    padding: spacing.md,
    // A flat, hard-edged shadow (not a soft blurred one) reads more like
    // a physical sheet of paper lifted slightly off the board.
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.22,
    shadowRadius: 6,
    elevation: 6,
  },
  progressRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: spacing.sm,
  },
  eyebrow: {
    ...typography.eyebrow,
    color: colors.textSecondaryOnPastel,
    flexShrink: 1,
  },
  progressNumber: {
    fontFamily: fonts.display,
    fontSize: 16,
    color: colors.success,
  },
  progressTrack: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: 'rgba(31,22,12,0.12)',
    marginBottom: spacing.md,
  },
  progressFill: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.success,
  },
  tagRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  tag: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
  },
  tagText: {
    ...typography.caption,
    fontSize: 12,
  },
  missionName: {
    ...typography.missionName,
    color: colors.textPrimary,
    marginBottom: spacing.sm,
  },
  description: {
    ...typography.body,
    color: colors.textSecondaryOnPastel,
    marginBottom: spacing.md,
  },
  button: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
    backgroundColor: colors.primary,
    paddingVertical: spacing.md,
    borderRadius: radius.md,
    minHeight: 56,
  },
  buttonText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 16,
    color: colors.textOnPrimary,
  },
});