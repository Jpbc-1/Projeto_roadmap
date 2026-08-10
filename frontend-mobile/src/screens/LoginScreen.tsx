import React, { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import DeskBackground from '../components/DeskBackground';
import NotepadCard from '../components/NotepadCard';
import AuthTextField from '../components/AuthTextField';
import { AuthDivider, PrimaryButton, SocialButton } from '../components/AuthButton';
import { colors, spacing, typography, fonts } from '../theme/colors';
import { useAuth } from '../context/AuthContext';

type LoginScreenProps = {
  onNavigateToRegister: () => void;
};

export default function LoginScreen({ onNavigateToRegister }: LoginScreenProps) {
  const { login } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!email.trim() || !password) {
      setError('Preencha e-mail e senha pra continuar.');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await login(email.trim(), password);
    } catch (err: any) {
      const status = err?.response?.status;
      setError(status === 401 ? 'E-mail ou senha incorretos.' : 'Não foi possível entrar agora. Tente de novo.');
    } finally {
      setSubmitting(false);
    }
  }

  function handleSocial(provider: 'google' | 'facebook') {
    Alert.alert('Em breve', `Login com ${provider === 'google' ? 'Google' : 'Facebook'} ainda não está disponível — use e-mail e senha por enquanto.`);
  }

  return (
    <DeskBackground>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <NotepadCard>
            <View style={styles.iconBadge}>
              <Ionicons name="book-outline" size={20} color={colors.primaryText} />
            </View>
            <Text style={styles.title}>Jornada</Text>
            <Text style={styles.subtitle}>Bem-vindo de volta. Sua jornada continua de onde parou.</Text>

            <AuthTextField
              label="E-mail"
              placeholder="seu@email.com"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
            />
            <AuthTextField
              label="Senha"
              placeholder="••••••••"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
            />

            {error && <Text style={styles.errorText}>{error}</Text>}

            <TouchableOpacity accessibilityRole="button" style={styles.forgotLink}>
              <Text style={styles.forgotText}>Esqueci minha senha</Text>
            </TouchableOpacity>

            <PrimaryButton label="Entrar" onPress={handleSubmit} loading={submitting} />

            <AuthDivider />

            <SocialButton provider="google" onPress={() => handleSocial('google')} />
            <SocialButton provider="facebook" onPress={() => handleSocial('facebook')} />

            <TouchableOpacity onPress={onNavigateToRegister} accessibilityRole="button" style={styles.footerLink}>
              <Text style={styles.footerText}>
                Primeira vez aqui? <Text style={styles.footerLink2}>Criar conta</Text>
              </Text>
            </TouchableOpacity>
          </NotepadCard>
        </ScrollView>
      </KeyboardAvoidingView>
    </DeskBackground>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  scrollContent: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
  },
  iconBadge: {
    width: 40,
    height: 40,
    borderRadius: 12,
    backgroundColor: colors.primaryTint,
    alignItems: 'center',
    justifyContent: 'center',
    alignSelf: 'center',
    marginBottom: spacing.sm,
  },
  title: {
    fontFamily: fonts.handwritten,
    fontSize: 40,
    color: colors.textPrimary,
    textAlign: 'center',
    lineHeight: 44,
  },
  subtitle: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 4,
    marginBottom: spacing.lg,
    paddingHorizontal: spacing.sm,
  },
  errorText: {
    ...typography.caption,
    fontSize: 12,
    color: colors.ratingAgain,
    marginTop: -spacing.sm,
    marginBottom: spacing.sm,
  },
  forgotLink: {
    alignSelf: 'flex-end',
    marginBottom: spacing.md,
  },
  forgotText: {
    ...typography.caption,
    fontSize: 12,
    fontFamily: fonts.bodySemiBold,
    color: colors.primaryText,
  },
  footerLink: {
    alignSelf: 'center',
    marginTop: spacing.md,
  },
  footerText: {
    ...typography.caption,
    fontSize: 13,
    color: colors.textSecondary,
  },
  footerLink2: {
    fontFamily: fonts.bodySemiBold,
    color: colors.primaryText,
  },
});
