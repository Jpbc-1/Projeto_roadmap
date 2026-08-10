import React, { useEffect, useRef } from 'react';
import { Animated, StyleSheet, Easing } from 'react-native';

type WashiTapeProps = {
  color: string;
  rotation?: number;
  style?: object;
};

// A simple rotated semi-transparent strip. Cheap, no dependency, reads
// as tape at a glance because of the slight rotation + torn-paper
// translucency, not because it's geometrically accurate tape. Tape
// doesn't rock like a pin would (it's flat and stuck down), so instead
// it gets the faintest opacity shimmer — like light catching it
// slightly differently — same "something's alive" idea, different
// physical logic. Slower and more understated than the pin's wobble.
export default function WashiTape({ color, rotation = -8, style }: WashiTapeProps) {
  const shimmer = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmer, { toValue: 1, duration: 4200, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
        Animated.timing(shimmer, { toValue: 0, duration: 4200, easing: Easing.inOut(Easing.quad), useNativeDriver: true }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [shimmer]);

  const opacity = shimmer.interpolate({ inputRange: [0, 1], outputRange: [0.78, 0.92] });

  return (
    <Animated.View
      style={[
        styles.tape,
        { backgroundColor: color, opacity, transform: [{ rotate: `${rotation}deg` }] },
        style,
      ]}
      pointerEvents="none"
    />
  );
}

const styles = StyleSheet.create({
  tape: {
    position: 'absolute',
    width: 48,
    height: 20,
    borderRadius: 2,
  },
});