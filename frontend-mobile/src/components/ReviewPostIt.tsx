import React from 'react';
import { Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts } from '../theme/colors';

type ReviewPostItProps = {
  count: number;
  onPress: () => void;
};

// Camadas extra atrás do post-it de cima -- puramente decorativas, sem
// conteúdo, só pra sugerir "isso é uma pilha". Documento de visão:
// "quanto menos revisões restarem, menor fica a pilha de post-its";
// como esse trigger só mostra a CONTAGEM total (o encolher página a
// página acontece dentro do FlashcardReview), o melhor que dá pra fazer
// aqui é a mesma ideia em escala menor -- 1 revisão = só o post-it de
// cima, 2 = mais uma camada atrás, 3+ = pilha "cheia" (não cresce mais
// que isso pra não virar bagunça visual).
const STACK_COLORS = [colors.postIt.blue, colors.postIt.pink];

export default function ReviewPostIt({ count, onPress }: ReviewPostItProps) {
  const extraLayers = Math.min(Math.max(count - 1, 0), 2);

  return (
    <TouchableOpacity
      style={styles.wrap}
      onPress={onPress}
      activeOpacity={0.85}
      accessibilityRole="button"
      accessibilityLabel={`Abrir revisões pendentes, ${count} no total`}
    >
      {Array.from({ length: extraLayers }).map((_, i) => (
        <View
          key={i}
          style={[
            styles.layer,
            {
              backgroundColor: STACK_COLORS[i % STACK_COLORS.length],
              transform: [{ rotate: `${(i + 1) * -4}deg` }, { translateY: (i + 1) * -2 }],
            },
          ]}
        />
      ))}

      <View style={styles.topLayer}>
        <View style={styles.pinHead} />
        <Ionicons name="repeat" size={14} color={colors.textPrimary} style={styles.icon} />
        <Text style={styles.count}>{count}</Text>
        <Text style={styles.label}>rev.</Text>
      </View>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  wrap: {
    alignItems: 'center',
    justifyContent: 'center',
    minWidth: 64,
    minHeight: 64,
  },
  layer: {
    position: 'absolute',
    top: 6,
    width: 64,
    height: 58,
    borderRadius: radius.sm,
    opacity: 0.75,
  },
  topLayer: {
    alignItems: 'center',
    backgroundColor: colors.postIt.yellow,
    borderRadius: radius.sm,
    paddingTop: 14,
    paddingBottom: spacing.sm,
    paddingHorizontal: spacing.md,
    minWidth: 64,
    transform: [{ rotate: '3deg' }],
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.22,
    shadowRadius: 5,
    elevation: 5,
  },
  pinHead: {
    position: 'absolute',
    top: -7,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: colors.streak,
    borderWidth: 1.5,
    borderColor: 'rgba(0,0,0,0.15)',
  },
  icon: {
    marginBottom: 2,
  },
  count: {
    fontFamily: fonts.display,
    fontSize: 18,
    color: colors.textPrimary,
    lineHeight: 20,
  },
  label: {
    ...typography.caption,
    fontSize: 10,
    color: colors.textSecondaryOnPastel,
  },
});
