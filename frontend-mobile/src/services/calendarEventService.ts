import { api } from './api';

// Mirrors app/api/v1/schemas/notification_preferences.py (NotificationPreferenceFields)
// and app/api/v1/schemas/calendar_events.py on the backend. Keep these two
// in sync by hand — there's no shared codegen between the two repos yet.
export type NotificationTimingMode = 'app_default' | 'custom';
export type NotificationStyle = 'app_generated' | 'custom_message';

export type CalendarEvent = {
  id: number;
  title: string;
  description: string | null;
  start_datetime: string; // ISO 8601, e.g. "2026-07-27T11:00:00-03:00"
  end_datetime: string | null;
  is_all_day: boolean;
  notify_enabled: boolean;
  remind_before_minutes: number | null;
  notification_timing_mode: NotificationTimingMode;
  notification_style: NotificationStyle;
  custom_message: string | null;
};

export type CreateCalendarEventInput = {
  title: string;
  description?: string | null;
  start_datetime: string;
  end_datetime?: string | null;
  is_all_day?: boolean;
  notify_enabled?: boolean;
  remind_before_minutes?: number | null;
  notification_timing_mode?: NotificationTimingMode;
  notification_style?: NotificationStyle;
  custom_message?: string | null;
};

export type UpdateCalendarEventInput = Partial<CreateCalendarEventInput>;

export const calendarEventService = {
  // O back exige start/end no intervalo — usado pela timeline do dia e
  // pela tira de dias da semana (ver useAgenda.ts, que calcula esse
  // intervalo a partir do dia selecionado).
  listByRange: async (startIso: string, endIso: string): Promise<CalendarEvent[]> => {
    const response = await api.get('/calendar-events', {
      params: { start: startIso, end: endIso },
    });
    return response.data;
  },

  get: async (eventId: number): Promise<CalendarEvent> => {
    const response = await api.get(`/calendar-events/${eventId}`);
    return response.data;
  },

  create: async (input: CreateCalendarEventInput): Promise<CalendarEvent> => {
    const response = await api.post('/calendar-events', input);
    return response.data;
  },

  update: async (eventId: number, input: UpdateCalendarEventInput): Promise<CalendarEvent> => {
    const response = await api.put(`/calendar-events/${eventId}`, input);
    return response.data;
  },

  delete: async (eventId: number): Promise<void> => {
    await api.delete(`/calendar-events/${eventId}`);
  },
};
