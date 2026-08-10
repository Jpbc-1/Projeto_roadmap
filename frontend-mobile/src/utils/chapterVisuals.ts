import { Ionicons } from '@expo/vector-icons';

// O back não manda um ícone por capítulo (só title/status) — mas o mapa
// grafite e a página de detalhe do capítulo ficam mais fáceis de
// reconhecer de relance se cada capítulo tem um símbolo próprio, tipo um
// marco numa trilha de aventura. Em vez de inventar um campo novo na
// API, derivamos o ícone do próprio `chapter.id`: determinístico (o
// mesmo capítulo sempre pega o mesmo ícone, em qualquer tela), sem
// precisar guardar nada.
//
// Lista pensada como "pontos de uma jornada" (bandeira, bússola, mapa,
// luneta...) e não como o assunto do capítulo em si — não temos como
// saber se "Capítulo 3" é sobre Python ou sobre nutrição, então o ícone
// é só um marcador visual, nunca uma tentativa de ilustrar o conteúdo.
const WAYPOINT_ICONS: (keyof typeof Ionicons.glyphMap)[] = [
  'flag',
  'compass',
  'map',
  'telescope',
  'book',
  'bulb',
  'rocket',
  'trail-sign',
  'leaf',
  'footsteps',
  'diamond',
  'planet',
];

export function iconForChapter(chapterId: number): keyof typeof Ionicons.glyphMap {
  const index = ((chapterId % WAYPOINT_ICONS.length) + WAYPOINT_ICONS.length) % WAYPOINT_ICONS.length;
  return WAYPOINT_ICONS[index];
}
