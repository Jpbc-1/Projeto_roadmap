// Small, dependency-free date helpers for the Agenda screen. Kept
// separate from the hooks/components so the date math (the part most
// likely to hide an off-by-one) is easy to find and easy to unit test on
// its own later.
//
// IMPORTANT — timezone note: this all works in the DEVICE's local time
// (new Date(), getDay(), setHours() all operate on local wall-clock time
// in RN). The backend's Reminder.time_of_day is stored per the user's
// saved timezone (see User.timezone), which may not match the device's
// current timezone 1:1 if the person travels. That mismatch already
// exists on the backend side (see the review notes on date.today());
// nothing here makes it worse, but it's not solved here either.

export const WEEKDAY_SHORT = ['D', 'S', 'T', 'Q', 'Q', 'S', 'S']; // 0=domingo
export const WEEKDAY_LONG = [
  'domingo',
  'segunda-feira',
  'terça-feira',
  'quarta-feira',
  'quinta-feira',
  'sexta-feira',
  'sábado',
];
const MONTH_NAMES = [
  'janeiro',
  'fevereiro',
  'março',
  'abril',
  'maio',
  'junho',
  'julho',
  'agosto',
  'setembro',
  'outubro',
  'novembro',
  'dezembro',
];

export function isSameDay(a: Date, b: Date): boolean {
  return a.getFullYear() === b.getFullYear() && a.getMonth() === b.getMonth() && a.getDate() === b.getDate();
}

export function startOfDay(date: Date): Date {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  return d;
}

export function endOfDay(date: Date): Date {
  const d = new Date(date);
  d.setHours(23, 59, 59, 999);
  return d;
}

export function addDays(date: Date, amount: number): Date {
  const d = new Date(date);
  d.setDate(d.getDate() + amount);
  return d;
}

/** Sunday that starts the week containing `date` — matches the backend's
 * 0=domingo convention for Reminder.days_of_week. */
export function startOfWeek(date: Date): Date {
  return addDays(startOfDay(date), -date.getDay());
}

export function weekDays(anchor: Date): Date[] {
  const start = startOfWeek(anchor);
  return Array.from({ length: 7 }, (_, i) => addDays(start, i));
}

/** "Bom dia" / "Boa tarde" / "Boa noite", read once when the screen mounts —
 * matches the greeting shown in the reference design. */
export function greetingForHour(hour: number): string {
  if (hour < 12) return 'Bom dia';
  if (hour < 18) return 'Boa tarde';
  return 'Boa noite';
}

export function formatLongDate(date: Date): string {
  const weekday = WEEKDAY_LONG[date.getDay()];
  const capitalized = weekday.charAt(0).toUpperCase() + weekday.slice(1);
  return `${capitalized} · ${date.getDate()} de ${MONTH_NAMES[date.getMonth()]}`;
}

export function formatMonthYear(date: Date): string {
  const month = MONTH_NAMES[date.getMonth()];
  return `${month.charAt(0).toUpperCase() + month.slice(1)} ${date.getFullYear()}`;
}

export function formatMonthShort(date: Date): string {
  return MONTH_NAMES[date.getMonth()].slice(0, 3);
}

/** "amanhã", "quinta", "12 de ago" — the label used on the upcoming-item
 * chips. Falls back to a short date once it's far enough away that a
 * weekday name alone would be ambiguous (see the 6-day cutoff below). */
export function relativeDayLabel(date: Date, today: Date = new Date()): string {
  const diffDays = Math.round((startOfDay(date).getTime() - startOfDay(today).getTime()) / 86400000);
  if (diffDays === 0) return 'hoje';
  if (diffDays === 1) return 'amanhã';
  if (diffDays > 1 && diffDays < 7) return WEEKDAY_LONG[date.getDay()].split('-')[0];
  return `${date.getDate()} de ${formatMonthShort(date)}`;
}

export function formatHM(date: Date): string {
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  return `${h}:${m}`;
}

/** "1h30" / "45min" — matches the compact duration format in the
 * reference cards ("11:00 · 1.5h" became "11:00 · 1h30" here, since that
 * reads better for non-round durations). */
export function formatDurationMinutes(minutes: number): string {
  if (minutes < 60) return `${minutes}min`;
  const h = Math.floor(minutes / 60);
  const m = minutes % 60;
  return m === 0 ? `${h}h` : `${h}h${String(m).padStart(2, '0')}`;
}

/** HH:MM:SS (backend's time_of_day shape) -> a Date on an arbitrary day,
 * for feeding into the native time picker / for HH:MM display. */
export function timeStringToDate(time: string): Date {
  const [h, m, s] = time.split(':').map(Number);
  const d = new Date();
  d.setHours(h ?? 0, m ?? 0, s ?? 0, 0);
  return d;
}

export function dateToTimeString(date: Date): string {
  const h = String(date.getHours()).padStart(2, '0');
  const m = String(date.getMinutes()).padStart(2, '0');
  return `${h}:${m}:00`;
}
