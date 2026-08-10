import React, { useEffect, useMemo, useRef } from 'react';
import { Animated, Easing, StyleSheet, View } from 'react-native';
import { colors } from '../theme/colors';

type CelebrationBurstProps = {
  /** Chamado quando a animação termina -- o pai deve desmontar o burst aqui (ver ChapterDetailScreen/FlashcardReview) */
  onDone?: () => void;
  particleColors?: string[];
};

const DEFAULT_COLORS = [colors.success, colors.primary, colors.xp, colors.reviews];
const PARTICLE_COUNT = 10;

// Micro-recompensa visual pro momento de completar algo -- exatamente o
// tipo de "só mais um" que torna um hábito viciante em vez de só
// funcional. Nada de partícula-lib nova: um punhado de Views animando
// transform+opacity com o driver nativo já dá o efeito, e roda liso
// mesmo em aparelho fraco.
export default function CelebrationBurst({ onDone, particleColors = DEFAULT_COLORS }: CelebrationBurstProps) {
  const progress = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const animation = Animated.timing(progress, {
      toValue: 1,
      duration: 620,
      easing: Easing.out(Easing.cubic),
      useNativeDriver: true,
    });
    animation.start(({ finished }) => {
      if (finished) onDone?.();
    });
    return () => animation.stop();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const particles = useMemo(
    () =>
      Array.from({ length: PARTICLE_COUNT }, (_, i) => {
        const angle = (i / PARTICLE_COUNT) * Math.PI * 2 + (i % 2 === 0 ? 0.18 : -0.18);
        const distance = 42 + (i % 3) * 15;
        return {
          color: particleColors[i % particleColors.length],
          dx: Math.cos(angle) * distance,
          dy: Math.sin(angle) * distance,
          size: i % 3 === 0 ? 8 : 6,
        };
      }),
    [particleColors]
  );

  return (
    <View style={styles.wrap} pointerEvents="none">
      {particles.map((p, i) => {
        const translateX = progress.interpolate({ inputRange: [0, 1], outputRange: [0, p.dx] });
        const translateY = progress.interpolate({ inputRange: [0, 1], outputRange: [0, p.dy] });
        const opacity = progress.interpolate({ inputRange: [0, 0.65, 1], outputRange: [1, 1, 0] });
        const scale = progress.interpolate({ inputRange: [0, 0.3, 1], outputRange: [0.3, 1, 0.7] });
        return (
          <Animated.View
            key={i}
            style={[
              styles.particle,
              {
                width: p.size,
                height: p.size,
                borderRadius: p.size / 2,
                backgroundColor: p.color,
                opacity,
                transform: [{ translateX }, { translateY }, { scale }],
              },
            ]}
          />
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    position: 'absolute',
    top: '50%',
    left: '50%',
    width: 0,
    height: 0,
    alignItems: 'center',
    justifyContent: 'center',
  },
  particle: {
    position: 'absolute',
  },
});
