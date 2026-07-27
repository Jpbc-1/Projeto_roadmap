import React, { useState } from 'react';
import { View, Text, ScrollView, TouchableOpacity, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import NotebookBackground from '../components/NotebookBackground';
import RoadmapSketch, { SketchChapter } from '../components/RoadmapSketch';
import ReviewStack from '../components/ReviewStack';
import FlashcardReview, { Flashcard } from '../components/FlashcardReview';

type Roadmap = {
  key: string;
  title: string;
  tint: string;
  chapters: SketchChapter[];
};

const ROADMAPS: Roadmap[] = [
  {
    key: 'python',
    title: 'Python p/ Dados',
    tint: colors.postIt.yellow,
    chapters: [
      { title: 'Primeiros passos', status: 'completed' },
      { title: 'Estrutura de dados', status: 'completed' },
      { title: 'DataFrames', status: 'current' },
      { title: 'Limpeza de dados', status: 'locked' },
      { title: 'Visualização', status: 'locked' },
    ],
  },
  {
    key: 'sql',
    title: 'SQL',
    tint: colors.postIt.blue,
    chapters: [
      { title: 'Select básico', status: 'completed' },
      { title: 'Filtros', status: 'current' },
      { title: 'Joins', status: 'locked' },
      { title: 'Agregações', status: 'locked' },
    ],
  },
  {
    key: 'estatistica',
    title: 'Estatística',
    tint: colors.postIt.green,
    chapters: [
      { title: 'Medidas centrais', status: 'current' },
      { title: 'Dispersão', status: 'locked' },
      { title: 'Distribuições', status: 'locked' },
    ],
  },
];

const REVIEW_CARDS: Flashcard[] = [
  { question: 'O que é um DataFrame?', answer: 'Uma estrutura de dados em forma de tabela do pandas — linhas e colunas, como uma planilha.' },
  { question: 'Comando pra ver as 5 primeiras linhas', answer: 'df.head()' },
  { question: 'O que faz um INNER JOIN?', answer: 'Combina linhas de duas tabelas onde a condição de junção é verdadeira nas duas.' },
  { question: 'Mediana vs média: quando usar mediana?', answer: 'Quando há valores extremos (outliers) que distorceriam a média.' },
];

export default function ObjetivosScreen() {
  const [selectedRoadmap, setSelectedRoadmap] = useState(ROADMAPS[0].key);
  const [reviewing, setReviewing] = useState(false);

  const roadmap = ROADMAPS.find((r) => r.key === selectedRoadmap) ?? ROADMAPS[0];
  const completedCount = ROADMAPS.reduce(
    (sum, r) => sum + r.chapters.filter((c) => c.status === 'completed').length,
    0
  );

  return (
    <NotebookBackground>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Text style={styles.heading}>Seus Objetivos</Text>
        <Text style={styles.subheading}>Cada roadmap, desenhado como uma trilha no seu caderno</Text>

        <View style={styles.tabRow}>
          {ROADMAPS.map((r) => {
            const active = r.key === selectedRoadmap;
            return (
              <TouchableOpacity
                key={r.key}
                style={[styles.tab, { backgroundColor: active ? r.tint : 'transparent', borderColor: colors.graphite }]}
                onPress={() => setSelectedRoadmap(r.key)}
                accessibilityRole="tab"
                accessibilityState={{ selected: active }}
              >
                <Text style={[styles.tabText, active && styles.tabTextActive]} numberOfLines={1}>
                  {r.title}
                </Text>
              </TouchableOpacity>
            );
          })}
        </View>

        <View style={styles.sketchCard}>
          <RoadmapSketch chapters={roadmap.chapters} />
        </View>

        <View style={styles.tallyRow}>
          <Ionicons name="checkmark-done" size={16} color={colors.success} />
          <Text style={styles.tallyText}>{completedCount} capítulos concluídos ao todo</Text>
        </View>

        {reviewing ? (
          <FlashcardReview
            cards={REVIEW_CARDS}
            onClose={() => setReviewing(false)}
            onComplete={() => setReviewing(false)}
          />
        ) : (
          <ReviewStack pendingCount={REVIEW_CARDS.length} onStart={() => setReviewing(true)} />
        )}

        <TouchableOpacity style={styles.newGoalButton} accessibilityRole="button" accessibilityLabel="Novo objetivo">
          <Ionicons name="add" size={18} color={colors.textPrimary} />
          <Text style={styles.newGoalText}>Novo objetivo</Text>
        </TouchableOpacity>
      </ScrollView>
    </NotebookBackground>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  heading: {
    ...typography.screenTitle,
    color: colors.textPrimary,
  },
  subheading: {
    ...typography.body,
    fontSize: 14,
    color: colors.textSecondary,
    marginTop: spacing.sm,
    marginBottom: spacing.lg,
  },
  tabRow: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.sm,
  },
  tab: {
    minHeight: touchTarget,
    borderWidth: 1.5,
    borderRadius: radius.sm,
    paddingHorizontal: spacing.md,
    justifyContent: 'center',
  },
  tabText: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    color: colors.textSecondary,
  },
  tabTextActive: {
    color: colors.textPrimary,
  },
  sketchCard: {
    backgroundColor: colors.notebookPaper,
    borderRadius: radius.sm,
    paddingVertical: spacing.md,
  },
  tallyRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  tallyText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  newGoalButton: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    gap: spacing.sm,
    minHeight: touchTarget,
    marginTop: spacing.lg,
    borderRadius: radius.md,
    borderWidth: 1.5,
    borderColor: colors.graphite,
    borderStyle: 'dashed',
  },
  newGoalText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.textPrimary,
  },
});
