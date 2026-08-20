import React, { useEffect, useRef, useState } from 'react';
import { Animated, Easing, Modal, Pressable, Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import CelebrationBurst from './CelebrationBurst'
import { DueReview, ReviewDifficulty } from '../services/knowledgeService';

type FlashcardReviewProps = {
  cards: DueReview[];
  onAnswer: (nodeId: number, difficulty: ReviewDifficulty) => Promise<void>;
  onClose: () => void;
};

// O back guarda só o nome do tópico pra revisão espaçada (não uma
// pergunta com resposta escondida pra revelar) — o mecanismo real é
// "veja o conceito, julgue com sinceridade se lembrou dele", então não
// tem passo de "toque pra revelar" aqui como uma flashcard clássica
// teria. RATING_BUTTONS cobre os 3 que aparecem na referência; "Não
// lembrei" fica como um link discreto abaixo — o back tem 4 níveis
// (again/hard/good/easy), e sem essa 4ª opção o algoritmo de repetição
// nunca reseta o intervalo de quem esqueceu de verdade.
const RATING_BUTTONS: { key: ReviewDifficulty; label: string; color: string }[] = [
  { key: 'easy', label: 'Fácil', color: colors.ratingEasy },
  { key: 'good', label: 'Médio', color: colors.ratingMedium },
  { key: 'hard', label: 'Difícil', color: colors.ratingHard },
];

const STACK_COLORS = [colors.postIt.blue, colors.postIt.pink];

export default function FlashcardReview({ cards: initialCards, onAnswer, onClose }: FlashcardReviewProps) {
  // Snapshot único, tirado só na abertura -- onAnswer dispara uma
  // invalidação da query lá em cima (pra o contador "X rev." atualizar),
  // e essa query encolhendo enquanto isso ainda está aberto bagunçaria
  // o índice (o card que "devia" vir a seguir muda de posição embaixo
  // da gente). A sessão de revisão trabalha numa lista fixa; a lista ao
  // vivo só importa de novo na próxima vez que a tela abrir.
  const [cards] = useState(initialCards);
  const [index, setIndex] = useState(0);
  const [submitting, setSubmitting] = useState(false);
  // "Mesa limpa" -- estado final antes de fechar, só quando a última
  // carta da sessão é respondida (ver handleRate). Reforça a mesma
  // sensação de "arrumei minha mesa de estudos" que o documento de
  // visão pede pras revisões.
  const [cleared, setCleared] = useState(false);

  // Duas animações independentes: `exitAnim` tira o card ATUAL de cena
  // quando respondido (0 = parado, 1 = saindo); `enterAnim` traz o
  // PRÓXIMO card pra cena assim que `index` muda (0 = acabou de chegar,
  // 1 = assentado). Compostas com Animated.add/multiply -- não precisa
  // do Reanimated pra isso.
  const exitAnim = useRef(new Animated.Value(0)).current;
  const enterAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    enterAnim.setValue(0);
    Animated.timing(enterAnim, { toValue: 1, duration: 260, easing: Easing.out(Easing.cubic), useNativeDriver: true }).start();
  }, [index, enterAnim]);

  useEffect(() => {
    if (!cleared) return;
    const timeout = setTimeout(onClose, 1500);
    return () => clearTimeout(timeout);
  }, [cleared, onClose]);

  const card = cards[index];
  const isLast = index === cards.length - 1;
  const remainingBehind = Math.min(Math.max(cards.length - index - 1, 0), 2);

  async function handleRate(difficulty: ReviewDifficulty) {
    if (!card || submitting) return;
    setSubmitting(true);
    // Anima a saída assim que a pessoa toca -- não espera a rede pra
    // sentir que a resposta "foi registrada". Se a chamada falhar, a
    // animação volta pro lugar (catch abaixo) e o card fica pronto pra
    // tentar de novo.
    Animated.timing(exitAnim, { toValue: 1, duration: 200, easing: Easing.in(Easing.cubic), useNativeDriver: true }).start();
    try {
      await onAnswer(card.node_id, difficulty);
      if (isLast) {
        setCleared(true);
      } else {
        setIndex((i) => i + 1);
        exitAnim.setValue(0);
      }
    } catch {
      exitAnim.setValue(0);
    } finally {
      setSubmitting(false);
    }
  }

  if (!card && !cleared) return null;

  const translateY = Animated.add(
    enterAnim.interpolate({ inputRange: [0, 1], outputRange: [18, 0] }),
    exitAnim.interpolate({ inputRange: [0, 1], outputRange: [0, -46] })
  );
  const opacity = Animated.multiply(
    enterAnim.interpolate({ inputRange: [0, 1], outputRange: [0, 1] }),
    exitAnim.interpolate({ inputRange: [0, 1], outputRange: [1, 0] })
  );

  return (
    <Modal visible transparent animationType="fade" onRequestClose={onClose}>
      <Pressable style={styles.overlay} onPress={onClose}>
        <Pressable style={styles.pinWrap} onPress={(e) => e.stopPropagation()}>
          <View style={styles.pinHead} />

          <View style={styles.stackWrap}>
            {Array.from({ length: remainingBehind }).map((_, i) => (
              <View
                key={i}
                style={[
                  styles.stackLayer,
                  {
                    backgroundColor: STACK_COLORS[i % STACK_COLORS.length],
                    transform: [{ rotate: `${(i + 1) * 3.5}deg` }, { translateY: (i + 1) * 4 }],
                  },
                ]}
              />
            ))}

            {cleared ? (
              <View style={styles.card}>
                <CelebrationBurst />
                <View style={styles.clearedIconCircle}>
                  <Ionicons name="sparkles" size={22} color={colors.success} />
                </View>
                <Text style={styles.clearedTitle}>Mesa limpa! ✨</Text>
                <Text style={styles.clearedSubtitle}>Todas as revisões de hoje, feitas.</Text>
              </View>
            ) : (
              <Animated.View style={[styles.card, { opacity, transform: [{ translateY }] }]}>
                <View style={styles.headerRow}>
                  <Ionicons name="repeat" size={13} color={colors.textSecondaryOnPastel} />
                  <Text style={styles.headerLabel}>REVISÃO</Text>
                </View>
                <Text style={styles.progress}>
                  {index + 1} de {cards.length}
                </Text>

                <Text style={styles.topic}>{card.topic_name}</Text>
                {card.goal_title && <Text style={styles.goalTitle}>{card.goal_title}</Text>}

                <Text style={styles.prompt}>Como foi esta revisão?</Text>

                <View style={styles.ratingRow}>
                  {RATING_BUTTONS.map((btn) => (
                    <TouchableOpacity
                      key={btn.key}
                      style={styles.ratingButton}
                      onPress={() => handleRate(btn.key)}
                      disabled={submitting}
                      accessibilityRole="button"
                      accessibilityLabel={btn.label}
                    >
                      <View style={[styles.ratingDot, { backgroundColor: btn.color }]} />
                      <Text style={styles.ratingText}>{btn.label}</Text>
                    </TouchableOpacity>
                  ))}
                </View>

                <TouchableOpacity onPress={() => handleRate('again')} disabled={submitting} style={styles.forgotLink}>
                  <Text style={styles.forgotText}>Não lembrei de nada</Text>
                </TouchableOpacity>

                <View style={styles.dotsRow}>
                  {cards.map((_, i) => (
                    <View key={i} style={[styles.progressDot, i === index && styles.progressDotActive]} />
                  ))}
                </View>
              </Animated.View>
            )}
          </View>
        </Pressable>
        <Text style={styles.closeHint}>toque fora para fechar</Text>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    padding: spacing.lg,
  },
  pinWrap: {
    alignItems: 'center',
    width: '100%',
    maxWidth: 340,
  },
  pinHead: {
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: colors.streak,
    borderWidth: 1.5,
    borderColor: 'rgba(0,0,0,0.15)',
    marginBottom: -7,
    zIndex: 1,
  },
  stackWrap: {
    width: '100%',
  },
  stackLayer: {
    position: 'absolute',
    top: 0,
    left: spacing.md,
    right: spacing.md,
    height: 140,
    borderRadius: radius.sm,
    opacity: 0.7,
  },
  card: {
    width: '100%',
    backgroundColor: colors.postIt.yellow,
    borderRadius: radius.sm,
    padding: spacing.lg,
    transform: [{ rotate: '-0.6deg' }],
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.28,
    shadowRadius: 10,
    elevation: 8,
  },
  clearedIconCircle: {
    alignSelf: 'center',
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: colors.successTint,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  clearedTitle: {
    ...typography.missionName,
    fontSize: 20,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  clearedSubtitle: {
    ...typography.caption,
    fontSize: 13,
    color: colors.textSecondaryOnPastel,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  headerLabel: {
    ...typography.eyebrow,
    color: colors.textSecondaryOnPastel,
  },
  progress: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondaryOnPastel,
    marginTop: 2,
  },
  topic: {
    ...typography.missionName,
    fontSize: 22,
    color: colors.textPrimary,
    marginTop: spacing.md,
  },
  goalTitle: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondaryOnPastel,
    marginTop: 2,
  },
  prompt: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: 'rgba(31,22,12,0.15)',
    paddingTop: spacing.md,
  },
  ratingRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  ratingButton: {
    flex: 1,
    minHeight: touchTarget + 12,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    borderRadius: radius.md,
    backgroundColor: 'rgba(255,255,255,0.55)',
  },
  ratingDot: {
    width: 22,
    height: 22,
    borderRadius: 11,
  },
  ratingText: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
    color: colors.textPrimary,
  },
  forgotLink: {
    alignSelf: 'center',
    marginTop: spacing.md,
  },
  forgotText: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondaryOnPastel,
    textDecorationLine: 'underline',
  },
  dotsRow: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 6,
    marginTop: spacing.md,
  },
  progressDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: 'rgba(31,22,12,0.2)',
  },
  progressDotActive: {
    backgroundColor: colors.textPrimary,
  },
  closeHint: {
    ...typography.caption,
    fontSize: 11,
    color: 'rgba(255,255,255,0.7)',
    marginTop: spacing.md,
  },
});
