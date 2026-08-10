import { useMemo } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { calendarEventService, CalendarEvent, CreateCalendarEventInput } from '../services/calendarEventService';
import { reminderService, Reminder, CreateReminderInput } from '../services/reminderService';
import { addDays, endOfDay, isSameDay, startOfDay, startOfWeek } from '../utils/dateUtils';

// A CalendarEvent and a Reminder render on the same timeline but aren't
// the same shape (a Reminder has no end time, ever). AgendaItem is the
// one shape every component downstream of this file actually works with,
// so WeekStrip/DayTimeline/UpcomingChip don't need to know about either
// backend model.
export type AgendaItem = {
  key: string; // `${kind}-${id}`, stable across refetches for list keys
  kind: 'calendar_event' | 'reminder';
  id: number;
  title: string;
  time: Date; // the specific occurrence being rendered, on the day being viewed
  durationMinutes: number | null; // null for reminders — they're a point, not a span
  raw: CalendarEvent | Reminder;
};

function calendarEventToItem(event: CalendarEvent): AgendaItem {
  const start = new Date(event.start_datetime);
  const durationMinutes = event.end_datetime
    ? Math.round((new Date(event.end_datetime).getTime() - start.getTime()) / 60000)
    : null;
  return {
    key: `calendar_event-${event.id}`,
    kind: 'calendar_event',
    id: event.id,
    title: event.title,
    time: start,
    durationMinutes,
    raw: event,
  };
}

/** A Reminder recurs every week on `days_of_week` — this projects it onto
 * one specific calendar day (`onDay`) so it can sit on the same timeline
 * as CalendarEvents for that day. */
function reminderToItemOnDay(reminder: Reminder, onDay: Date): AgendaItem {
  const [h, m] = reminder.time_of_day.split(':').map(Number);
  const time = new Date(onDay);
  time.setHours(h, m, 0, 0);
  return {
    key: `reminder-${reminder.id}`,
    kind: 'reminder',
    id: reminder.id,
    title: reminder.label,
    time,
    durationMinutes: null,
    raw: reminder,
  };
}

// ---------------------------------------------------------------------
// Queries
// ---------------------------------------------------------------------

/** All calendar events touching the week that contains `anchor` — one
 * fetch feeds both the WeekStrip's "does this day have anything" dots
 * and the selected day's timeline, instead of re-fetching per tap. */
export function useWeekCalendarEvents(anchor: Date) {
  const start = startOfWeek(anchor);
  const end = endOfDay(addDays(start, 6));
  return useQuery({
    queryKey: ['calendar-events', 'week', start.toISOString().slice(0, 10)],
    queryFn: () => calendarEventService.listByRange(start.toISOString(), end.toISOString()),
  });
}

/** Reminders don't have a date (they recur by weekday), so unlike
 * calendar events there's no range to fetch — the full active list is
 * small (a personal set of routines, not a growing log) and is filtered
 * client-side per day below. */
export function useReminders() {
  return useQuery({
    queryKey: ['reminders'],
    queryFn: () => reminderService.list(),
  });
}

export function useDayAgenda(selectedDay: Date) {
  const weekEvents = useWeekCalendarEvents(selectedDay);
  const reminders = useReminders();

  const items = useMemo(() => {
    const eventsToday = (weekEvents.data ?? [])
      .filter((e) => isSameDay(new Date(e.start_datetime), selectedDay))
      .map(calendarEventToItem);

    const weekday = selectedDay.getDay();
    const remindersToday = (reminders.data ?? [])
      .filter((r) => r.is_active && r.days_of_week.includes(weekday))
      .map((r) => reminderToItemOnDay(r, selectedDay));

    return [...eventsToday, ...remindersToday].sort((a, b) => a.time.getTime() - b.time.getTime());
  }, [weekEvents.data, reminders.data, selectedDay]);

  return {
    items,
    isLoading: weekEvents.isLoading || reminders.isLoading,
    isError: weekEvents.isError || reminders.isError,
  };
}

/** Feeds the dismissible chip row at the top of the screen — calendar
 * events only (see NewCompromissoModal notes: a Reminder recurring every
 * week doesn't read naturally as "lembrete · quinta", so chips stay
 * scoped to one-off compromissos/eventos, matching the reference). */
export function useUpcomingChips(daysAhead = 7) {
  const today = startOfDay(new Date());
  const end = endOfDay(addDays(today, daysAhead));
  const query = useQuery({
    queryKey: ['calendar-events', 'upcoming', today.toISOString().slice(0, 10)],
    queryFn: () => calendarEventService.listByRange(today.toISOString(), end.toISOString()),
  });

  const items = useMemo(() => {
    return (query.data ?? [])
      .filter((e) => !isSameDay(new Date(e.start_datetime), today)) // hoje já aparece na timeline principal
      .sort((a, b) => new Date(a.start_datetime).getTime() - new Date(b.start_datetime).getTime())
      .slice(0, 6)
      .map(calendarEventToItem);
  }, [query.data]);

  return { items, isLoading: query.isLoading };
}

// ---------------------------------------------------------------------
// Mutations
// ---------------------------------------------------------------------

// Both event/reminder creation invalidate the same set of query keys, so
// any screen watching the week, the reminders list, or the upcoming
// chips picks up the change on its next render — no manual cache
// patching, which is the usual source of "stale until you pull to
// refresh" bugs.
function useInvalidateAgenda() {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['calendar-events'] });
    queryClient.invalidateQueries({ queryKey: ['reminders'] });
  };
}

export function useCreateCalendarEvent() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: (input: CreateCalendarEventInput) => calendarEventService.create(input),
    onSuccess: invalidate,
  });
}

export function useCreateReminder() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: (input: CreateReminderInput) => reminderService.create(input),
    onSuccess: invalidate,
  });
}

export function useDeleteCalendarEvent() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: (eventId: number) => calendarEventService.delete(eventId),
    onSuccess: invalidate,
  });
}

export function useDeleteReminder() {
  const invalidate = useInvalidateAgenda();
  return useMutation({
    mutationFn: (reminderId: number) => reminderService.delete(reminderId),
    onSuccess: invalidate,
  });
}
