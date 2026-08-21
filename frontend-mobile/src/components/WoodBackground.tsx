import React from 'react';
import { View, StyleSheet } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { colors } from '../theme/colors';

type WoodBackgroundProps = {
  children: React.ReactNode;
};

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