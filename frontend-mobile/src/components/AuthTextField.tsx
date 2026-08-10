import React from 'react';
import { Text, TextInput, TextInputProps, View, StyleSheet } from 'react-native';
import { colors, spacing, typography, fonts } from '../theme/colors';

type AuthTextFieldProps = TextInputProps & {
  label: string;
  error?: string;
};

// Underlined, not boxed — "written directly on the ruled page" reads
// closer to the notepad concept than a bordered input box floating on
// top of it (and it's one less rectangle competing with the card and
// button shapes below it).
export default function AuthTextField({ label, error, style, ...inputProps }: AuthTextFieldProps) {
  return (
    <View style={styles.wrapper}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, style]}
        placeholderTextColor={colors.textSecondary}
        autoCapitalize="none"
        autoCorrect={false}
        {...inputProps}
      />
      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: {
    marginBottom: spacing.md,
  },
  label: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondary,
    marginBottom: 2,
  },
  input: {
    ...typography.body,
    fontSize: 15,
    color: colors.textPrimary,
    borderBottomWidth: 1,
    borderBottomColor: colors.notebookRuleLine,
    paddingVertical: 6,
  },
  error: {
    ...typography.caption,
    fontSize: 11,
    color: colors.ratingAgain,
    marginTop: 4,
  },
});
