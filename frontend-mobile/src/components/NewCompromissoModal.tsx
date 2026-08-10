import React, { useState } from 'react';
import {
  Modal,
  Platform,
  Pressable,
  ScrollView,
  Text,
  TextInput,
  TouchableOpacity,
  View,
  StyleSheet,
  KeyboardAvoidingView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import DateTimePicker, { DateTimePickerAndroid, DateTimePickerEvent } from '@react-native-community/datetimepicker';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import { useCreateCalendarEvent, useCreateReminder } from '../hooks/useAgenda';
import { addDays, dateToTimeString, formatHM, formatLongDate, isSameDay } from '../utils/dateUtils';
import MonthCalendarPicker from './MonthCalendarPicker';
import { NotificationStyle } from '../services/calendarEventService';

type ItemType = 'compromisso' | 'lembrete' | 'evento';
type QuickDateMode = 'hoje' | 'amanha' | 'semana' | 'outro';
type ReminderMinutes = 0 | 15 | 30 | 60;

type NewCompromissoModalProps = {
  visible: boolean;
  onClose: () => void;
  /** O dia que estava selecionado na tela ao abrir o modal — vira o
   * ponto de partida de "Para quando?" (ainda pode ser trocado lá dentro). */
  initialDate: Date;
};

const TYPE_OPTIONS: { key: ItemType; label: string; icon: keyof typeof Ionicons.glyphMap }[] = [
  { key: 'compromisso', label: 'Compromisso', icon: 'document-text-outline' },
  { key: 'lembrete', label: 'Lembrete', icon: 'notifications-outline' },
  { key: 'evento', label: 'Evento', icon: 'star-outline' },
];

const REMINDER_MINUTE_OPTIONS: { value: ReminderMinutes; label: string }[] = [
  { value: 0, label: 'Na hora' },
  { value: 15, label: '15 min' },
  { value: 30, label: '30 min' },
  { value: 60, label: '1 hora' },
];

function resolveQuickMode(seedDate: Date): QuickDateMode {
  const today = new Date();
  if (isSameDay(seedDate, today)) return 'hoje';
  if (isSameDay(seedDate, addDays(today, 1))) return 'amanha';
  if (isSameDay(seedDate, addDays(today, 7))) return 'semana';
  return 'outro';
}

function initialState(seedDate: Date) {
  return {
    dateMode: resolveQuickMode(seedDate),
    selectedDate: seedDate,
    showCalendar: false,
    title: '',
    time: null as Date | null,
    showTimePicker: false,
    type: 'compromisso' as ItemType,
    remindBefore: 15 as ReminderMinutes,
    messageStyle: 'padrao' as 'padrao' | 'personalizada',
    customMessage: '',
  };
}

export default function NewCompromissoModal({ visible, onClose, initialDate }: NewCompromissoModalProps) {
  const [state, setState] = useState(() => initialState(initialDate));
  const createEvent = useCreateCalendarEvent();
  const createReminder = useCreateReminder();
  const isSubmitting = createEvent.isPending || createReminder.isPending;
  const submitError = createEvent.isError || createReminder.isError;

  function patch(partial: Partial<ReturnType<typeof initialState>>) {
    setState((prev) => ({ ...prev, ...partial }));
  }

  function handleClose() {
    setState(initialState(initialDate));
    createEvent.reset();
    createReminder.reset();
    onClose();
  }

  function selectQuickDate(mode: QuickDateMode) {
    const today = new Date();
    if (mode === 'hoje') patch({ dateMode: mode, selectedDate: today, showCalendar: false });
    else if (mode === 'amanha') patch({ dateMode: mode, selectedDate: addDays(today, 1), showCalendar: false });
    else if (mode === 'semana') patch({ dateMode: mode, selectedDate: addDays(today, 7), showCalendar: false });
    else patch({ dateMode: mode, showCalendar: !state.showCalendar });
  }

  function onChangeTime(event: DateTimePickerEvent, selected?: Date) {
    if (event.type === 'dismissed') return;
    if (selected) patch({ time: selected });
  }

  // Android's own docs recommend the imperative dialog API over the
  // declarative <DateTimePicker> component — it models the native
  // "opens like an alert" behavior more faithfully and has a longer
  // history of issues when used as a regular component. iOS has no
  // imperative equivalent, so it keeps the inline spinner below.
  function openTimePicker() {
    if (Platform.OS === 'android') {
      DateTimePickerAndroid.open({
        value: state.time ?? new Date(),
        mode: 'time',
        is24Hour: true,
        onChange: onChangeTime,
      });
    } else {
      patch({ showTimePicker: true });
    }
  }

  const canSubmit = state.title.trim().length > 0 && state.time !== null && !isSubmitting;

  function handleSave() {
    if (!canSubmit || !state.time) return;

    const notificationStyle: NotificationStyle = state.messageStyle === 'personalizada' ? 'custom_message' : 'app_generated';
    const customMessage = state.messageStyle === 'personalizada' ? state.customMessage.trim() || null : null;

    if (state.type === 'lembrete') {
      createReminder.mutate(
        {
          label: state.title.trim(),
          time_of_day: dateToTimeString(state.time),
          // Um Lembrete é recorrente por dia-da-semana no back — aqui a
          // pessoa só escolhe UMA data neste modal (não um conjunto de
          // dias), então a leitura mais natural é "repete toda
          // <dia-da-semana escolhido>", não todo santo dia. Se isso não
          // for o que você quer, vale trocar por um seletor de dias como
          // o da AvailabilityCard antiga.
          days_of_week: [state.selectedDate.getDay()],
          notification_timing_mode: 'custom',
          notification_style: notificationStyle,
          custom_message: customMessage,
        },
        { onSuccess: handleClose }
      );
      return;
    }

    // 'compromisso' e 'evento' viram o mesmo CalendarEvent no back — ele
    // não tem um campo pra distinguir os dois hoje. O ícone/rótulo que a
    // pessoa escolheu só existe no momento da criação; ao recarregar a
    // lista do servidor, todo CalendarEvent volta com o mesmo tratamento
    // visual (ver accentFor em AgendaEventCard.tsx).
    const start = new Date(state.selectedDate);
    start.setHours(state.time.getHours(), state.time.getMinutes(), 0, 0);

    createEvent.mutate(
      {
        title: state.title.trim(),
        start_datetime: start.toISOString(),
        notify_enabled: true,
        remind_before_minutes: state.remindBefore,
        notification_timing_mode: 'custom',
        notification_style: notificationStyle,
        custom_message: customMessage,
      },
      { onSuccess: handleClose }
    );
  }

  const previewBody =
    state.messageStyle === 'personalizada' && state.customMessage.trim()
      ? state.customMessage.trim()
      : state.type === 'lembrete'
        ? `Hora de: ${state.title || 'seu lembrete'}`
        : `Hora do seu compromisso: ${state.title || 'compromisso'}`;

  return (
    <Modal visible={visible} transparent animationType="slide" onRequestClose={handleClose}>
      <KeyboardAvoidingView
        style={styles.overlay}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <Pressable style={StyleSheet.absoluteFill} onPress={handleClose} accessibilityLabel="Fechar" />

        <View style={styles.sheet}>
          <View style={styles.header}>
            <Text style={styles.headerTitle}>Novo compromisso</Text>
            <TouchableOpacity
              onPress={handleClose}
              hitSlop={{ top: 10, bottom: 10, left: 10, right: 10 }}
              accessibilityRole="button"
              accessibilityLabel="Fechar"
            >
              <Ionicons name="close" size={22} color={colors.textPrimary} />
            </TouchableOpacity>
          </View>

          <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled">
            <Text style={styles.label}>Para quando?</Text>
            <View style={styles.pillRow}>
              <QuickPill label="Hoje" active={state.dateMode === 'hoje'} onPress={() => selectQuickDate('hoje')} />
              <QuickPill label="Amanhã" active={state.dateMode === 'amanha'} onPress={() => selectQuickDate('amanha')} />
              <QuickPill label="+1 semana" active={state.dateMode === 'semana'} onPress={() => selectQuickDate('semana')} />
            </View>
            <TouchableOpacity
              style={[styles.otherDayButton, state.dateMode === 'outro' && styles.otherDayButtonActive]}
              onPress={() => selectQuickDate('outro')}
              accessibilityRole="button"
              accessibilityLabel="Escolher outro dia"
            >
              <Ionicons name="calendar-outline" size={16} color={colors.textPrimary} />
              <Text style={styles.otherDayText}>
                {state.dateMode === 'outro' ? formatLongDate(state.selectedDate) : 'Outro dia'}
              </Text>
              <Ionicons name={state.showCalendar ? 'chevron-up' : 'chevron-down'} size={16} color={colors.textSecondary} />
            </TouchableOpacity>
            {state.showCalendar && (
              <MonthCalendarPicker
                selectedDate={state.selectedDate}
                onSelectDate={(date) => patch({ selectedDate: date, dateMode: 'outro' })}
              />
            )}

            <Text style={styles.label}>O que é?</Text>
            <TextInput
              style={styles.textInput}
              placeholder="Academia, Reunião, Almoço..."
              placeholderTextColor={colors.textSecondary}
              value={state.title}
              onChangeText={(title) => patch({ title })}
              maxLength={120}
              returnKeyType="done"
            />

            <Text style={styles.label}>Que horas?</Text>
            <TouchableOpacity
              style={styles.timeInput}
              onPress={openTimePicker}
              accessibilityRole="button"
              accessibilityLabel="Escolher horário"
            >
              <Text style={state.time ? styles.timeValue : styles.timePlaceholder}>
                {state.time ? formatHM(state.time) : '--:--'}
              </Text>
              <Ionicons name="time-outline" size={18} color={colors.textSecondary} />
            </TouchableOpacity>
            {Platform.OS === 'ios' && state.showTimePicker && (
              <View style={styles.iosPickerWrap}>
                <DateTimePicker value={state.time ?? new Date()} mode="time" is24Hour display="spinner" onChange={onChangeTime} />
                <TouchableOpacity style={styles.iosPickerDone} onPress={() => patch({ showTimePicker: false })}>
                  <Text style={styles.iosPickerDoneText}>Concluído</Text>
                </TouchableOpacity>
              </View>
            )}

            <Text style={styles.label}>Tipo</Text>
            <View style={styles.typeRow}>
              {TYPE_OPTIONS.map((option) => {
                const active = state.type === option.key;
                return (
                  <TouchableOpacity
                    key={option.key}
                    style={[styles.typeCard, active && styles.typeCardActive]}
                    onPress={() => patch({ type: option.key })}
                    accessibilityRole="button"
                    accessibilityLabel={option.label}
                    accessibilityState={{ selected: active }}
                  >
                    <Ionicons name={option.icon} size={20} color={colors.textPrimary} />
                    <Text style={styles.typeLabel}>{option.label}</Text>
                  </TouchableOpacity>
                );
              })}
            </View>

            <Text style={styles.label}>Notificação</Text>
            <Text style={styles.sublabel}>Quando avisar?</Text>
            <View style={styles.pillRow}>
              {REMINDER_MINUTE_OPTIONS.map((option) => (
                <QuickPill
                  key={option.value}
                  label={option.label}
                  active={state.remindBefore === option.value}
                  onPress={() => patch({ remindBefore: option.value })}
                />
              ))}
            </View>

            <Text style={styles.sublabel}>Mensagem</Text>
            <View style={styles.pillRow}>
              <MessageStyleOption
                icon="chatbubble-outline"
                label="Padrão"
                active={state.messageStyle === 'padrao'}
                onPress={() => patch({ messageStyle: 'padrao' })}
              />
              <MessageStyleOption
                icon="create-outline"
                label="Personalizada"
                active={state.messageStyle === 'personalizada'}
                onPress={() => patch({ messageStyle: 'personalizada' })}
              />
            </View>
            {state.messageStyle === 'personalizada' && (
              <TextInput
                style={styles.textInput}
                placeholder="Escreva a mensagem da notificação..."
                placeholderTextColor={colors.textSecondary}
                value={state.customMessage}
                onChangeText={(customMessage) => patch({ customMessage })}
                maxLength={200}
                multiline
              />
            )}

            <View style={styles.previewCard}>
              <View style={styles.previewIconBadge}>
                <Ionicons name="calendar" size={14} color={colors.textOnPrimary} />
              </View>
              <View style={styles.previewTextBlock}>
                <View style={styles.previewHeaderRow}>
                  <Text style={styles.previewApp}>Roadmap AI</Text>
                  <Text style={styles.previewWhen}>agora</Text>
                </View>
                <Text style={styles.previewBody} numberOfLines={2}>
                  {previewBody}
                </Text>
              </View>
            </View>

            <View style={styles.aiNote}>
              <Text style={styles.aiNoteText}>
                ✦ A IA vai encaixar suas missões nos horários livres desta agenda.
              </Text>
            </View>

            {submitError && (
              <Text style={styles.errorText}>Não foi possível salvar agora. Confira sua conexão e tente de novo.</Text>
            )}
          </ScrollView>

          <View style={styles.footer}>
            <TouchableOpacity style={styles.cancelButton} onPress={handleClose} accessibilityRole="button" accessibilityLabel="Cancelar">
              <Text style={styles.cancelText}>Cancelar</Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[styles.saveButton, !canSubmit && styles.saveButtonDisabled]}
              onPress={handleSave}
              disabled={!canSubmit}
              accessibilityRole="button"
              accessibilityLabel="Salvar na agenda"
            >
              <Text style={styles.saveText}>{isSubmitting ? 'Salvando...' : 'Salvar na agenda ✓'}</Text>
            </TouchableOpacity>
          </View>
        </View>
      </KeyboardAvoidingView>
    </Modal>
  );
}

function QuickPill({ label, active, onPress }: { label: string; active: boolean; onPress: () => void }) {
  return (
    <TouchableOpacity
      style={[styles.pill, active && styles.pillActive]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
    >
      <Text style={[styles.pillText, active && styles.pillTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

function MessageStyleOption({
  icon,
  label,
  active,
  onPress,
}: {
  icon: keyof typeof Ionicons.glyphMap;
  label: string;
  active: boolean;
  onPress: () => void;
}) {
  return (
    <TouchableOpacity
      style={[styles.pill, styles.messagePill, active && styles.pillActive]}
      onPress={onPress}
      accessibilityRole="button"
      accessibilityState={{ selected: active }}
    >
      <Ionicons name={icon} size={14} color={active ? colors.surface : colors.textPrimary} />
      <Text style={[styles.pillText, active && styles.pillTextActive]}>{label}</Text>
    </TouchableOpacity>
  );
}

const styles = StyleSheet.create({
  overlay: {
    flex: 1,
    backgroundColor: 'rgba(0,0,0,0.45)',
    justifyContent: 'flex-end',
  },
  sheet: {
    backgroundColor: colors.surface,
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.md,
    maxHeight: '88%',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: spacing.sm,
  },
  headerTitle: {
    ...typography.screenTitle,
    fontSize: 20,
    color: colors.textPrimary,
  },
  label: {
    ...typography.eyebrow,
    color: colors.textSecondary,
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  sublabel: {
    ...typography.caption,
    color: colors.textSecondary,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  pillRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  pill: {
    minHeight: touchTarget - 8,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.surface,
  },
  pillActive: {
    backgroundColor: colors.textPrimary,
    borderColor: colors.textPrimary,
  },
  pillText: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
  },
  pillTextActive: {
    color: colors.surface,
    fontFamily: fonts.bodySemiBold,
  },
  messagePill: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  otherDayButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: touchTarget - 8,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    borderWidth: 1,
    borderColor: colors.border,
    marginTop: spacing.sm,
    alignSelf: 'flex-start',
  },
  otherDayButtonActive: {
    borderColor: colors.textPrimary,
  },
  otherDayText: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
  },
  textInput: {
    ...typography.body,
    color: colors.textPrimary,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    padding: spacing.md,
    minHeight: touchTarget,
  },
  timeInput: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    minHeight: touchTarget,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingHorizontal: spacing.md,
  },
  timeValue: {
    fontFamily: fonts.displayMedium,
    fontSize: 16,
    color: colors.textPrimary,
  },
  timePlaceholder: {
    fontFamily: fonts.displayMedium,
    fontSize: 16,
    color: colors.textSecondary,
  },
  iosPickerWrap: {
    alignItems: 'flex-end',
  },
  iosPickerDone: {
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
  },
  iosPickerDoneText: {
    ...typography.body,
    fontSize: 14,
    fontFamily: fonts.bodySemiBold,
    color: colors.primaryText,
  },
  typeRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  typeCard: {
    flex: 1,
    minHeight: 72,
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: radius.md,
    paddingVertical: spacing.sm,
  },
  typeCardActive: {
    borderColor: colors.textPrimary,
    borderWidth: 1.5,
    backgroundColor: colors.neutralTint,
  },
  typeLabel: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textPrimary,
  },
  previewCard: {
    flexDirection: 'row',
    gap: spacing.sm,
    backgroundColor: colors.neutralTint,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.lg,
  },
  previewIconBadge: {
    width: 28,
    height: 28,
    borderRadius: radius.sm,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  previewTextBlock: {
    flex: 1,
  },
  previewHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  previewApp: {
    ...typography.caption,
    fontSize: 12,
    fontFamily: fonts.bodySemiBold,
    color: colors.textPrimary,
  },
  previewWhen: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
  },
  previewBody: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondary,
    marginTop: 2,
  },
  aiNote: {
    backgroundColor: colors.primaryTint,
    borderRadius: radius.md,
    padding: spacing.md,
    marginTop: spacing.md,
  },
  aiNoteText: {
    ...typography.caption,
    color: colors.primaryText,
  },
  errorText: {
    ...typography.caption,
    color: colors.ratingAgain,
    marginTop: spacing.md,
  },
  footer: {
    flexDirection: 'row',
    gap: spacing.sm,
    paddingVertical: spacing.md,
  },
  cancelButton: {
    flex: 1,
    minHeight: touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: colors.border,
  },
  cancelText: {
    ...typography.body,
    fontSize: 15,
    color: colors.textPrimary,
  },
  saveButton: {
    flex: 2,
    minHeight: touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.md,
    backgroundColor: colors.textPrimary,
  },
  saveButtonDisabled: {
    opacity: 0.4,
  },
  saveText: {
    ...typography.body,
    fontSize: 15,
    fontFamily: fonts.bodySemiBold,
    color: colors.surface,
  },
});
