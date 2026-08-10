import React, { useEffect, useRef } from 'react';
import { View, Animated, Easing, StyleSheet, Platform } from 'react-native';
import { colors } from '../theme/colors';

// A believable pin without needing react-native-svg: a solid circle for
// the head, a smaller offset lighter circle for the glossy highlight, and
// a real platform shadow underneath. Used on 1-2 cards max — this is
// decoration reinforcing the corkboard idea, not something every card
// needs.
//
// The rock is deliberately tiny (±2.5deg) and slow (3.6s each way) — it
// should read as "this is a physical object, not a flat icon," not as a
// notification demanding attention. Uses core RN Animated, not
// Reanimated, so it doesn't add a dependency for one small effect.
export default function PushPin() {
  const rock = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(rock, { toValue: 1, duration: 3600, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(rock, { toValue: -1, duration: 3600, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(rock, { toValue: 0, duration: 3600, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [rock]);

  const rotate = rock.interpolate({ inputRange: [-1, 1], outputRange: ['-2.5deg', '2.5deg'] });

  return (
    <View style={styles.wrapper} pointerEvents="none">
      <Animated.View style={[styles.shadowCatcher, { transform: [{ rotate }] }]}>
        <View style={styles.head}>
          <View style={styles.highlight} />
        </View>
      </Animated.View>
    </View>
  );
}

const SIZE = 20;

const styles = StyleSheet.create({
  wrapper: {
    position: 'absolute',
    top: -10,
    alignSelf: 'center',
    zIndex: 2,
  },
  shadowCatcher: {
    ...Platform.select({
      ios: {
        shadowColor: '#000',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 0.25,
        shadowRadius: 3,
      },
      android: { elevation: 4 },
    }),
  },
  head: {
    width: SIZE,
    height: SIZE,
    borderRadius: SIZE / 2,
    backgroundColor: colors.streak,
    alignItems: 'center',
    justifyContent: 'center',
  },
  highlight: {
    width: SIZE * 0.35,
    height: SIZE * 0.35,
    borderRadius: (SIZE * 0.35) / 2,
    backgroundColor: 'rgba(255,255,255,0.55)',
    marginBottom: SIZE * 0.25,
    marginRight: SIZE * 0.2,
  },
});