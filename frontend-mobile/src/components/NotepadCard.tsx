import React from 'react';
import { View, StyleSheet } from 'react-native';
import { colors, radius } from '../theme/colors';
import PushPin from './PushPin';

type NotepadCardProps = {
  children: React.ReactNode;
  /** How many pins hold it down — 3 for shorter cards reads calmer than
   * 4 pinned corners, matching the density in the reference shots. */
  pinCount?: 3 | 4;
};

const RING_COUNT = 15;
const LINE_SPACING = 30;
const LINE_COUNT = 26; // generous on purpose; excess just gets clipped by the card's rounded corners

// PushPin centers itself (alignSelf: 'center') inside whatever wraps it
// — it doesn't take a position prop, and it's already used elsewhere
// (MissionCard on Home), so rather than changing its shared behavior,
// each pin here gets its own narrow absolutely-positioned slot to center
// within, spread across the top edge.
function pinLeftPositions(count: 3 | 4): number[] {
  return count === 3 ? [16, 50, 84] : [10, 37, 63, 90];
}

export default function NotepadCard({ children, pinCount = 4 }: NotepadCardProps) {
  return (
    <View style={styles.wrapper}>
      {pinLeftPositions(pinCount).map((left) => (
        <View key={left} style={[styles.pinSlot, { left: `${left}%` }]}>
          <PushPin />
        </View>
      ))}

      <View style={styles.cardShadow}>
        <View style={styles.card}>
          <View style={styles.spiralStrip}>
            {Array.from({ length: RING_COUNT }).map((_, i) => (
              <View key={i} style={styles.ring} />
            ))}
          </View>

          <View style={styles.paper}>
            <View style={StyleSheet.absoluteFill} pointerEvents="none">
              {Array.from({ length: LINE_COUNT }).map((_, i) => (
                <View key={i} style={[styles.ruleLine, { top: (i + 1) * LINE_SPACING }]} />
              ))}
            </View>
            <View style={styles.content}>{children}</View>
          </View>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    position: 'relative',
    marginTop: 26, // room for the pins to sit above the card, on the wood
  },
  pinSlot: {
    position: 'absolute',
    top: 0,
    width: 24,
    marginLeft: -12,
    zIndex: 2,
  },
  cardShadow: {
    borderRadius: radius.lg,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.28,
    shadowRadius: 16,
    elevation: 10,
  },
  card: {
    backgroundColor: colors.notebookPaper,
    borderRadius: radius.lg,
    overflow: 'hidden',
  },
  spiralStrip: {
    flexDirection: 'row',
    justifyContent: 'space-evenly',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingVertical: 10,
  },
  ring: {
    width: 9,
    height: 9,
    borderRadius: 4.5,
    backgroundColor: 'rgba(0,0,0,0.22)',
  },
  paper: {
    position: 'relative',
  },
  ruleLine: {
    position: 'absolute',
    left: 0,
    right: 0,
    height: 1,
    backgroundColor: colors.notebookRuleLine,
  },
  content: {
    padding: 24,
  },
});
