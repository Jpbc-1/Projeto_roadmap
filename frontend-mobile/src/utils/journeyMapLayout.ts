import { ChapterProgress } from '../services/roadmapService';

// ─── modelo ──────────────────────────────────────────────────────────
//
// O back só conhece 3 estados de capítulo (locked/in_progress/completed)
// — "fog" (neblina, capítulo que a IA ainda nem desenhou) e "trophy"
// (jornada inteira concluída) não existem como status; são inferidos
// aqui, puramente visuais. Um roadmap de verdade pode ter dezenas de
// capítulos ao longo do tempo, mas o documento de visão é explícito:
// "a IA gera só alguns capítulos por vez" — então o mapa mostra uma
// JANELA (histórico recente + atual + próximos + neblina), não a lista
// inteira. Histórico mais antigo vira um resumo em texto (ver
// `olderCount`), não nós extras competindo por espaço com o capítulo
// atual, que é o real protagonista da tela.

export type MapNodeKind = 'done' | 'current' | 'locked' | 'fog' | 'trophy';

export type MapNode = {
  key: string;
  kind: MapNodeKind;
  /** null para os nós sintéticos (fog/trophy) — não existe capítulo por trás deles */
  chapter: ChapterProgress | null;
};

export type PositionedNode = MapNode & {
  x: number;
  y: number;
  r: number;
};

export type JourneyMapModel = {
  nodes: MapNode[];
  /** capítulos concluídos que existem mas ficaram de fora da janela visível */
  olderCount: number;
  /** capítulos bloqueados que existem mas ficaram de fora da janela visível */
  beyondCount: number;
  /** não sobrou nenhum capítulo atual/bloqueado — a jornada deste roadmap acabou */
  journeyComplete: boolean;
};

const HISTORY_VISIBLE = 2;
const UPCOMING_VISIBLE = 2;

export function buildJourneyMapModel(chapters: ChapterProgress[]): JourneyMapModel {
  const completed = chapters.filter((c) => c.status === 'completed').sort((a, b) => a.order_index - b.order_index);
  const current = chapters.find((c) => c.status === 'in_progress') ?? null;
  const locked = chapters.filter((c) => c.status === 'locked').sort((a, b) => a.order_index - b.order_index);

  const historyVisible = completed.slice(-HISTORY_VISIBLE);
  const olderCount = completed.length - historyVisible.length;
  const upcomingVisible = locked.slice(0, UPCOMING_VISIBLE);
  const beyondCount = locked.length - upcomingVisible.length;

  // Igual à lógica que já existia (ver git blame de JourneyPath): sem
  // capítulo atual e sem nada bloqueado, mas com pelo menos 1 concluído,
  // é o sinal disponível mais confiável de "acabou" que os dados dão —
  // não existe um campo `is_complete` explícito no roadmap.
  const journeyComplete = !current && locked.length === 0 && completed.length > 0;

  const nodes: MapNode[] = [
    ...historyVisible.map((c): MapNode => ({ key: `done-${c.id}`, kind: 'done', chapter: c })),
    ...(current ? [{ key: `current-${current.id}`, kind: 'current' as const, chapter: current }] : []),
    ...upcomingVisible.map((c): MapNode => ({ key: `locked-${c.id}`, kind: 'locked', chapter: c })),
  ];

  if (journeyComplete) {
    nodes.push({ key: 'trophy', kind: 'trophy', chapter: null });
  } else if (chapters.length > 0) {
    // "O roadmap nunca é totalmente fixo" — enquanto a jornada não
    // termina, sempre existe mais trilha sendo desenhada lá na frente,
    // mesmo que o back ainda não tenha gerado esses capítulos.
    nodes.push({ key: 'fog', kind: 'fog', chapter: null });
  }

  return { nodes, olderCount, beyondCount, journeyComplete };
}

// ─── posicionamento ──────────────────────────────────────────────────
//
// Trilha sinuosa, não uma lista reta — index 0 (mais antigo/concluído)
// embaixo, subindo até o nó mais recente no topo (mesma metáfora de
// "escalada" da referência). O capítulo atual (ou o troféu, se a
// jornada acabou) é a âncora: o zigue-zague alterna dos dois lados dele,
// crescendo levemente conforme se afasta, então a trilha nunca corre
// pra fora da tela mesmo com mais nós.

export const VIEW_W = 320;
const CENTER_X = VIEW_W / 2;
// V_SPACING/BOTTOM_PAD calculados pro pior caso de rótulo, não pro
// médio: o nó "current" é o maior (r=36) E tem o bloco de texto mais
// alto (selo "agora" + título de até 2 linhas + subtítulo) — e ele
// pode muito bem ser o nó mais de baixo do mapa (objetivo criado na
// hora, zero capítulos concluídos ainda, é literalmente o estado
// inicial de todo objetivo nesse app). Sem folga generosa aqui, esse
// exato caso comum ficaria com o rótulo cortado embaixo do canvas ou
// encostando no nó vizinho.
const V_SPACING = 150;
const TOP_PAD = 60;
const BOTTOM_PAD = 120;
const AMPLITUDE = 48;

const RADIUS_BY_KIND: Record<MapNodeKind, number> = {
  done: 25,
  current: 36,
  locked: 22,
  fog: 18,
  trophy: 32,
};

export function layoutJourneyNodes(nodes: MapNode[]): PositionedNode[] {
  const anchorIndex = Math.max(
    nodes.findIndex((n) => n.kind === 'current' || n.kind === 'trophy'),
    0
  );

  return nodes.map((node, i) => {
    const rel = i - anchorIndex;
    const side = rel === 0 ? 0 : rel % 2 === 0 ? 1 : -1;
    const magnitude = Math.min(Math.abs(rel), 3);
    const x = CENTER_X + side * AMPLITUDE * (0.35 + magnitude * 0.22);
    const y = TOP_PAD + (nodes.length - 1 - i) * V_SPACING;

    const baseR = RADIUS_BY_KIND[node.kind];
    const taper = node.kind === 'done' || node.kind === 'locked' ? Math.min(Math.abs(rel) * 1.5, 6) : 0;

    return { ...node, x, y, r: Math.max(baseR - taper, 14) };
  });
}

export function journeyCanvasHeight(nodeCount: number): number {
  return TOP_PAD + BOTTOM_PAD + Math.max(nodeCount - 1, 0) * V_SPACING;
}

// ─── traço suave ─────────────────────────────────────────────────────
//
// Catmull-Rom convertido pra série de Béziers cúbicas (fator padrão
// 1/6) — curva suave passando por TODOS os pontos, não só uma
// aproximação entre eles. Suporta qualquer quantidade de pontos (0, 1
// ou N), já que a janela visível muda de tamanho dependendo de quantos
// capítulos existem.
export function smoothPathD(points: { x: number; y: number }[]): string {
  if (points.length === 0) return '';
  if (points.length === 1) return `M ${points[0].x} ${points[0].y}`;

  let d = `M ${points[0].x} ${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i === 0 ? 0 : i - 1];
    const p1 = points[i];
    const p2 = points[i + 1];
    const p3 = points[i + 2 < points.length ? i + 2 : i + 1];
    const c1x = p1.x + (p2.x - p0.x) / 6;
    const c1y = p1.y + (p2.y - p0.y) / 6;
    const c2x = p2.x - (p3.x - p1.x) / 6;
    const c2y = p2.y - (p3.y - p1.y) / 6;
    d += ` C ${c1x} ${c1y} ${c2x} ${c2y} ${p2.x} ${p2.y}`;
  }
  return d;
}
