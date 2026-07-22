// Design tokens for the app.
//
// Rules this file enforces:
// 1) Each color = exactly one meaning, never reused for something else.
// 2) Every foreground/background pair actually used for text is >= 4.5:1
//    (WCAG AA, normal text). Every color used only as an icon/graphic/fill
//    is >= 3:1 (WCAG 1.4.11, non-text contrast). Verified with a script,
//    not eyeballed — see the ratios noted next to each token.
// 3) Spacing is a strict 8px scale — no value anywhere in the app that
//    isn't a multiple of 8.

export const colors = {
  // Brand / primary — navigation + the mission card's hero gradient.
  // White text/icons on primary or anywhere along the primary→primaryDark
  // gradient never drop below 5.3:1 (checked at both endpoints and 9
  // points in between).
  primary: '#6C4CF1',
  primaryDark: '#4C2FD9',

  // Functional accents — one job each, never reused for anything else.
  success: '#128049', // completion / positive action (mission button) — 4.99:1 with white text
  streak: '#D6540F', // streak / consistency — 3.5–4.1:1 in every context it's used (tint, track, marker)
  xp: '#B37200', // XP / rewards — 3.69:1 against its tint

  // Course/path category accents. These differentiate content categories,
  // not app-wide states — always paired with a distinct icon + text label
  // so meaning never depends on the color alone.
  courseBlue: '#2E6FE0', // 4.0–4.2:1 against its tint and track
  courseTeal: '#0A7F72', // 4.2–4.6:1 against its tint and track

  // Level and badge count are profile stats, not core mechanics — kept
  // deliberately neutral instead of taking on their own accent color, so
  // the four accent colors above stay unambiguous.
  neutralIcon: '#4B5563', // 6.7–7.6:1 on white/neutralTint
  neutralTint: '#F1F1F5',

  // Tints — light backgrounds paired 1:1 with the accents above
  streakTint: '#FFF1E7',
  xpTint: '#FFF7E3',
  courseBlueTint: '#EAF2FF',
  courseTealTint: '#E6FBF8',

  // Neutrals
  background: '#F7F7FB',
  surface: '#FFFFFF',
  border: '#ECECF3',
  textPrimary: '#1A1A2E', // 16–17:1 on background/surface
  textSecondary: '#6B6B80', // 4.9–5.2:1 on background/surface
  textOnPrimary: '#FFFFFF', // the ONLY text/icon color on the gradient card

  // Decorative-only overlay (e.g. an unfilled progress track sitting on
  // the gradient). Never used for text or for anything conveying meaning
  // on its own — always paired with an explicit numeric label.
  overlayOnPrimary: 'rgba(255,255,255,0.28)',
} as const;

// Strict 8px grid. Every padding/margin/gap in every component pulls one
// of these four values — nothing in between.
export const spacing = {
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
} as const;

export const radius = {
  sm: 8,
  md: 16,
  lg: 24,
  pill: 999,
} as const;

export const typography = {
  greeting: { fontSize: 20, fontWeight: '700' as const },
  h1: { fontSize: 22, fontWeight: '800' as const },
  h2: { fontSize: 16, fontWeight: '700' as const },
  body: { fontSize: 14, fontWeight: '400' as const },
  caption: { fontSize: 12, fontWeight: '500' as const },
  eyebrow: { fontSize: 11, fontWeight: '700' as const, letterSpacing: 0.6 },
} as const;

// Minimum touch target, per Android/iOS accessibility guidelines (>=44px).
// 48 satisfies that AND stays on the 8px grid.
export const touchTarget = 48;