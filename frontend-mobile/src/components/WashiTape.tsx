import React from 'react';
import { View, StyleSheet } from 'react-native';

type WashiTapeProps = {
  color: string;
  rotation?: number;
  style?: object;
};

// A simple rotated semi-transparent strip. Cheap, no dependency, reads
// as tape at a glance because of the slight rotation + torn-paper
// translucency, not because it's geometrically accurate tape.
export default function WashiTape({ color, rotation = -8, style }: WashiTapeProps) {
  return (
    <View
      style={[
        styles.tape,
        { backgroundColor: color, transform: [{ rotate: `${rotation}deg` }] },
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
    opacity: 0.85,
    borderRadius: 2,
  },
});
