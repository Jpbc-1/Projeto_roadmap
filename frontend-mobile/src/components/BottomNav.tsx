import React from 'react';
import { View, Text, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useSafeAreaInsets } from 'react-native-safe-area-context';
import { colors, spacing, typography, touchTarget } from '../theme/colors';

type NavItem = {
  key: string;
  label: string;
  iconOutline: keyof typeof Ionicons.glyphMap;
  iconFilled: keyof typeof Ionicons.glyphMap;
};

const items: NavItem[] = [
  { key: 'inicio', label: 'Início', iconOutline: 'home-outline', iconFilled: 'home' },
  { key: 'objetivos', label: 'Objetivos', iconOutline: 'flag-outline', iconFilled: 'flag' },
  { key: 'comunidade', label: 'Comunidade', iconOutline: 'people-outline', iconFilled: 'people' },
  { key: 'rotina', label: 'Rotina', iconOutline: 'calendar-outline', iconFilled: 'calendar' },
];

type BottomNavProps = {
  active: string;
  onSelect: (key: string) => void;
};

// Visual reference only — no routing included. Plug `onSelect` into
// React Navigation / Expo Router / whatever the project already uses.
export default function BottomNav({ active, onSelect }: BottomNavProps) {
  // The bar sits at the very bottom of the screen, which on Android is
  // exactly where the gesture bar / 3-button nav lives. insets.bottom is
  // the exact height of that system area on THIS device — we add a bit of
  // our own breathing room (spacing.sm) on top of it rather than guessing
  // a fixed pixel value that would be wrong on half the phones out there.
  const insets = useSafeAreaInsets();

  return (
    <View style={[styles.bar, { paddingBottom: insets.bottom + spacing.sm }]}>
      {items.map((item) => {
        const isActive = item.key === active;
        const tint = isActive ? colors.primary : colors.textSecondary;
        return (
          <TouchableOpacity
            key={item.key}
            style={styles.item}
            onPress={() => onSelect(item.key)}
            accessibilityRole="tab"
            accessibilityState={{ selected: isActive }}
            accessibilityLabel={item.label}
          >
            <Ionicons name={isActive ? item.iconFilled : item.iconOutline} size={22} color={tint} />
            <Text style={[styles.label, { color: tint, fontWeight: isActive ? '700' : '500' }]}>{item.label}</Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    borderTopWidth: 1,
    borderTopColor: colors.border,
    backgroundColor: colors.surface,
    paddingTop: spacing.sm,
  },
  item: {
    flex: 1,
    minHeight: touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
  },
  label: {
    ...typography.caption,
    fontSize: 11,
  },
});