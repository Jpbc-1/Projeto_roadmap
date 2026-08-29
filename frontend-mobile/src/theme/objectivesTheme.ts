// Paleta "papel/grafite" própria da tela de Objetivos.
// Deliberadamente separada de `theme/colors.ts`: essa tela usa uma
// linguagem visual (papel + trilha desenhada à mão) diferente do resto
// do app. Se preferirem, dá pra mesclar com o tema global depois.

export const paper = {
  base: '#F1E8D2',
  dark: '#E4D7B3',
  deep: '#D9CAA1',
  cream: '#FAF5E6',
};

export const ink = {
  base: '#3B372C',
  soft: '#6B6553',
};

export const accent = {
  green: '#55744D',
  greenDeep: '#3D5637',
  amber: '#C9813D',
  amberDeep: '#A3612A',
  grey: '#A89E89',
  greyLine: '#C7BC9E',
  red: '#B1483A',
};

// As fontes "handwritten" do mockup (Kalam / Patrick Hand) não estão
// instaladas no projeto. Usei o que já existe:
// - Caveat cobre bem os títulos com jeito de escrita à mão.
// - Inter cobre o corpo de texto (mais legível em telas pequenas).
// Se quiserem o visual de "Patrick Hand" (corpo também manuscrito), dá pra
// `expo install @expo-google-fonts/patrick-hand` e trocar `fonts.body`.
export const fonts = {
  hand: 'Caveat_700Bold',
  handSemi: 'Caveat_600SemiBold',
  body: 'Inter_400Regular',
  bodyMedium: 'Inter_500Medium',
  bodyBold: 'Inter_700Bold',
};
