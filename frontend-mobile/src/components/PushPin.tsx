import React from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { colors } from '../theme/colors';

// A believable pin without needing react-native-svg: a solid circle for
// the head, a smaller offset lighter circle for the glossy highlight, and
// a real platform shadow underneath. Used on 1-2 cards max — this is
// decoration reinforcing the corkboard idea, not something every card
// needs.
export default function PushPin() {
  return (
    <View style={styles.wrapper} pointerEvents="none">
      <View style={styles.shadowCatcher}>
        <View style={styles.head}>
          <View style={styles.highlight} />
        </View>
      </View>
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
