import { api } from './api';
import type { NotificationStyle, NotificationTimingMode } from './calendarEventService';

// Mirrors app/api/v1/schemas/reminders.py on the backend.
export type Reminder = {
  id: number;
  label: string;
  time_of_day: string; // "HH:MM:SS", fuso do usuário (ver User.timezone no back)
  days_of_week: number[]; // 0=domingo ... 6=sábado
  is_active: boolean;
  notification_timing_mode: NotificationTimingMode;
  notification_style: NotificationStyle;
  custom_message: string | null;
};

export type CreateReminderInput = {
  label: string;
  time_of_day?: string | null;
  days_of_week?: number[] | null;
  notification_timing_mode?: NotificationTimingMode;
  notification_style?: NotificationStyle;
  custom_message?: string | null;
};

export type UpdateReminderInput = Partial<CreateReminderInput>;

// ATENÇÃO: os caminhos abaixo seguem o mesmo padrão REST de
// app/api/v1/endpoints/calendar_events.py (que eu revisei linha a linha),
// mas eu não tinha o conteúdo exato de endpoints/reminders.py na mão —
// só os use cases (ListReminders, GetReminder, CreateReminder,
// UpdateReminder, DeleteReminder, ToggleReminder) e o repositório. Se as
// rotas reais do seu reminders.py tiverem nomes diferentes — em especial
// o toggle, que não tem um verbo REST óbvio — é só ajustar as strings
// abaixo, o resto do app não muda.
export const reminderService = {
  list: async (): Promise<Reminder[]> => {
    const response = await api.get('/reminders');
    return response.data;
  },

  get: async (reminderId: number): Promise<Reminder> => {
    const response = await api.get(`/reminders/${reminderId}`);
    return response.data;
  },

  create: async (input: CreateReminderInput): Promise<Reminder> => {
    const response = await api.post('/reminders', input);
    return response.data;
  },

  update: async (reminderId: number, input: UpdateReminderInput): Promise<Reminder> => {
    const response = await api.put(`/reminders/${reminderId}`, input);
    return response.data;
  },

  toggle: async (reminderId: number, isActive: boolean): Promise<Reminder> => {
    const response = await api.patch(`/reminders/${reminderId}/toggle`, { is_active: isActive });
    return response.data;
  },

  delete: async (reminderId: number): Promise<void> => {
    await api.delete(`/reminders/${reminderId}`);
  },
};
