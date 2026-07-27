import React from 'react';
import { View, StyleSheet } from 'react-native';
import { colors } from '../theme/colors';

type NotebookBackgroundProps = {
  children: React.ReactNode;
};

const LINE_SPACING = 32;
const LINE_COUNT = 60; // covers well past any realistic screen height
const MARGIN_X = 44;

export default function NotebookBackground({ children }: NotebookBackgroundProps) {
  return (
    <View style={styles.container}>
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        {Array.from({ length: LINE_COUNT }).map((_, i) => (
          <View key={i} style={[styles.ruleLine, { top: (i + 1) * LINE_SPACING }]} />
        ))}
        <View style={styles.marginLine} />
        {Array.from({ length: 16 }).map((_, i) => (
          <View key={i} style={[styles.hole, { top: 48 + i * 64 }]}>
            <View style={styles.holeInner} />
          </View>
        ))}
      </View>
      <View style={styles.content}>{children}</View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.notebookPaper,
  },
  content: {
    flex: 1,
    paddingLeft: MARGIN_X - 8,
  },
  ruleLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: colors.notebookRuleLine,
  },
  marginLine: {
    position: 'absolute',
    top: 0,
    bottom: 0,
    left: MARGIN_X,
    width: 1.5,
    backgroundColor: colors.notebookMarginLine,
    opacity: 0.5,
  },
  hole: {
    position: 'absolute',
    left: 14,
    width: 16,
    height: 16,
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  holeInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: 'rgba(0,0,0,0.10)',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.3,
    shadowRadius: 1,
  },
});
