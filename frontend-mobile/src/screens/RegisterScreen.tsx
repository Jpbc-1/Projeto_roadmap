import React, { useState } from 'react';
import { Alert, KeyboardAvoidingView, Platform, ScrollView, Text, TouchableOpacity, View, StyleSheet } from 'react-native';
import DeskBackground from '../components/DeskBackground';
import NotepadCard from '../components/NotepadCard';
import AuthTextField from '../components/AuthTextField';
import { AuthDivider, PrimaryButton, SocialButton } from '../components/AuthButton';
import { colors, spacing, typography, fonts } from '../theme/colors';
import { useAuth } from '../context/AuthContext';

type RegisterScreenProps = {
  onNavigateToLogin: () => void;
};

const MIN_PASSWORD_LENGTH = 8;

export default function RegisterScreen({ onNavigateToLogin }: RegisterScreenProps) {
  const { register } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit() {
    if (!email.trim() || !password) {
      setError('Preencha e-mail e senha pra continuar.');
      return;
    }
    // O back não impõe um mínimo de senha hoje (aceitaria até "a") -- vale
    // manter essa checagem aqui mesmo assim, não é sensato depender só do
    // servidor pra isso.
    if (password.length < MIN_PASSWORD_LENGTH) {
      setError(`Sua senha precisa ter pelo menos ${MIN_PASSWORD_LENGTH} caracteres.`);
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await register(email.trim(), password, name.trim() || undefined);
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === 'string' ? detail : 'Não foi possível criar sua conta agora. Tente de novo.');
    } finally {
      setSubmitting(false);
    }
  }

  function handleSocial(provider: 'google' | 'facebook') {
    Alert.alert('Em breve', `Cadastro com ${provider === 'google' ? 'Google' : 'Facebook'} ainda não está disponível — use e-mail e senha por enquanto.`);
  }

  return (
    <DeskBackground>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <NotepadCard>
            <Text style={styles.eyebrow}>página 1 de muitas</Text>
            <Text style={styles.title}>Começar do zero</Text>
            <Text style={styles.subtitle}>Sua primeira página está em branco. Vamos preenchê-la juntos.</Text>

            <AuthTextField label="Nome" placeholder="Como posso te chamar?" autoCapitalize="words" value={name} onChangeText={setName} />
            <AuthTextField
              label="E-mail"
              placeholder="seu@email.com"
              keyboardType="email-address"
              value={email}
              onChangeText={setEmail}
            />
            <AuthTextField
              label="Senha"
              placeholder="Crie uma senha forte"
              secureTextEntry
              value={password}
              onChangeText={setPassword}
            />

            {error && <Text style={styles.errorText}>{error}</Text>}

            <PrimaryButton label="Começar jornada →" onPress={handleSubmit} loading={submitting} />

            <AuthDivider />

            <SocialButton provider="google" onPress={() => handleSocial('google')} />
            <SocialButton provider="facebook" onPress={() => handleSocial('facebook')} />

            <TouchableOpacity onPress={onNavigateToLogin} accessibilityRole="button" style={styles.footerLink}>
              <Text style={styles.footerText}>
                Já tem uma conta? <Text style={styles.footerLink2}>Entrar</Text>
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
  eyebrow: {
    ...typography.eyebrow,
    fontSize: 11,
    color: colors.textSecondary,
    textAlign: 'center',
  },
  title: {
    fontFamily: fonts.handwritten,
    fontSize: 36,
    color: colors.textPrimary,
    textAlign: 'center',
    lineHeight: 40,
    marginTop: 2,
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
