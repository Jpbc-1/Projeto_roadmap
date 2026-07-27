import React, { useState } from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';

export type Flashcard = {
  question: string;
  answer: string;
};

type FlashcardReviewProps = {
  cards: Flashcard[];
  onClose: () => void;
  onComplete: () => void;
};

type Rating = 'again' | 'hard' | 'medium' | 'easy';

const RATING_BUTTONS: { key: Rating; label: string; color: string }[] = [
  { key: 'again', label: 'Again', color: colors.ratingAgain },
  { key: 'hard', label: 'Difícil', color: colors.ratingHard },
  { key: 'medium', label: 'Médio', color: colors.ratingMedium },
  { key: 'easy', label: 'Fácil', color: colors.ratingEasy },
];

// A rating doesn't just advance the deck in a real spaced-repetition
// system — it changes when the card comes back (Again = minutes, Easy =
// weeks). No scheduling engine here, but the interaction is the real
// one: you have to look at the answer and honestly judge yourself
// before the deck moves on, which is the actual mechanic that makes
// spaced repetition work.
export default function FlashcardReview({ cards, onClose, onComplete }: FlashcardReviewProps) {
  const [index, setIndex] = useState(0);
  const [revealed, setRevealed] = useState(false);

  const card = cards[index];
  const isLast = index === cards.length - 1;

  function handleRate() {
    if (isLast) {
      onComplete();
      return;
    }
    setIndex((i) => i + 1);
    setRevealed(false);
  }

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity
          onPress={onClose}
          hitSlop={{ top: 12, bottom: 12, left: 12, right: 12 }}
          accessibilityRole="button"
          accessibilityLabel="Fechar revisão"
        >
          <Ionicons name="close" size={22} color={colors.textPrimary} />
        </TouchableOpacity>
        <Text style={styles.progress}>
          {index + 1} de {cards.length}
        </Text>
        <View style={{ width: 22 }} />
      </View>

      <TouchableOpacity
        style={styles.card}
        onPress={() => setRevealed(true)}
        activeOpacity={revealed ? 1 : 0.9}
        disabled={revealed}
        accessibilityRole="button"
        accessibilityLabel={revealed ? card.answer : `${card.question}. Toque para ver a resposta`}
      >
        <Text style={styles.questionLabel}>PERGUNTA</Text>
        <Text style={styles.question}>{card.question}</Text>

        {revealed ? (
          <>
            <View style={styles.divider} />
            <Text style={styles.answerLabel}>RESPOSTA</Text>
            <Text style={styles.answer}>{card.answer}</Text>
          </>
        ) : (
          <View style={styles.tapHint}>
            <Ionicons name="hand-left-outline" size={14} color={colors.textSecondaryOnPastel} />
            <Text style={styles.tapHintText}>Toque pra ver a resposta</Text>
          </View>
        )}
      </TouchableOpacity>

      {revealed && (
        <View style={styles.ratingRow}>
          {RATING_BUTTONS.map((btn) => (
            <TouchableOpacity
              key={btn.key}
              style={[styles.ratingButton, { backgroundColor: btn.color }]}
              onPress={handleRate}
              accessibilityRole="button"
              accessibilityLabel={btn.label}
            >
              <Text style={styles.ratingText}>{btn.label}</Text>
            </TouchableOpacity>
          ))}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    marginTop: spacing.lg,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.md,
  },
  progress: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  card: {
    backgroundColor: colors.postIt.yellow,
    borderRadius: radius.sm,
    padding: spacing.lg,
    minHeight: 200,
    transform: [{ rotate: '-0.5deg' }],
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.2,
    shadowRadius: 6,
    elevation: 5,
  },
  questionLabel: {
    ...typography.eyebrow,
    color: colors.textSecondaryOnPastel,
    marginBottom: spacing.sm,
  },
  question: {
    ...typography.missionName,
    fontSize: 20,
    color: colors.textPrimary,
  },
  divider: {
    height: 1,
    backgroundColor: 'rgba(31,22,12,0.15)',
    marginVertical: spacing.md,
  },
  answerLabel: {
    ...typography.eyebrow,
    color: colors.textSecondaryOnPastel,
    marginBottom: spacing.sm,
  },
  answer: {
    ...typography.body,
    color: colors.textPrimary,
  },
  tapHint: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.lg,
  },
  tapHintText: {
    ...typography.caption,
    color: colors.textSecondaryOnPastel,
  },
  ratingRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  ratingButton: {
    flex: 1,
    minHeight: touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
  },
  ratingText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
    color: colors.iconOnDark,
  },
});
