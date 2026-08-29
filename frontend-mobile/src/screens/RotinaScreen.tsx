import React, { useMemo, useState } from 'react';
import { Text, TouchableOpacity, View, ScrollView, ActivityIndicator, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import AgendaBackground from '../components/AgendaBackground';
import WeekStrip from '../components/WeekStrip';
import UpcomingChip from '../components/UpcomingChip';
import DayTimeline from '../components/DayTimeline';
import MonthCalendarPicker from '../components/MonthCalendarPicker';
import NewCompromissoModal from '../components/NewCompromissoModal';
import { useDayAgenda, useUpcomingChips, useWeekCalendarEvents, useDeleteCalendarEvent } from '../hooks/useAgenda';
import { formatLongDate, formatMonthShort, greetingForHour } from '../utils/dateUtils';

export default function RotinaScreen() {
  const [selectedDate, setSelectedDate] = useState(() => new Date());
  const [monthPickerOpen, setMonthPickerOpen] = useState(false);
  const [modalVisible, setModalVisible] = useState(false);

  // Read once per mount, not on every render — the greeting shouldn't
  // flip from "Bom dia" to "Boa tarde" mid-scroll just because the clock
  // ticked past noon while the screen was already open.
  const [greeting] = useState(() => greetingForHour(new Date().getHours()));

  const { items: dayItems, isLoading: dayLoading } = useDayAgenda(selectedDate);
  const { items: upcomingItems } = useUpcomingChips();
  const weekEvents = useWeekCalendarEvents(selectedDate);
  const deleteEvent = useDeleteCalendarEvent();

  const daysWithEvents = useMemo(
    () => (weekEvents.data ?? []).map((e) => new Date(e.start_datetime)),
    [weekEvents.data]
  );

  function selectDate(date: Date) {
    setSelectedDate(date);
    setMonthPickerOpen(false);
  }

  return (
    <AgendaBackground>
      <View style={styles.header}>
        <View style={styles.headerTop}>
          <View>
            <Text style={styles.greeting}>{greeting}.</Text>
            <Text style={styles.title}>Agenda</Text>
          </View>
        </View>

        <View style={styles.dateRow}>
          <Text style={styles.dateLabel}>{formatLongDate(selectedDate)}</Text>
          <TouchableOpacity
            style={styles.monthButton}
            onPress={() => setMonthPickerOpen((prev) => !prev)}
            accessibilityRole="button"
            accessibilityLabel="Abrir calendário do mês"
          >
            <Text style={styles.monthButtonText}>{formatMonthShort(selectedDate)}</Text>
            <Ionicons name={monthPickerOpen ? 'chevron-up' : 'chevron-down'} size={14} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>

        {monthPickerOpen ? (
          <MonthCalendarPicker selectedDate={selectedDate} onSelectDate={selectDate} />
        ) : (
          <WeekStrip anchor={selectedDate} selectedDate={selectedDate} onSelectDate={selectDate} daysWithEvents={daysWithEvents} />
        )}

        {upcomingItems.length > 0 && (
          <ScrollView
            horizontal
            showsHorizontalScrollIndicator={false}
            style={styles.chipRow}
            contentContainerStyle={styles.chipRowContent}
          >
            {upcomingItems.map((item, index) => (
              <UpcomingChip key={item.key} item={item} colorIndex={index} onDismiss={() => deleteEvent.mutate(item.id)} />
            ))}
          </ScrollView>
        )}
      </View>

      <View style={styles.timelineWrapper}>
        {dayLoading ? (
          <ActivityIndicator style={styles.loading} color={colors.primaryText} />
        ) : (
          <DayTimeline day={selectedDate} items={dayItems} />
        )}
      </View>

      <TouchableOpacity
        style={styles.fab}
        onPress={() => setModalVisible(true)}
        activeOpacity={0.85}
        accessibilityRole="button"
        accessibilityLabel="Adicionar novo compromisso"
      >
        <Ionicons name="add" size={28} color={colors.textOnPrimary} />
      </TouchableOpacity>

      <NewCompromissoModal visible={modalVisible} onClose={() => setModalVisible(false)} initialDate={selectedDate} />
    </AgendaBackground>
  );
}

const FAB_SIZE = 56;

const styles = StyleSheet.create({
  header: {
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
    paddingBottom: spacing.md, // Um respiro legal embaixo dos dias da semana
    backgroundColor: '#F5EFE6', // Cor de fundo destacada para a parte fixa
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(31,22,12,0.08)', // Linha divisória sutil
  },
  headerTop: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  greeting: {
    ...typography.caption,
    fontFamily: fonts.bodyMedium,
    color: colors.textSecondary,
  },
  title: {
    ...typography.screenTitle,
    fontSize: 28,
    color: colors.textPrimary,
  },
  dateRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginTop: spacing.sm,
  },
  dateLabel: {
    ...typography.body,
    fontSize: 14,
    color: colors.textSecondary,
  },
  monthButton: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: touchTarget - 16,
    paddingHorizontal: spacing.md,
    borderRadius: radius.pill,
    backgroundColor: colors.primaryTint,
  },
  monthButtonText: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    color: colors.textPrimary,
  },
  chipRow: {
    marginTop: spacing.md,
  },
  chipRowContent: {
    paddingRight: spacing.md,
  },
  timelineWrapper: {
    flex: 1,
    marginTop: spacing.sm,
  },
  loading: {
    marginTop: spacing.xl,
  },
  fab: {
    position: 'absolute',
    right: spacing.md,
    bottom: spacing.lg,
    width: FAB_SIZE,
    height: FAB_SIZE,
    borderRadius: FAB_SIZE / 2,
    backgroundColor: colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 6,
    elevation: 8,
  },
});
