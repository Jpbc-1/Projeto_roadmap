import React from 'react';
import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors } from '../theme/colors';

type WoodBackgroundProps = {
  children: React.ReactNode;
};

// Fixed, deterministic speckle positions (not random-per-render — a
// corkboard's texture doesn't reshuffle every time you look at it).
// Percent-based so it scales with whatever screen it renders on.
const SPECKLES = [
  { x: 63.4, y: 4.4, size: 2.8, o: 0.09 }, { x: 72.7, y: 67.0, size: 4.7, o: 0.07 },
  { x: 42.5, y: 4.9, size: 2.7, o: 0.11 }, { x: 4.5, y: 21.1, size: 3.9, o: 0.12 },
  { x: 23.2, y: 58.6, size: 4.4, o: 0.06 }, { x: 79.4, y: 69.0, size: 3.0, o: 0.08 },
  { x: 93.9, y: 34.3, size: 2.3, o: 0.07 }, { x: 83.4, y: 60.0, size: 4.4, o: 0.13 },
  { x: 53.5, y: 95.4, size: 3.1, o: 0.11 }, { x: 81.6, y: 61.4, size: 4.6, o: 0.12 },
  { x: 69.6, y: 6.4, size: 2.7, o: 0.09 }, { x: 9.7, y: 24.3, size: 2.3, o: 0.09 },
  { x: 63.0, y: 37.0, size: 3.1, o: 0.08 }, { x: 27.6, y: 91.9, size: 3.9, o: 0.12 },
  { x: 18.4, y: 72.0, size: 2.5, o: 0.1 }, { x: 97.0, y: 63.4, size: 3.7, o: 0.13 },
  { x: 82.9, y: 76.5, size: 2.7, o: 0.06 }, { x: 32.3, y: 27.7, size: 2.6, o: 0.15 },
  { x: 86.1, y: 32.2, size: 4.0, o: 0.1 }, { x: 89.8, y: 46.0, size: 2.8, o: 0.08 },
  { x: 55.9, y: 27.2, size: 3.8, o: 0.14 }, { x: 40.3, y: 23.1, size: 5.0, o: 0.11 },
  { x: 10.7, y: 6.5, size: 2.3, o: 0.12 }, { x: 78.0, y: 42.5, size: 2.2, o: 0.1 },
  { x: 97.6, y: 52.8, size: 4.9, o: 0.14 }, { x: 3.1, y: 71.2, size: 4.0, o: 0.11 },
  { x: 27.6, y: 63.5, size: 2.3, o: 0.1 }, { x: 45.6, y: 93.6, size: 4.6, o: 0.08 },
  { x: 50.1, y: 19.2, size: 4.7, o: 0.14 }, { x: 30.7, y: 63.3, size: 3.8, o: 0.07 },
  { x: 75.2, y: 53.8, size: 4.3, o: 0.11 }, { x: 2.1, y: 33.1, size: 2.1, o: 0.15 },
  { x: 86.4, y: 81.8, size: 2.9, o: 0.06 }, { x: 86.3, y: 92.9, size: 2.3, o: 0.1 },
  { x: 8.6, y: 75.0, size: 4.3, o: 0.07 },
];

// Bigger, softer marks — actual stains/watermarks/knots, not texture
// noise. Each rendered as 3 nested circles fading outward (no blur
// filter needed). A mix of darker (water stain) and lighter
// (sun-bleached patch) so it doesn't read as one repeated motif.
const STAINS = [
  { x: 32.5, y: 18.1, r: 78, dark: false },
  { x: 50.5, y: 36.8, r: 48, dark: true },
  { x: 8.2, y: 42.7, r: 48, dark: false },
  { x: 41.1, y: 76.9, r: 51, dark: false },
  { x: 58.3, y: 87.5, r: 74, dark: false },
  { x: 88.0, y: 9.1, r: 88, dark: false },
];

function Stain({ x, y, r, dark }: { x: number; y: number; r: number; dark: boolean }) {
  const rgb = dark ? '0,0,0' : '255,255,255';
  const [o1, o2, o3] = dark ? [0.025, 0.04, 0.055] : [0.02, 0.035, 0.05];
  const layers = [
    { scale: 1, o: o1 },
    { scale: 0.65, o: o2 },
    { scale: 0.35, o: o3 },
  ];
  return (
    <>
      {layers.map((layer, i) => {
        const size = r * 2 * layer.scale;
        return (
          <View
            key={i}
            style={{
              position: 'absolute',
              left: `${x}%`,
              top: `${y}%`,
              width: size,
              height: size,
              marginLeft: -size / 2,
              marginTop: -size / 2,
              borderRadius: size / 2,
              backgroundColor: `rgba(${rgb},${layer.o})`,
            }}
          />
        );
      })}
    </>
  );
}

export default function WoodBackground({ children }: WoodBackgroundProps) {
  return (
    <View style={styles.container}>
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <LinearGradient
          colors={['rgba(255,255,255,0.10)', 'rgba(0,0,0,0)', 'rgba(0,0,0,0.12)']}
          locations={[0, 0.5, 1]}
          start={{ x: 0.1, y: 0 }}
          end={{ x: 0.22, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
        <LinearGradient
          colors={['rgba(0,0,0,0)', 'rgba(0,0,0,0.1)', 'rgba(0,0,0,0)']}
          locations={[0, 0.5, 1]}
          start={{ x: 0.5, y: 0 }}
          end={{ x: 0.58, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
        <LinearGradient
          colors={['rgba(255,255,255,0.09)', 'rgba(0,0,0,0.06)']}
          start={{ x: 0.82, y: 0 }}
          end={{ x: 0.9, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
        <LinearGradient
          colors={['rgba(0,0,0,0.16)', 'rgba(0,0,0,0)', 'rgba(0,0,0,0)', 'rgba(0,0,0,0.18)']}
          locations={[0, 0.15, 0.85, 1]}
          start={{ x: 0, y: 0 }}
          end={{ x: 0, y: 1 }}
          style={StyleSheet.absoluteFill}
        />
        {STAINS.map((s, i) => (
          <Stain key={i} {...s} />
        ))}
        {SPECKLES.map((s, i) => (
          <View
            key={i}
            style={{
              position: 'absolute',
              left: `${s.x}%`,
              top: `${s.y}%`,
              width: s.size,
              height: s.size,
              borderRadius: s.size / 2,
              backgroundColor: `rgba(0,0,0,${s.o})`,
            }}
          />
        ))}
      </View>
      {children}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
});