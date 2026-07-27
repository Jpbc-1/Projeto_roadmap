import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Path, Circle } from 'react-native-svg';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography } from '../theme/colors';

export type SketchChapterStatus = 'completed' | 'current' | 'locked';

export type SketchChapter = {
  title: string;
  status: SketchChapterStatus;
};

type RoadmapSketchProps = {
  chapters: SketchChapter[]; // up to 5, positions are hand-placed along the path
};

// Pre-placed node positions along a hand-drawn-looking winding path — not
// computed geometry, because a real pencil sketch isn't computed geometry
// either. Supports up to 5 chapters; extras are ignored rather than
// crowding the drawing.
const SLOTS = [
  { x: 34, y: 148 },
  { x: 104, y: 76 },
  { x: 182, y: 132 },
  { x: 254, y: 58 },
  { x: 318, y: 108 },
];

const PATH_D =
  'M34,148 C60,110 84,84 104,76 C132,64 158,108 182,132 C210,160 232,86 254,58 C278,28 298,80 318,108';

const VIEW_W = 340;
const VIEW_H = 190;

export default function RoadmapSketch({ chapters }: RoadmapSketchProps) {
  const shown = chapters.slice(0, SLOTS.length);

  return (
    <View style={styles.wrap}>
      <Svg width="100%" height={VIEW_H} viewBox={`0 0 ${VIEW_W} ${VIEW_H}`}>
        {/* Doubled, slightly offset stroke = the "sketchy pencil" look —
            a single clean stroke reads as vector art, not a drawing. */}
        <Path d={PATH_D} stroke={colors.graphite} strokeWidth={1.6} fill="none" opacity={0.55} strokeLinecap="round" />
        <Path
          d={PATH_D}
          stroke={colors.graphite}
          strokeWidth={1.6}
          fill="none"
          opacity={0.55}
          strokeLinecap="round"
          transform="translate(1.5, 1)"
        />

        {shown.map((chapter, i) => {
          const pos = SLOTS[i];
          if (chapter.status === 'completed') {
            return (
              <React.Fragment key={i}>
                <Circle cx={pos.x} cy={pos.y} r={11} stroke={colors.graphite} strokeWidth={1.6} fill={colors.notebookPaper} />
                <Circle cx={pos.x} cy={pos.y} r={5.5} fill={colors.success} />
              </React.Fragment>
            );
          }
          if (chapter.status === 'current') {
            return (
              <React.Fragment key={i}>
                <Circle cx={pos.x} cy={pos.y} r={14} stroke={colors.graphite} strokeWidth={2} fill={colors.notebookPaper} />
                <Circle cx={pos.x} cy={pos.y} r={14} stroke={colors.graphite} strokeWidth={0.8} fill="none" opacity={0.4} transform={`translate(1.2, -1) scale(1.08)`} />
              </React.Fragment>
            );
          }
          return (
            <Circle
              key={i}
              cx={pos.x}
              cy={pos.y}
              r={9}
              stroke={colors.graphite}
              strokeWidth={1.2}
              fill="none"
              opacity={0.45}
              strokeDasharray="2,2"
            />
          );
        })}
      </Svg>

      {/* Labels positioned to roughly sit near each node — plain text,
          not part of the drawing, so it stays perfectly legible. */}
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        {shown.map((chapter, i) => {
          const pos = SLOTS[i];
          const isLocked = chapter.status === 'locked';
          return (
            <View
              key={i}
              style={[
                styles.labelWrap,
                {
                  left: `${(pos.x / VIEW_W) * 100}%`,
                  top: `${(pos.y / VIEW_H) * 100}%`,
                },
              ]}
            >
              {chapter.status === 'current' && (
                <View style={styles.currentBadge}>
                  <Ionicons name="pencil" size={10} color={colors.textOnPrimary} />
                </View>
              )}
              <Text style={[styles.label, isLocked && styles.labelLocked]} numberOfLines={2}>
                {chapter.title}
              </Text>
            </View>
          );
        })}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: {
    marginTop: spacing.sm,
  },
  labelWrap: {
    position: 'absolute',
    width: 96,
    // Half of the width above, centering the label under its node —
    // a computed geometric offset, not a spacing choice (see the same
    // pattern/comment on StreakProgress's marker).
    marginLeft: -48,
    marginTop: spacing.md,
    alignItems: 'center',
  },
  label: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textPrimary,
    textAlign: 'center',
  },
  labelLocked: {
    color: colors.textSecondary,
  },
  currentBadge: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
});
