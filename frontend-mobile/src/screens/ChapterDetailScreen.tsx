import React, { useEffect, useRef, useState } from 'react';
import { Alert, Animated, Text, TextInput, TouchableOpacity, View, ScrollView, StyleSheet } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { colors, spacing, radius, typography, fonts, touchTarget } from '../theme/colors';
import NotebookBackground from '../components/NotebookBackground';
import CelebrationBurst from '../components/CelebrationBurst';
import { iconForChapter } from '../utils/chapterVisuals';
import { ChapterProgress, MissionProgress } from '../services/roadmapService';
import { useCompleteMission, useCreateMission, useDeleteMission, useUpdateMission } from '../hooks/useObjetivos';

type ChapterDetailScreenProps = {
  chapter: ChapterProgress;
  goalId: number;
  onBack: () => void;
};

const HIT_SLOP = { top: 8, bottom: 8, left: 8, right: 8 };

const STATUS_COLOR: Record<ChapterProgress['status'], string> = {
  completed: colors.success,
  in_progress: colors.primaryText,
  locked: colors.neutralIcon,
};

export default function ChapterDetailScreen({ chapter, goalId, onBack }: ChapterDetailScreenProps) {
  const completeMission = useCompleteMission(goalId);
  const createMission = useCreateMission(goalId);
  const updateMission = useUpdateMission(goalId);
  const deleteMission = useDeleteMission(goalId);

  const [addingMission, setAddingMission] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  // A conquista "grande" (confete + faixa) é reservada pro momento em
  // que a ÚLTIMA missão do capítulo é concluída -- disparar isso a cada
  // missão banalizaria a recompensa. Cada toque comum já ganha o próprio
  // feedback pequeno (o bounce do checkbox, ver MissionCheckbox).
  const [chapterCelebration, setChapterCelebration] = useState(false);

  useEffect(() => {
    if (!chapterCelebration) return;
    const timeout = setTimeout(() => setChapterCelebration(false), 2200);
    return () => clearTimeout(timeout);
  }, [chapterCelebration]);

  const missions = [...chapter.missions].sort((a, b) => a.order_index - b.order_index);
  const doneCount = missions.filter((m) => m.completed).length;
  const pct = missions.length > 0 ? Math.round((doneCount / missions.length) * 100) : 0;
  const chapterLocked = chapter.status === 'locked';
  const statusColor = STATUS_COLOR[chapter.status];

  function handleToggle(missionId: number, alreadyCompleted: boolean) {
    // Não dá pra "desmarcar" -- o back não tem endpoint pra isso
    // (completar é uma execução registrada, não um campo booleano solto).
    if (alreadyCompleted || chapterLocked) return;
    const remainingAfterThis = missions.filter((m) => !m.completed && m.id !== missionId).length;
    completeMission.mutate({ missionId });
    if (remainingAfterThis === 0) setChapterCelebration(true);
  }

  function handleEditMission(missionId: number, title: string) {
    updateMission.mutate({ missionId, input: { title } });
  }

  function handleDeleteMission(missionId: number) {
    deleteMission.mutate(missionId);
  }

  function handleAddMission() {
    const title = newTitle.trim();
    if (title.length < 3) return;
    createMission.mutate(
      { goal_id: goalId, chapter_id: chapter.id, title },
      { onSuccess: () => { setNewTitle(''); setAddingMission(false); } }
    );
  }

  return (
    <NotebookBackground>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <TouchableOpacity onPress={onBack} style={styles.backLink} accessibilityRole="button" accessibilityLabel="Voltar ao mapa">
          <Ionicons name="arrow-back" size={16} color={colors.textSecondary} />
          <Text style={styles.backText}>voltar ao mapa</Text>
        </TouchableOpacity>

        <View style={styles.headerRow}>
          <View style={[styles.chapterIconCircle, { backgroundColor: `${statusColor}1A`, borderColor: `${statusColor}55` }]}>
            <Ionicons name={iconForChapter(chapter.id)} size={26} color={statusColor} />
          </View>
          <View style={styles.headerTextBlock}>
            <Text style={styles.eyebrow}>Capítulo {chapter.order_index + 1}</Text>
            <Text style={styles.title}>{chapter.title}</Text>
          </View>
        </View>

        {chapter.status === 'completed' && (
          <View style={[styles.statusChip, { backgroundColor: colors.successTint }]}>
            <Ionicons name="checkmark-circle" size={14} color={colors.success} />
            <Text style={[styles.statusChipText, { color: colors.success }]}>Concluído</Text>
          </View>
        )}

        {chapter.status === 'in_progress' && (
          <View style={styles.progressRow}>
            <View style={styles.progressTrack}>
              <View style={[styles.progressFill, { width: `${pct}%` }]} />
            </View>
            <Text style={styles.progressLabel}>{pct}%</Text>
          </View>
        )}

        {chapterLocked && (
          <View style={styles.lockedNote}>
            <Ionicons name="lock-closed-outline" size={13} color={colors.textSecondary} />
            <Text style={styles.lockedNoteText}>Complete o capítulo atual pra desbloquear este.</Text>
          </View>
        )}

        <View style={styles.sectionHeaderRow}>
          <Text style={styles.sectionLabel}>
            Missões
            <Text style={styles.sectionCount}> · {doneCount}/{missions.length} concluídas</Text>
          </Text>
        </View>

        <View style={styles.missionListWrap}>
          {chapterCelebration && (
            <View style={styles.celebrationAnchor} pointerEvents="none">
              <CelebrationBurst onDone={() => setChapterCelebration(false)} />
            </View>
          )}

          {missions.map((mission) => (
            <MissionRow
              key={mission.id}
              mission={mission}
              locked={chapterLocked}
              onToggle={() => handleToggle(mission.id, mission.completed)}
              onEdit={(title) => handleEditMission(mission.id, title)}
              onDelete={() => handleDeleteMission(mission.id)}
            />
          ))}

          {missions.length === 0 && !addingMission && (
            <Text style={styles.emptyMissions}>
              {chapterLocked ? 'As missões deste capítulo ainda vão aparecer aqui.' : 'Nenhuma missão ainda — adicione a primeira!'}
            </Text>
          )}
        </View>

        {!chapterLocked && (
          addingMission ? (
            <View style={styles.addForm}>
              <TextInput
                style={styles.addInput}
                placeholder="Título da nova missão..."
                placeholderTextColor={colors.textSecondary}
                value={newTitle}
                onChangeText={setNewTitle}
                autoFocus
                maxLength={255}
                onSubmitEditing={handleAddMission}
              />
              <View style={styles.addActions}>
                <TouchableOpacity onPress={() => { setAddingMission(false); setNewTitle(''); }} style={styles.addCancel}>
                  <Text style={styles.addCancelText}>Cancelar</Text>
                </TouchableOpacity>
                <TouchableOpacity onPress={handleAddMission} style={styles.addConfirm} disabled={createMission.isPending}>
                  <Text style={styles.addConfirmText}>{createMission.isPending ? 'Salvando...' : 'Adicionar'}</Text>
                </TouchableOpacity>
              </View>
            </View>
          ) : (
            <TouchableOpacity style={styles.addButton} onPress={() => setAddingMission(true)} accessibilityRole="button" accessibilityLabel="Adicionar missão">
              <Text style={styles.addButtonText}>+ adicionar missão</Text>
            </TouchableOpacity>
          )
        )}

        {!chapterLocked && missions.length > 0 && (
          <Text style={styles.hint}>toque no lápis pra editar · toque na lixeira pra apagar</Text>
        )}
      </ScrollView>
    </NotebookBackground>
  );
}

// ─── checkbox com bounce -- só anima na transição false→true, então
// missões que já chegam concluídas do servidor não "pulam" à toa ───────

function MissionCheckbox({ done }: { done: boolean }) {
  const scale = useRef(new Animated.Value(1)).current;
  const wasDone = useRef(done);

  useEffect(() => {
    if (done && !wasDone.current) {
      scale.setValue(0.55);
      Animated.spring(scale, { toValue: 1, friction: 4, tension: 130, useNativeDriver: true }).start();
    }
    wasDone.current = done;
  }, [done, scale]);

  return (
    <Animated.View style={[styles.checkbox, done && styles.checkboxDone, { transform: [{ scale }] }]}>
      {done && <Ionicons name="checkmark" size={14} color={colors.surface} />}
    </Animated.View>
  );
}

// ─── linha de missão: concluir, editar (inline) e apagar (com confirmação) ─

function MissionRow({
  mission,
  locked,
  onToggle,
  onEdit,
  onDelete,
}: {
  mission: MissionProgress;
  locked: boolean;
  onToggle: () => void;
  onEdit: (title: string) => void;
  onDelete: () => void;
}) {
  const [editing, setEditing] = useState(false);
  const [text, setText] = useState(mission.title);
  const inputRef = useRef<TextInput>(null);

  useEffect(() => {
    if (editing) inputRef.current?.focus();
  }, [editing]);

  function commitEdit() {
    const trimmed = text.trim();
    if (trimmed.length >= 3 && trimmed !== mission.title) {
      onEdit(trimmed);
    } else {
      setText(mission.title);
    }
    setEditing(false);
  }

  function confirmDelete() {
    Alert.alert('Apagar esta missão?', `"${mission.title}" será removida do capítulo. Essa ação não pode ser desfeita.`, [
      { text: 'Cancelar', style: 'cancel' },
      { text: 'Apagar', style: 'destructive', onPress: onDelete },
    ]);
  }

  return (
    <View style={[styles.missionRow, mission.completed && styles.missionRowDone]}>
      <TouchableOpacity
        onPress={onToggle}
        disabled={mission.completed || locked}
        hitSlop={HIT_SLOP}
        accessibilityRole="checkbox"
        accessibilityState={{ checked: mission.completed, disabled: mission.completed || locked }}
        accessibilityLabel={mission.title}
      >
        <MissionCheckbox done={mission.completed} />
      </TouchableOpacity>

      {editing ? (
        <TextInput
          ref={inputRef}
          style={styles.missionEditInput}
          value={text}
          onChangeText={setText}
          onBlur={commitEdit}
          onSubmitEditing={commitEdit}
          maxLength={255}
        />
      ) : (
        <Text style={[styles.missionTitle, mission.completed && styles.missionTitleDone]}>{mission.title}</Text>
      )}

      {!locked && !editing && (
        <View style={styles.missionActions}>
          {!mission.completed && (
            <TouchableOpacity onPress={() => setEditing(true)} hitSlop={HIT_SLOP} accessibilityRole="button" accessibilityLabel="Editar missão">
              <Ionicons name="pencil-outline" size={15} color={colors.textSecondary} />
            </TouchableOpacity>
          )}
          <TouchableOpacity onPress={confirmDelete} hitSlop={HIT_SLOP} accessibilityRole="button" accessibilityLabel="Apagar missão">
            <Ionicons name="trash-outline" size={15} color={colors.textSecondary} />
          </TouchableOpacity>
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  content: {
    padding: spacing.md,
    paddingBottom: spacing.xl,
  },
  backLink: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  backText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  chapterIconCircle: {
    width: 52,
    height: 52,
    borderRadius: 26,
    borderWidth: 1.5,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTextBlock: {
    flex: 1,
  },
  eyebrow: {
    ...typography.eyebrow,
    color: colors.textSecondary,
  },
  title: {
    ...typography.screenTitle,
    color: colors.textPrimary,
    marginTop: 2,
  },
  statusChip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    alignSelf: 'flex-start',
    borderRadius: radius.pill,
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    marginTop: spacing.md,
  },
  statusChipText: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    fontSize: 12,
  },
  progressRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
  },
  progressTrack: {
    flex: 1,
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.border,
  },
  progressFill: {
    height: spacing.sm,
    borderRadius: radius.pill,
    backgroundColor: colors.primary,
  },
  progressLabel: {
    fontFamily: fonts.display,
    fontSize: 13,
    color: colors.primaryText,
  },
  lockedNote: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.sm,
    marginTop: spacing.md,
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: radius.sm,
    backgroundColor: colors.neutralTint,
    alignSelf: 'flex-start',
  },
  lockedNoteText: {
    ...typography.caption,
    fontSize: 12,
    color: colors.textSecondary,
  },
  sectionHeaderRow: {
    marginTop: spacing.lg,
    marginBottom: spacing.sm,
  },
  sectionLabel: {
    ...typography.cardTitle,
    fontSize: 15,
    color: colors.textPrimary,
  },
  sectionCount: {
    ...typography.caption,
    fontFamily: fonts.body,
    fontSize: 12,
    color: colors.textSecondary,
  },
  missionListWrap: {
    position: 'relative',
    gap: spacing.sm,
  },
  celebrationAnchor: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    height: 40,
    alignItems: 'center',
    zIndex: 5,
  },
  missionRow: {
    position: 'relative',
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
    minHeight: touchTarget,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    paddingHorizontal: spacing.md,
  },
  missionRowDone: {
    backgroundColor: 'rgba(15,122,69,0.06)',
    borderColor: 'transparent',
  },
  checkbox: {
    width: 22,
    height: 22,
    borderRadius: 11,
    borderWidth: 1.5,
    borderColor: colors.graphite,
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxDone: {
    backgroundColor: colors.success,
    borderColor: colors.success,
  },
  missionTitle: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
    flex: 1,
  },
  missionTitleDone: {
    color: colors.success,
    textDecorationLine: 'line-through',
  },
  missionEditInput: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
    flex: 1,
    borderBottomWidth: 1,
    borderBottomColor: colors.primary,
    paddingVertical: 2,
  },
  missionActions: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: spacing.md,
  },
  emptyMissions: {
    ...typography.caption,
    fontSize: 13,
    color: colors.textSecondary,
    textAlign: 'center',
    paddingVertical: spacing.lg,
  },
  hint: {
    ...typography.caption,
    fontSize: 10,
    color: colors.textSecondary,
    textAlign: 'center',
    marginTop: spacing.md,
    opacity: 0.7,
  },
  addButton: {
    minHeight: touchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: radius.sm,
    borderWidth: 1.5,
    borderColor: colors.graphite,
    borderStyle: 'dashed',
    marginTop: spacing.sm,
  },
  addButtonText: {
    fontFamily: fonts.bodySemiBold,
    fontSize: 14,
    color: colors.textPrimary,
  },
  addForm: {
    marginTop: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: radius.sm,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
  },
  addInput: {
    ...typography.body,
    fontSize: 14,
    color: colors.textPrimary,
    borderBottomWidth: 1,
    borderBottomColor: colors.notebookRuleLine,
    paddingVertical: spacing.sm,
  },
  addActions: {
    flexDirection: 'row',
    justifyContent: 'flex-end',
    gap: spacing.sm,
    marginTop: spacing.sm,
  },
  addCancel: {
    minHeight: touchTarget - 8,
    justifyContent: 'center',
    paddingHorizontal: spacing.md,
  },
  addCancelText: {
    ...typography.caption,
    color: colors.textSecondary,
  },
  addConfirm: {
    minHeight: touchTarget - 8,
    justifyContent: 'center',
    paddingHorizontal: spacing.md,
    borderRadius: radius.sm,
    backgroundColor: colors.textPrimary,
  },
  addConfirmText: {
    ...typography.caption,
    fontFamily: fonts.bodySemiBold,
    color: colors.surface,
  },
});
