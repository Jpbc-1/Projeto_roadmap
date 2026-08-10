import React from 'react';
import { ActivityIndicator, Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';

type PrimaryButtonProps = {
  label: string;
  onPress: () => void;
  loading?: boolean;
  disabled?: boolean;
};

export function PrimaryButton({ label, onPress, loading, disabled }: PrimaryButtonProps) {
  return (
    <TouchableOpacity
      style={[styles.primary, (disabled || loading) && styles.primaryDisabled]}
      onPress={onPress}
      disabled={disabled || loading}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      {loading ? <ActivityIndicator color={colors.surface} /> : <Text style={styles.primaryText}>{label}</Text>}
    </TouchableOpacity>
  );
}

type SocialButtonProps = {
  provider: 'google' | 'facebook';
  onPress: () => void;
};

// "G" e "f" desenhados com View/Text simples em vez de puxar um pacote de
// logos de terceiro só por dois ícones — mantém a mesma filosofia
// "nada de asset extra pra um detalhe pequeno" do resto do tema.
export function SocialButton({ provider, onPress }: SocialButtonProps) {
  const label = provider === 'google' ? 'Continuar com Google' : 'Continuar com Facebook';
  return (
    <TouchableOpacity style={styles.social} onPress={onPress} accessibilityRole="button" accessibilityLabel={label}>
      {provider === 'google' ? (
        <View style={styles.googleMark}>
          <Text style={styles.googleMarkText}>G</Text>
        </View>
      ) : (
        <View style={styles.facebookMark}>
          <Ionicons name="logo-facebook" size={16} color={colors.surface} />
        </View>
      )}
      <Text style={styles.socialText}>{label}</Text>
    </TouchableOpacity>
  );
}

export function AuthDivider() {
  return (
    <View style={styles.dividerRow}>
      <View style={styles.dividerLine} />
      <Text style={styles.dividerText}>ou</Text>
      <View style={styles.dividerLine} />
    </View>
  );
}

const styles = StyleSheet.create({
  primary: {
    minHeight: touchTarget,
    borderRadius: radius.md,
    backgroundColor: colors.textPrimary,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.sm,
  },
  primaryDisabled: {
    opacity: 0.55,
  },
  primaryText: {
    ...typography.body,
    fontSize: 15,
    fontFamily: fonts.bodySemiBold,
    color: colors.surface,
  },
  dividerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginVertical: spacing.md,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: colors.notebookRuleLine,
  },
  dividerText: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
  },
  social: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: touchTarget - 8,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
    marginBottom: spacing.sm,
  },
  googleMark: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#FFFFFF',
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
  },
  googleMarkText: {
    fontSize: 11,
    fontFamily: fonts.bodyBold,
    color: '#4285F4',
  },
  facebookMark: {
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: '#1877F2',
    alignItems: 'center',
    justifyContent: 'center',
  },
  socialText: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
  },
});
