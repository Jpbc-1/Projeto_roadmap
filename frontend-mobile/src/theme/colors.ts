// Design tokens for the app.
//
// Visual identity: a warm corkboard/mural — wood background, cream cards
// pinned to it, warm accents. Color system still follows 5 named systems,
// each with one meaning, never reused, now in a warm palette instead of
// the earlier cool one:
//   Orange  -> Roadmap / planning / brand (buttons, active nav)
//   Gold    -> Nível / XP (level is XP made visible as a number)
//   Rust    -> Streak / consistency (a distinct hue from primary orange —
//              checked side by side so they never get confused)
//   Purple  -> Reviews / knowledge
//   Green   -> Troféus / achievement (chapters, roadmaps, objectives,
//              milestones, and the finish-mission button)
//
// Every foreground/background pair used for TEXT is >= 4.5:1 (WCAG AA).
// Every pair used only as an icon/graphic/fill is >= 3:1 (WCAG 1.4.11).
// Verified with a script, not eyeballed — ratios noted next to each token.
// Text directly on the wood background is its own check (wood is darker
// than the cream cards, so the same text color doesn't automatically
// carry over — see textOnWoodMuted).

export const colors = {
  // Roadmap / planning / brand. Paired with DARK text/icons, not white —
  // a brighter, more energetic orange reads better with dark-on-orange
  // than a muted orange would with white-on-orange (5.95:1 either way).
  primary: '#E8752E',
  primaryTint: '#FBE4D2',
  // A darker variant for when "this is primary/roadmap-related" needs to
  // show up as TEXT, a border, or an icon on a LIGHT background (a
  // selected chip, "today" on the calendar) instead of as a solid fill.
  // The bright `primary` above only clears contrast paired with dark
  // text ON it (5.95:1) — used as text/border ON cream or primaryTint
  // itself, it drops to ~2.7:1. This is the compliant alternative for
  // those spots (5.7–6.8:1 on both).
  primaryText: '#9C4712',

  // Nível / XP — level's number uses this; it's XP made legible, not a
  // separate system. 5.1:1 against its tint.
  xp: '#8A5900',
  xpTint: '#FBEBC7',

  // Streak / consistency. Split the same way as primary: a vibrant,
  // energetic red for the flame icon/fill/marker (3.3–4.7:1 — this is
  // the "grabs your attention" color you asked for), and a darker
  // version for whenever the streak count needs to render as actual
  // TEXT (6.1:1 on cream).
  streak: '#D63A08',
  streakText: '#A8330A',
  streakTint: '#FCE8DB',

  // Post-it pastels for "Suas outras missões" — purely decorative
  // variety (which card gets which color has no meaning), cycled
  // through per card like different colored notes on a board. Dark text
  // (textPrimary) holds 11.9–13.7:1 on all five; the dedicated
  // `textSecondaryOnPastel` below covers the lighter secondary text.
  postIt: {
    yellow: '#F5E1A0',
    blue: '#BEE0E8',
    pink: '#F3C9CE',
    green: '#C9E4C5',
    peach: '#F6D9B8',
  },
  textSecondaryOnPastel: '#5C4C3A', // 5.5–6.3:1 on every postIt color above — textSecondary itself dips to ~4.2 on pink, so this is the safe version for that surface specifically

  // Reviews / knowledge (spaced repetition) — 5.4:1 against its tint.
  reviews: '#7A2FD1',
  reviewsTint: '#EFE2FB',

  // Troféus / achievement — big milestones AND the finish-mission button
  // (a mission is a tiny achievement too). 4.7:1 on its tint, 4.9:1 as
  // text directly on a cream card (the bold "44%" style number).
  success: '#0F7A45',
  successTint: '#DFF3E6',

  // Neutral — for anything that isn't one of the 5 systems (time
  // estimate tags, disabled states). Icon-only use (4.2:1, clears the
  // 3:1 non-text minimum); never used for text.
  neutralIcon: '#7A6A57',
  neutralTint: '#F0E6D6',

  // Base — wood & parchment
  background: '#B8875C', // the board itself
  surface: '#FBF3E7', // cream cards pinned to it
  border: '#E8DCC8', // warm tan borders/progress-tracks on cream
  textPrimary: '#1F160C', // 16.2:1 on cream, 5.65:1 directly on wood — safe in both places
  textSecondary: '#6E5D4A', // 5.7:1 on cream — CREAM ONLY, drops to ~2:1 on wood, never use there
  textOnWoodMuted: '#33200E', // small labels sitting directly on wood (e.g. eyebrows) — 4.9:1
  textOnPrimary: '#1F160C', // text/icons on the orange button — same value as textPrimary, named for clarity at the call site
  iconOnDark: '#FFFFFF', // small icons sitting on a saturated fill that ISN'T primary (e.g. the streak marker on rust) — verified per use, not a general-purpose "white" token

  // --- Objetivos tab: notebook theme (separate material from the wood/cork Home) ---
  notebookPaper: '#FAF7F0',
  notebookRuleLine: '#C7D9EA', // faint ruled-paper lines — decorative texture, not information, so not contrast-checked the way text is
  notebookMarginLine: '#E08080', // the red margin line down the left side — same, purely decorative
  graphite: '#454545', // the "pencil sketch" roadmap path + node outlines — 8.9:1 on notebookPaper, safe even if used as text

  // Spaced-repetition rating buttons (Again / Difícil / Médio / Fácil) —
  // a genuinely distinct rating scale, not one of the 5 app-wide systems,
  // so it gets its own small verified set. All >=4.5:1 with white text.
  ratingAgain: '#C62828',
  ratingHard: '#9C580B',
  ratingMedium: '#4A5A78',
  ratingEasy: '#0F7A45', // same hex as `success` — mastering a review IS a small achievement, so reusing it here is intentional, not a new meaning
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

// Minimum touch target, per Android/iOS accessibility guidelines (>=44px).
// 48 satisfies that AND stays on the 8px grid.
export const touchTarget = 48;

// ---------------------------------------------------------------------
// Typography — exactly two type families.
//   display -> Space Grotesk: titles, section headers, mission names,
//              and every number that works as a "scoreboard" (level,
//              streak days, XP earned, trophy progress, chapter %).
//   body    -> Inter: everything meant to be read. 16px is the floor for
//              anything actually read start-to-finish; short scanned
//              labels (tags, nav labels, timestamps) can go smaller.
// Both must be loaded with useFonts() before the app renders — see
// App.tsx. Font names below match the @expo-google-fonts export names.
// ---------------------------------------------------------------------

export const fonts = {
  display: 'SpaceGrotesk_700Bold',
  displaySemiBold: 'SpaceGrotesk_600SemiBold',
  displayMedium: 'SpaceGrotesk_500Medium',
  body: 'Inter_400Regular',
  bodyMedium: 'Inter_500Medium',
  bodySemiBold: 'Inter_600SemiBold',
  bodyBold: 'Inter_700Bold',
} as const;

export const typography = {
  statNumberLarge: { fontFamily: fonts.display, fontSize: 32 },
  statNumber: { fontFamily: fonts.display, fontSize: 20 },

  greeting: { fontFamily: fonts.display, fontSize: 20 },
  screenTitle: { fontFamily: fonts.display, fontSize: 24 },
  sectionTitle: { fontFamily: fonts.display, fontSize: 18 },
  cardTitle: { fontFamily: fonts.displaySemiBold, fontSize: 15 },
  missionName: { fontFamily: fonts.display, fontSize: 22, lineHeight: 28 },

  body: { fontFamily: fonts.body, fontSize: 16, lineHeight: 22 },
  bodyMedium: { fontFamily: fonts.bodyMedium, fontSize: 16, lineHeight: 22 },

  caption: { fontFamily: fonts.bodyMedium, fontSize: 13 },
  eyebrow: { fontFamily: fonts.bodySemiBold, fontSize: 11, letterSpacing: 0.6 },
} as const;
