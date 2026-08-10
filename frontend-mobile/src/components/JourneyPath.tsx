import React, { useEffect, useMemo, useRef } from 'react';
import { Animated, Easing, StyleSheet, Text, TouchableOpacity, View } from 'react-native';
import Svg, { Circle, Defs, LinearGradient, Path, Stop } from 'react-native-svg';
// Mesmo nome, dois pacotes diferentes: o de cima é a definição de
// gradiente do SVG (só existe dentro de <Defs>, usada via fill="url(#)");
// este aqui é a versão que renderiza de verdade como uma View — mesma
// lib que WoodBackground já usa pro grão de madeira.
import { LinearGradient as ViewGradient } from 'expo-linear-gradient';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import { ChapterProgress } from '../services/roadmapService';
import { iconForChapter } from '../utils/chapterVisuals';
import {
  JourneyMapModel,
  PositionedNode,
  VIEW_W,
  buildJourneyMapModel,
  journeyCanvasHeight,
  layoutJourneyNodes,
  smoothPathD,
} from '../utils/journeyMapLayout';

type JourneyPathProps = {
  chapters: ChapterProgress[];
  /** Uma das cores de colors.postIt, escolhida por objetivo (ver ObjetivosScreen)
   * — dá ao capítulo atual (e ao brilho por trás dele) a mesma identidade de
   * cor do marcador daquele caderno lá em cima. */
  accentTint: string;
  onSelectChapter: (chapterId: number) => void;
};

const LABEL_WIDTH = 124;

// react-native-svg suporta animar props numéricas de elementos SVG
// (r, opacity, strokeDashoffset) via Animated.createAnimatedComponent —
// não precisa do Reanimated pra isso, e é o mesmo `Animated` que
// PushPin/WashiTape já usam no resto do app.
const AnimatedCircle = Animated.createAnimatedComponent(Circle);

export default function JourneyPath({ chapters, accentTint, onSelectChapter }: JourneyPathProps) {
  const model = useMemo(() => buildJourneyMapModel(chapters), [chapters]);
  const positioned = useMemo(() => layoutJourneyNodes(model.nodes), [model.nodes]);
  const canvasHeight = useMemo(() => journeyCanvasHeight(model.nodes.length), [model.nodes.length]);

  const currentNode = positioned.find((n) => n.kind === 'current') ?? null;
  const currentChapter = currentNode?.chapter ?? null;
  const currentDone = currentChapter?.missions.filter((m) => m.completed).length ?? 0;
  const currentTotal = currentChapter?.missions.length ?? 0;
  const currentProgress = currentTotal > 0 ? currentDone / currentTotal : 0;

  // Separa o traço em dois trechos: sólido do começo até onde a pessoa
  // já pisou (concluídos + atual), tracejado dali pra frente (bloqueados
  // + neblina). "Caminho andado" vs "caminho ainda sendo desenhado",
  // direto do documento de visão.
  const walkedUntil = useMemo(() => {
    const currentIdx = positioned.findIndex((n) => n.kind === 'current' || n.kind === 'trophy');
    if (currentIdx >= 0) return currentIdx;
    let lastDone = -1;
    positioned.forEach((n, i) => {
      if (n.kind === 'done') lastDone = i;
    });
    return lastDone;
  }, [positioned]);

  const walkedD = useMemo(
    () => smoothPathD(positioned.slice(0, walkedUntil + 1).map((n) => ({ x: n.x, y: n.y }))),
    [positioned, walkedUntil]
  );
  const aheadD = useMemo(
    () => smoothPathD(positioned.slice(Math.max(walkedUntil, 0)).map((n) => ({ x: n.x, y: n.y }))),
    [positioned, walkedUntil]
  );

  const fogNode = positioned.find((n) => n.kind === 'fog') ?? null;

  if (chapters.length === 0) {
    return (
      <View style={styles.panel}>
        <View style={styles.emptyWrap}>
          <Ionicons name="hourglass-outline" size={20} color={colors.neutralIcon} />
          <Text style={styles.emptyText}>Sua jornada ainda está sendo desenhada pela IA...</Text>
        </View>
      </View>
    );
  }

  return (
    <View style={styles.panel}>
      <ViewGradient
        pointerEvents="none"
        colors={['rgba(31,22,12,0.07)', 'rgba(31,22,12,0)']}
        style={styles.insetShadow}
      />
      {model.olderCount > 0 && (
        <Text style={styles.olderSummary}>
          +{model.olderCount} capítulo{model.olderCount > 1 ? 's' : ''} mais atrás no seu caderno
        </Text>
      )}

      <View style={[styles.canvasWrap, { aspectRatio: VIEW_W / canvasHeight }]}>
        <Svg width="100%" height="100%" viewBox={`0 0 ${VIEW_W} ${canvasHeight}`} style={StyleSheet.absoluteFill}>
          <Defs>
            <LinearGradient id="fogFade" x1="0" y1="1" x2="0" y2="0">
              <Stop offset="0" stopColor={colors.notebookPaper} stopOpacity={0} />
              <Stop offset="0.55" stopColor={colors.notebookPaper} stopOpacity={0.6} />
              <Stop offset="1" stopColor={colors.notebookPaper} stopOpacity={0.96} />
            </LinearGradient>
          </Defs>

          <MapBackdrop canvasHeight={canvasHeight} fogNode={fogNode} />

          {walkedUntil >= 0 && (
            <>
              <Path d={walkedD} stroke={colors.graphite} strokeWidth={2.6} fill="none" strokeLinecap="round" opacity={0.16} />
              <Path d={walkedD} stroke={colors.graphite} strokeWidth={1.7} fill="none" strokeLinecap="round" opacity={0.55} />
            </>
          )}
          {aheadD !== '' && (
            <Path
              d={aheadD}
              stroke={colors.neutralIcon}
              strokeWidth={1.4}
              fill="none"
              strokeLinecap="round"
              strokeDasharray="1 7"
              opacity={0.45}
            />
          )}

          {positioned.map((node) =>
            node.kind === 'current' ? (
              <CurrentNodeArt key={node.key} node={node} accentTint={accentTint} progress={currentProgress} />
            ) : (
              <StaticNodeArt key={node.key} node={node} />
            )
          )}

          {fogNode && (
            <Path
              d={`M 0 0 L ${VIEW_W} 0 L ${VIEW_W} ${Math.min(canvasHeight, fogNode.y + 90)} L 0 ${Math.min(canvasHeight, fogNode.y + 90)} Z`}
              fill="url(#fogFade)"
            />
          )}
        </Svg>

        <View style={StyleSheet.absoluteFill} pointerEvents="box-none">
          {positioned.map((node) => (
            <MapNodeOverlay
              key={node.key}
              node={node}
              canvasHeight={canvasHeight}
              title={titleForNode(node)}
              subtitle={subtitleForNode(node, model, currentProgress)}
              onSelectChapter={onSelectChapter}
            />
          ))}
        </View>
      </View>
    </View>
  );
}

// ─── arte de fundo (bem minimalista, de propósito) ────────────────────

function MapBackdrop({ canvasHeight, fogNode }: { canvasHeight: number; fogNode: PositionedNode | null }) {
  const hillY = canvasHeight - 30;
  return (
    <>
      <Path
        d={`M 0 ${hillY} Q ${VIEW_W * 0.26} ${hillY - 30} ${VIEW_W * 0.52} ${hillY - 6} T ${VIEW_W} ${hillY - 18} L ${VIEW_W} ${canvasHeight} L 0 ${canvasHeight} Z`}
        fill={colors.graphite}
        opacity={0.045}
      />
      {fogNode &&
        [-0.55, 0.32, -0.12, 0.6].map((dx, i) => (
          <Circle key={i} cx={fogNode.x + dx * 74} cy={Math.max(fogNode.y - 26 - i * 11, 10)} r={1.3} fill={colors.xp} opacity={0.22} />
        ))}
    </>
  );
}

// ─── nó atual: o único animado (brilho pulsando + preenchimento de cor
// crescendo com o progresso + anel de progresso) ───────────────────────

function CurrentNodeArt({ node, accentTint, progress }: { node: PositionedNode; accentTint: string; progress: number }) {
  return (
    <>
      <GlowPulse cx={node.x} cy={node.y} baseR={node.r} color={accentTint} />
      <Circle cx={node.x} cy={node.y} r={node.r} fill={colors.notebookPaper} stroke={colors.graphite} strokeWidth={1.4} strokeDasharray="3 3" opacity={0.5} />
      <ColorFill cx={node.x} cy={node.y} r={node.r - 3} color={accentTint} progress={progress} />
      <ProgressRing cx={node.x} cy={node.y} r={node.r + 6} progress={progress} color={colors.primary} />
    </>
  );
}

function GlowPulse({ cx, cy, baseR, color }: { cx: number; cy: number; baseR: number; color: string }) {
  const pulse = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    const loop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulse, { toValue: 1, duration: 1700, easing: Easing.inOut(Easing.sin), useNativeDriver: false }),
        Animated.timing(pulse, { toValue: 0, duration: 1700, easing: Easing.inOut(Easing.sin), useNativeDriver: false }),
      ])
    );
    loop.start();
    return () => loop.stop();
  }, [pulse]);

  // useNativeDriver: false porque isso anima `r`/`opacity` de um <Circle>
  // do SVG, não transform/opacity de uma View comum -- o driver nativo
  // não alcança essas props. Só 1 elemento pulsando devagar, então rodar
  // na thread de JS não pesa.
  const r = pulse.interpolate({ inputRange: [0, 1], outputRange: [baseR * 1.26, baseR * 1.48] });
  const opacity = pulse.interpolate({ inputRange: [0, 1], outputRange: [0.3, 0.13] });

  return <AnimatedCircle cx={cx} cy={cy} r={r} fill={color} opacity={opacity} />;
}

function ColorFill({ cx, cy, r, color, progress }: { cx: number; cy: number; r: number; color: string; progress: number }) {
  const animated = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animated, { toValue: progress, duration: 650, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
  }, [progress, animated]);

  // "Conforme o usuário avança, o desenho ganha mais cor" -- em 0% o nó
  // ainda lê como esboço (opacidade baixa, não zero: precisa continuar
  // reconhecível como "capítulo atual" mesmo antes da 1ª missão); em
  // 100% fica totalmente colorido.
  const opacity = animated.interpolate({ inputRange: [0, 1], outputRange: [0.14, 0.88] });

  return <AnimatedCircle cx={cx} cy={cy} r={r} fill={color} opacity={opacity} />;
}

function ProgressRing({ cx, cy, r, progress, color }: { cx: number; cy: number; r: number; progress: number; color: string }) {
  const animated = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    Animated.timing(animated, { toValue: progress, duration: 650, easing: Easing.out(Easing.cubic), useNativeDriver: false }).start();
  }, [progress, animated]);

  const circumference = 2 * Math.PI * r;
  const strokeDashoffset = animated.interpolate({ inputRange: [0, 1], outputRange: [circumference, 0] });

  return (
    <AnimatedCircle
      cx={cx}
      cy={cy}
      r={r}
      stroke={color}
      strokeWidth={3}
      fill="none"
      strokeLinecap="round"
      opacity={0.7}
      strokeDasharray={`${circumference} ${circumference}`}
      strokeDashoffset={strokeDashoffset}
      transform={`rotate(-90 ${cx} ${cy})`}
    />
  );
}

// ─── demais nós: estáticos, sem custo de animação ─────────────────────

function StaticNodeArt({ node }: { node: PositionedNode }) {
  if (node.kind === 'done') {
    return <Circle cx={node.x} cy={node.y} r={node.r} fill={colors.successTint} stroke={colors.success} strokeWidth={2} />;
  }
  if (node.kind === 'trophy') {
    return <Circle cx={node.x} cy={node.y} r={node.r} fill={colors.successTint} stroke={colors.success} strokeWidth={2.4} />;
  }
  if (node.kind === 'locked') {
    return (
      <Circle
        cx={node.x}
        cy={node.y}
        r={node.r}
        fill={colors.neutralTint}
        stroke={colors.neutralIcon}
        strokeWidth={1.4}
        strokeDasharray="3 4"
        opacity={0.85}
      />
    );
  }
  // fog
  return (
    <Circle cx={node.x} cy={node.y} r={node.r} fill={colors.notebookPaper} stroke={colors.neutralIcon} strokeWidth={1.2} strokeDasharray="2 5" opacity={0.4} />
  );
}

// ─── camada de toque + texto (View comum, não SVG -- fontes custom e
// acessibilidade funcionam de graça assim; ver histórico de
// RoadmapSketch pro mesmo raciocínio) ──────────────────────────────────

function titleForNode(node: PositionedNode): string {
  if (node.chapter) return node.chapter.title;
  return node.kind === 'fog' ? 'terra incógnita' : 'Jornada concluída!';
}

function subtitleForNode(node: PositionedNode, model: JourneyMapModel, currentProgress: number): string | null {
  if (node.kind === 'current') return `${Math.round(currentProgress * 100)}% do capítulo`;
  if (node.kind === 'fog') {
    return model.beyondCount > 0
      ? `a IA está desenhando (e mais ${model.beyondCount} depois)...`
      : 'a IA ainda está desenhando...';
  }
  if (node.kind === 'trophy') return 'bom trabalho 🎉';
  return null;
}

function accessibilityLabelFor(node: PositionedNode, title: string, subtitle: string | null): string {
  if (node.kind === 'done') return `Capítulo concluído: ${title}`;
  if (node.kind === 'current') return `Capítulo atual: ${title}${subtitle ? `, ${subtitle}` : ''}`;
  return `Capítulo bloqueado: ${title}`;
}

function MapNodeOverlay({
  node,
  canvasHeight,
  title,
  subtitle,
  onSelectChapter,
}: {
  node: PositionedNode;
  canvasHeight: number;
  title: string;
  subtitle: string | null;
  onSelectChapter: (chapterId: number) => void;
}) {
  const leftPct = (node.x / VIEW_W) * 100;
  const topPct = (node.y / canvasHeight) * 100;
  const touchSize = Math.max(node.r * 2, touchTarget);
  const isInteractive = node.kind === 'done' || node.kind === 'current' || node.kind === 'locked';
  const icon = node.chapter ? iconForChapter(node.chapter.id) : node.kind === 'fog' ? 'help' : 'trophy';

  const iconColor =
    node.kind === 'done'
      ? colors.success
      : node.kind === 'current'
        ? colors.primaryText
        : node.kind === 'trophy'
          ? colors.xp
          : colors.neutralIcon;

  const labelColor =
    node.kind === 'done'
      ? colors.success
      : node.kind === 'current'
        ? colors.primaryText
        : node.kind === 'trophy'
          ? colors.success
          : colors.textSecondary;

  const wrapOpacity = node.kind === 'locked' ? 0.85 : node.kind === 'fog' ? 0.55 : 1;

  const inner = (
    <>
      <View style={[styles.nodeTouchArea, { width: touchSize, height: touchSize, marginLeft: -touchSize / 2, marginTop: -touchSize / 2 }]}>
        <Ionicons name={icon} size={node.r * 0.7} color={iconColor} />
        {node.kind === 'done' && (
          <View style={styles.stampBadge}>
            <Ionicons name="checkmark" size={11} color={colors.surface} />
          </View>
        )}
      </View>

      <View style={[styles.nodeLabel, { marginLeft: -LABEL_WIDTH / 2, marginTop: node.r + spacing.sm }]}>
        {node.kind === 'current' && (
          <View style={styles.nowPill}>
            <Text style={styles.nowPillText}>agora</Text>
          </View>
        )}
        <Text style={[styles.nodeTitle, { color: labelColor }]} numberOfLines={2}>
          {title}
        </Text>
        {subtitle && (
          <Text style={[styles.nodeSubtitle, node.kind === 'fog' && styles.nodeSubtitleItalic]} numberOfLines={2}>
            {subtitle}
          </Text>
        )}
      </View>
    </>
  );

  return (
    <View style={[styles.nodeAnchor, { left: `${leftPct}%`, top: `${topPct}%`, opacity: wrapOpacity }]} pointerEvents="box-none">
      {isInteractive ? (
        <TouchableOpacity
          activeOpacity={0.75}
          onPress={() => node.chapter && onSelectChapter(node.chapter.id)}
          accessibilityRole="button"
          accessibilityLabel={accessibilityLabelFor(node, title, subtitle)}
        >
          {inner}
        </TouchableOpacity>
      ) : (
        <View>{inner}</View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  panel: {
    marginTop: spacing.sm,
    backgroundColor: colors.notebookPaper,
    borderRadius: radius.md,
    borderWidth: 1,
    borderColor: 'rgba(69,69,69,0.12)', // colors.graphite em baixa opacidade -- só textura, não texto, não precisa do teste de contraste
    paddingTop: spacing.sm,
    paddingBottom: spacing.md,
    paddingHorizontal: spacing.sm,
    overflow: 'hidden',
  },
  insetShadow: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 10,
    // Sombra "encaixada" no topo do painel -- sugere que o mapa está
    // ligeiramente afundado na página, sem precisar de inset box-shadow
    // (que o RN não suporta nativamente).
  },
  olderSummary: {
    ...typography.caption,
    fontSize: 11,
    color: colors.textSecondary,
    textAlign: 'center',
    marginBottom: spacing.sm,
  },
  canvasWrap: {
    width: '100%',
  },
  emptyWrap: {
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    paddingVertical: spacing.xl,
  },
  emptyText: {
    ...typography.caption,
    fontSize: 13,
    fontStyle: 'italic',
    color: colors.textSecondary,
    textAlign: 'center',
    paddingHorizontal: spacing.lg,
  },
  nodeAnchor: {
    position: 'absolute',
  },
  nodeTouchArea: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  stampBadge: {
    position: 'absolute',
    top: -2,
    right: -2,
    width: 18,
    height: 18,
    borderRadius: 9,
    backgroundColor: colors.success,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: colors.notebookPaper,
    transform: [{ rotate: '-10deg' }],
  },
  nodeLabel: {
    position: 'absolute',
    width: LABEL_WIDTH,
    alignItems: 'center',
  },
  nowPill: {
    backgroundColor: colors.primary,
    borderRadius: radius.pill,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    marginBottom: 3,
  },
  nowPillText: {
    ...typography.eyebrow,
    fontSize: 9,
    color: colors.textOnPrimary,
  },
  nodeTitle: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
    textAlign: 'center',
  },
  nodeSubtitle: {
    ...typography.caption,
    fontSize: 10,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: 1,
  },
  nodeSubtitleItalic: {
    fontStyle: 'italic',
  },
});
