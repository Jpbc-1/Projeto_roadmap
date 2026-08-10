import React from 'react';
import { View } from 'react-native';
import Svg, { Path, Ellipse, Rect, G } from 'react-native-svg';

// Actual little illustrations (not View-shape approximations like the
// wood grain speckles) — a pencil and a mug read as blocky nonsense if
// you try to fake them out of rotated rectangles, so this is the one
// place in the theme that reaches for react-native-svg (already a
// dependency, no new native install).
//
// Used sparingly and only behind the notepad card, same restraint
// PushPin/WashiTape already apply on Home — this is seasoning for the
// desk, not a full illustration scene.

export function PencilProp({ size = 64, rotation = -28 }: { size?: number; rotation?: number }) {
  return (
    <View style={{ width: size, height: size, transform: [{ rotate: `${rotation}deg` }] }}>
      <Svg width={size} height={size} viewBox="0 0 64 64">
        {/* corpo */}
        <Rect x="14" y="26" width="38" height="10" rx="1.5" fill="#D9A441" />
        <Rect x="14" y="26" width="38" height="3" fill="#F0C066" opacity={0.7} />
        {/* ponta de madeira */}
        <Path d="M52 26 L62 31 L52 36 Z" fill="#E8C79A" />
        {/* grafite */}
        <Path d="M58.5 28.6 L62 31 L58.5 33.4 Z" fill="#3A332B" />
        {/* virola metálica */}
        <Rect x="8" y="25.3" width="7" height="11.4" rx="1" fill="#C9CDD1" />
        <Rect x="9.5" y="25.3" width="1" height="11.4" fill="#9AA0A6" opacity={0.6} />
        <Rect x="12" y="25.3" width="1" height="11.4" fill="#9AA0A6" opacity={0.6} />
        {/* borracha */}
        <Rect x="2" y="25.3" width="7" height="11.4" rx="2.5" fill="#E39A9A" />
      </Svg>
    </View>
  );
}

export function CoffeeCupProp({ size = 72 }: { size?: number }) {
  return (
    <Svg width={size} height={size} viewBox="0 0 64 64">
      {/* vapor -- bem sutil, só pra dar vida sem virar o centro das atenções */}
      <G opacity={0.35}>
        <Path
          d="M24 14 C 21 11, 27 9, 24 5"
          stroke="#FFFFFF"
          strokeWidth={1.6}
          strokeLinecap="round"
          fill="none"
        />
        <Path
          d="M32 14 C 29 11, 35 9, 32 4"
          stroke="#FFFFFF"
          strokeWidth={1.6}
          strokeLinecap="round"
          fill="none"
        />
      </G>
      {/* alça */}
      <Path
        d="M46 30 C 56 30, 56 46, 46 46"
        stroke="#8A5A34"
        strokeWidth={4}
        fill="none"
        strokeLinecap="round"
      />
      {/* corpo da xícara */}
      <Path d="M14 24 H46 L43 50 a4 4 0 0 1 -4 3.4 H21 a4 4 0 0 1 -4 -3.4 Z" fill="#F4EFE6" />
      <Path d="M14 24 H46 L45.3 30 H14.7 Z" fill="#E7DFCE" />
      {/* café dentro */}
      <Ellipse cx="30" cy="25.5" rx="15.5" ry="2.6" fill="#5B3A22" />
      {/* pires */}
      <Ellipse cx="30" cy="56" rx="20" ry="3.4" fill="#F4EFE6" />
      <Ellipse cx="30" cy="56" rx="20" ry="3.4" fill="none" stroke="#D8CDB6" strokeWidth={1} />
    </Svg>
  );
}

/** Um clipe de papel simples -- terceiro detalhe opcional, bem pequeno,
 * pra variar a composição sem lotar a mesa (ver comentário no topo). */
export function PaperclipProp({ size = 28, rotation = 18 }: { size?: number; rotation?: number }) {
  return (
    <View style={{ width: size, height: size, transform: [{ rotate: `${rotation}deg` }] }}>
      <Svg width={size} height={size} viewBox="0 0 24 24">
        <Path
          d="M7 12.5 L15 4.5 a4 4 0 0 1 5.6 5.6 L11 20 a6 6 0 0 1 -8.5 -8.5 L11.5 3"
          stroke="#9AA0A6"
          strokeWidth={1.8}
          fill="none"
          strokeLinecap="round"
        />
      </Svg>
    </View>
  );
}
