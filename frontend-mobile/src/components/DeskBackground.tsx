import React from 'react';
import { View, StyleSheet } from 'react-native';
import WoodBackground from './WoodBackground';
import { CoffeeCupProp, PencilProp } from './DeskProps';

type DeskBackgroundProps = {
  children: React.ReactNode;
};

/** Same wood/cork surface as Home, plus a couple of small objects sitting
 * on the desk around the notepad — used behind login/register/onboarding
 * instead of plain WoodBackground so that stretch of the app reads as
 * "your notebook, open on your desk" rather than just "the Home tab's
 * texture reused". Kept to two props on purpose (see DeskProps.tsx) —
 * this is the margin around the notepad, not the whole scene. */
export default function DeskBackground({ children }: DeskBackgroundProps) {
  return (
    <WoodBackground>
      <View style={StyleSheet.absoluteFill} pointerEvents="none">
        <View style={styles.coffeeSlot}>
          <CoffeeCupProp size={58} />
        </View>
        <View style={styles.pencilSlot}>
          <PencilProp size={72} rotation={-32} />
        </View>
      </View>
      {children}
    </WoodBackground>
  );
}

const styles = StyleSheet.create({
  // Posicionados pra viverem na margem de madeira visível acima/ao lado
  // do notepad (ver paddingTop do NotepadCard) -- em telas onde o card
  // ocupa quase tudo, essa margem ainda existe, só fica mais estreita.
  coffeeSlot: {
    position: 'absolute',
    top: 6,
    left: 14,
  },
  pencilSlot: {
    position: 'absolute',
    top: 22,
    right: -6,
  },
});
