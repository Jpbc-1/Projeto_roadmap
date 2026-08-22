import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { useNetInfo } from '@react-native-community/netinfo';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, typography } from '../theme/colors';

export default function OfflineBanner() {
  const netInfo = useNetInfo();

  // Só exibe o banner se tivermos certeza de que a internet caiu.
  // netInfo.isConnected pode ser 'null' no milissegundo inicial enquanto ele checa.
  if (netInfo.isConnected !== false) return null;

  return (
    <View style={styles.container}>
      <Ionicons name="cloud-offline-outline" size={16} color={colors.textSecondary} />
      <Text style={styles.text}>
        Você está offline.
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    backgroundColor: colors.surface,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  text: {
    ...typography.caption,
    color: colors.textSecondary,
  },
});