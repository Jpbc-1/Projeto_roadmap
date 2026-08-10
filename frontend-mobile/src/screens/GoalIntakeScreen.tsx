import React, { useState } from 'react';
import { KeyboardAvoidingView, Platform, ScrollView, Text, TextInput, TouchableOpacity, View, StyleSheet } from 'react-native';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import DeskBackground from '../components/DeskBackground';
import NotepadCard from '../components/NotepadCard';
import { PrimaryButton } from '../components/AuthButton';
import { goalService, PriorKnowledgeLevel, InsufficientCreditsError } from '../services/goalService';

type GoalIntakeScreenProps = {
  onCreated: (goalId: number) => void;
};

type CategoryKey = 'tecnologia' | 'financas' | 'saude' | 'estudos' | 'projetos';

// Tocar num chip pré-preenche um ponto de partida editável -- trocar
// "página em branco" por "edite isso" é a maior redução de atrito que dá
// pra fazer sem mexer em mais nada (pedido explícito: "diminuir o
// atrito pra pessoa conseguir fazer um roadmap").
const CATEGORIES: { key: CategoryKey; label: string; icon: string; starter: string }[] = [
  { key: 'tecnologia', label: 'Tecnologia', icon: '💻', starter: 'Quero aprender a programar e criar meus próprios projetos.' },
  { key: 'financas', label: 'Finanças', icon: '💰', starter: 'Quero organizar minhas finanças e aprender a investir.' },
  { key: 'saude', label: 'Saúde', icon: '🏃', starter: 'Quero criar uma rotina de exercícios e me sentir mais disposto.' },
  { key: 'estudos', label: 'Estudos', icon: '📚', starter: 'Quero me preparar para uma prova/certificação importante.' },
  { key: 'projetos', label: 'Projetos', icon: '🎨', starter: 'Quero tirar do papel um projeto pessoal que ando adiando.' },
];

const DAYS_OPTIONS: { label: string; value: number }[] = [
  { label: '1–2 dias', value: 2 },
  { label: '3–4 dias', value: 4 },
  { label: '5–7 dias', value: 6 },
];

const MINUTES_OPTIONS: { label: string; value: number }[] = [
  { label: '~15 min', value: 15 },
  { label: '~30 min', value: 30 },
  { label: '~1h', value: 60 },
  { label: '2h+', value: 120 },
];

const LEVEL_OPTIONS: { label: string; value: PriorKnowledgeLevel }[] = [
  { label: 'Iniciante', value: 'beginner' },
  { label: 'Intermediário', value: 'intermediate' },
  { label: 'Avançado', value: 'advanced' },
];

const DEADLINE_OPTIONS: { label: string; months: number | null }[] = [
  { label: 'Sem prazo', months: null },
  { label: '1–3 meses', months: 2 },
  { label: '3–6 meses', months: 4 },
  { label: '6+ meses', months: 8 },
];

function monthsFromNowIso(months: number): string {
  const date = new Date();
  date.setMonth(date.getMonth() + months);
  return date.toISOString().slice(0, 10);
}

export default function GoalIntakeScreen({ onCreated }: GoalIntakeScreenProps) {
  const [prompt, setPrompt] = useState('');
  const [activeCategory, setActiveCategory] = useState<CategoryKey | null>(null);
  const [days, setDays] = useState<number | null>(null);
  const [minutes, setMinutes] = useState<number | null>(null);
  const [level, setLevel] = useState<PriorKnowledgeLevel | null>(null);
  const [deadlineMonths, setDeadlineMonths] = useState<number | null | undefined>(undefined); // undefined = ainda não escolheu
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function pickCategory(category: typeof CATEGORIES[number]) {
    // Só troca o texto (e só marca o chip como ativo) se o campo estiver
    // vazio ou ainda mostrando um ponto de partida "intocado" de
    // qualquer categoria — inclusive trocando de uma pra outra. Se a
    // pessoa já editou o texto, um toque no chip não sobrescreve nada
    // (e não finge que aquele chip representa o texto atual).
    const isEmptyOrUntouchedStarter = !prompt.trim() || CATEGORIES.some((c) => c.starter === prompt);
    if (isEmptyOrUntouchedStarter) {
      setPrompt(category.starter);
      setActiveCategory(category.key);
    }
  }

  async function handleSubmit() {
    if (prompt.trim().length < 8) {
      setError('Conta um pouco mais sobre o que você quer alcançar.');
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      const { goal } = await goalService.create({
        context_prompt: prompt.trim(),
        weekly_active_days: days ?? undefined,
        daily_time_minutes: minutes ?? undefined,
        prior_knowledge_level: level ?? undefined,
        target_date: deadlineMonths ? monthsFromNowIso(deadlineMonths) : undefined,
      });
      onCreated(goal.id);
    } catch (err) {
      if (err instanceof InsufficientCreditsError) {
        setError(err.message);
      } else {
        setError('Não foi possível criar seu plano agora. Tente de novo em instantes.');
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <DeskBackground>
      <KeyboardAvoidingView style={styles.flex} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <ScrollView contentContainerStyle={styles.scrollContent} keyboardShouldPersistTaps="handled">
          <NotepadCard pinCount={3}>
            <Text style={styles.title}>Qual objetivo você quer alcançar?</Text>
            <Text style={styles.subtitle}>
              Não precisa ser perfeito — escreva com suas palavras. A IA transforma isso num plano por
              etapas, e ajusta com você se faltar algum detalhe.
            </Text>

            <TextInput
              style={styles.promptInput}
              placeholder="Ex: Quero criar meu primeiro aplicativo."
              placeholderTextColor={colors.textSecondary}
              value={prompt}
              onChangeText={(text) => {
                setPrompt(text);
                if (activeCategory) setActiveCategory(null);
              }}
              multiline
              maxLength={4000}
              textAlignVertical="top"
            />

            <Text style={styles.sectionLabel}>OU ESCOLHA UM PONTO DE PARTIDA</Text>
            <View style={styles.chipWrap}>
              {CATEGORIES.map((category) => (
                <Chip
                  key={category.key}
                  label={`${category.icon}  ${category.label}`}
                  active={activeCategory === category.key}
                  onPress={() => pickCategory(category)}
                />
              ))}
            </View>

            <View style={styles.optionalBlock}>
              <Text style={styles.optionalTitle}>Perfil rápido (opcional)</Text>
              <Text style={styles.optionalHint}>
                Ajuda a IA a calibrar o ritmo. Pule o que não souber agora — se faltar algo importante, ela
                pergunta em seguida.
              </Text>

              <MiniQuestion label="Dias por semana">
                {DAYS_OPTIONS.map((opt) => (
                  <Chip key={opt.value} label={opt.label} active={days === opt.value} onPress={() => setDays(days === opt.value ? null : opt.value)} small />
                ))}
              </MiniQuestion>

              <MiniQuestion label="Tempo por dia">
                {MINUTES_OPTIONS.map((opt) => (
                  <Chip key={opt.value} label={opt.label} active={minutes === opt.value} onPress={() => setMinutes(minutes === opt.value ? null : opt.value)} small />
                ))}
              </MiniQuestion>

              <MiniQuestion label="Seu nível">
                {LEVEL_OPTIONS.map((opt) => (
                  <Chip key={opt.value} label={opt.label} active={level === opt.value} onPress={() => setLevel(level === opt.value ? null : opt.value)} small />
                ))}
              </MiniQuestion>

              <MiniQuestion label="Prazo" last>
                {DEADLINE_OPTIONS.map((opt) => (
                  <Chip
                    key={opt.label}
                    label={opt.label}
                    active={deadlineMonths === opt.months}
                    onPress={() => setDeadlineMonths(deadlineMonths === opt.months ? undefined : opt.months)}
                    small
                  />
                ))}
              </MiniQuestion>
            </View>

            {error && <Text style={styles.errorText}>{error}</Text>}

            <PrimaryButton label="Criar meu plano →" onPress={handleSubmit} loading={submitting} />
            <Text style={styles.reassurance}>Leva menos de um minuto. Você pode ajustar tudo depois.</Text>
          </NotepadCard>
        </ScrollView>
      </KeyboardAvoidingView>
    </DeskBackground>
  );
}

function MiniQuestion({ label, children, last }: { label: string; children: React.ReactNode; last?: boolean }) {
  return (
    <View style={[styles.miniQuestion, last && styles.miniQuestionLast]}>
      <Text style={styles.miniQuestionLabel}>{label}</Text>
      <View style={styles.chipWrap}>{children}</View>
    </View>
  );
}

function Chip({ label, active, onPress, small }: { label: string; active: boolean; onPress: () => void; small?: boolean }) {
  return (
    <TouchableOpacity
      style={[styles.chip, small && styles.chipSmall, active && styles.chipActive]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
    >
      <Text style={[styles.chipText, small && styles.chipTextSmall, active && styles.chipTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  flex: { flex: 1 },
  scrollContent: {
    paddingHorizontal: spacing.lg,
    paddingBottom: spacing.xl,
    paddingTop: spacing.sm,
  },
  title: {
    ...typography.screenTitle,
    fontSize: 22,
    lineHeight: 27,
    color: colors.textPrimary,
  },
  subtitle: {
    ...typography.caption,
    fontSize: 13,
    lineHeight: 18,
    color: colors.textSecondary,
    marginTop: 6,
    marginBottom: spacing.md,
  },
  promptInput: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    minHeight: 96,
  },
  sectionLabel: {
    ...typography.eyebrow,
    fontSize: 10,
    color: colors.textSecondary,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  chipWrap: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  chip: {
    minHeight: touchTarget - 8,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    alignItems: 'center',
    justifyContent: 'center',
  },
  chipSmall: {
    minHeight: 30,
    paddingHorizontal: spacing.sm + 2,
  },
  chipActive: {
    backgroundColor: colors.textPrimary,
    borderColor: colors.textPrimary,
  },
  chipText: {
    ...typography.body,
    fontSize: 13,
    color: colors.textPrimary,
  },
  chipTextSmall: {
    fontSize: 12,
  },
  chipTextActive: {
    color: colors.surface,
    fontFamily: fonts.bodySemiBold,
  },
  optionalBlock: {
    marginTop: spacing.lg,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: colors.notebookRuleLine,
  },
  optionalTitle: {
    ...typography.cardTitle,
    fontSize: 14,
    color: colors.textPrimary,
  },
  optionalHint: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
    marginTop: 2,
    marginBottom: spacing.sm,
  },
  miniQuestion: {
    marginBottom: spacing.sm,
  },
  miniQuestionLast: {
    marginBottom: 0,
  },
  miniQuestionLabel: {
    ...typography.caption,
    fontSize: 11,
    fontFamily: fonts.bodyMedium,
    color: colors.textSecondary,
    marginBottom: 6,
  },
  errorText: {
    ...typography.caption,
    fontSize: 12,
    color: colors.ratingAgain,
    marginTop: spacing.md,
  },
  reassurance: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.sm,
  },
});
