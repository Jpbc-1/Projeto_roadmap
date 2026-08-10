import { useMemo } from 'react';
import { useQueries, useQuery } from '@tanstack/react-query';
import { userService } from '../services/userService';
import { goalService, Goal } from '../services/goalService';
import { roadmapService, RoadmapProgress } from '../services/roadmapService';
import { reminderService } from '../services/reminderService';
import { knowledgeService } from '../services/knowledgeService';

export function useMyProfile() {
  return useQuery({ queryKey: ['users', 'me'], queryFn: userService.getMyProfile });
}

export function useNextReminderToday() {
  const query = useQuery({ queryKey: ['reminders'], queryFn: reminderService.list });
  const next = useMemo(() => {
    if (!query.data) return null;
    const now = new Date();
    const weekday = now.getDay();
    const nowMinutes = now.getHours() * 60 + now.getMinutes();

    const todays = query.data.filter((r) => r.is_active && r.days_of_week.includes(weekday));
    if (todays.length === 0) return null;

    const withMinutes = todays.map((r) => {
      const [h, m] = r.time_of_day.split(':').map(Number);
      return { reminder: r, minutes: h * 60 + m };
    });

    // Prefere o próximo que ainda não passou hoje; se todos já passaram,
    // mostra o primeiro do dia mesmo assim (mais útil que não mostrar nada).
    const upcoming = withMinutes.filter((x) => x.minutes >= nowMinutes).sort((a, b) => a.minutes - b.minutes);
    const chosen = upcoming[0] ?? [...withMinutes].sort((a, b) => a.minutes - b.minutes)[0];
    return chosen.reminder;
  }, [query.data]);

  return { data: next, isLoading: query.isLoading };
}

type FeaturedMission = {
  goalId: number;
  goalTitle: string;
  chapterTitle: string;
  chapterOrderIndex: number;
  missionId: number;
  missionTitle: string;
  missionDescription: string | null;
  estimatedMinutes: number | null;
  chapterMissionsDone: number;
  chapterMissionsTotal: number;
};

type OtherGoalSummary = {
  goalId: number;
  goalTitle: string;
  currentChapterTitle: string | null;
  currentMissionTitle: string | null;
  overallProgress: number; // 0-1, progresso em TODOS os capítulos, não só o atual
  isComplete: boolean;
};

/** Combina o perfil + a lista de objetivos + o roadmap de cada um pra
 * decidir: qual missão vira a hero card, e o que mostrar nos cards
 * resumidos dos outros objetivos. Um objetivo sem capítulo em progresso
 * (recém-criado, ainda gerando, ou 100% concluído) não vira destaque —
 * cai pros "outros" com uma legenda apropriada. */
export function useDashboardData() {
  const profileQuery = useMyProfile();
  const goalsQuery = useQuery({ queryKey: ['goals'], queryFn: goalService.list });
  const goals = goalsQuery.data ?? [];

  const roadmapResults = useQueries({
    queries: goals.map((goal) => ({
      queryKey: ['roadmap', goal.id],
      queryFn: () => roadmapService.getRoadmap(goal.id),
    })),
  });

  const reviewsQuery = useQuery({ queryKey: ['knowledge', 'due'], queryFn: knowledgeService.getDueReviews });
  const nextReminder = useNextReminderToday();

  const { featured, others } = useMemo(() => {
    let featuredResult: FeaturedMission | null = null;
    const othersResult: OtherGoalSummary[] = [];

    goals.forEach((goal: Goal, i: number) => {
      const roadmap: RoadmapProgress | undefined = roadmapResults[i]?.data;
      // Um roadmap que ainda não voltou da rede não é a mesma coisa que
      // um roadmap vazio -- tratar os dois igual faria um objetivo com
      // capítulo em andamento pipocar em "others" por um instante (com
      // título/progresso zerados) antes de virar o destaque de verdade
      // assim que a resposta chega. Melhor simplesmente esperar por
      // ESTE objetivo especificamente, sem travar a tela toda (ver
      // `roadmapsLoading` mais abaixo, que é o que a UI usa pra decidir
      // entre "carregando" e "realmente não tem nada aqui").
      if (roadmap === undefined) return;

      const currentChapter = roadmap.chapters.find((c) => c.status === 'in_progress');
      const currentMission =
        currentChapter?.missions.find((m) => m.id === roadmap.current_mission_id) ??
        currentChapter?.missions.find((m) => !m.completed);

      if (!featuredResult && currentChapter && currentMission) {
        const done = currentChapter.missions.filter((m) => m.completed).length;
        featuredResult = {
          goalId: goal.id,
          goalTitle: goal.title ?? 'Seu objetivo',
          chapterTitle: currentChapter.title,
          chapterOrderIndex: currentChapter.order_index,
          missionId: currentMission.id,
          missionTitle: currentMission.title,
          missionDescription: currentMission.description,
          estimatedMinutes: currentMission.estimated_minutes,
          chapterMissionsDone: done,
          chapterMissionsTotal: currentChapter.missions.length,
        };
      } else {
        const hasChapters = roadmap.chapters.length > 0;
        const isComplete = hasChapters && roadmap.chapters.every((c) => c.status === 'completed');
        // RoadmapCard documenta progress como "progresso geral no
        // roadmap", não só do capítulo atual -- soma missões
        // concluídas/total em TODOS os capítulos, não só no em andamento.
        const allMissions = roadmap.chapters.flatMap((c) => c.missions);
        const overallProgress = allMissions.length > 0 ? allMissions.filter((m) => m.completed).length / allMissions.length : 0;
        othersResult.push({
          goalId: goal.id,
          goalTitle: goal.title ?? 'Seu objetivo',
          currentChapterTitle: currentChapter?.title ?? null,
          currentMissionTitle: currentMission?.title ?? null,
          overallProgress,
          isComplete,
        });
      }
    });

    return { featured: featuredResult, others: othersResult };
  }, [goals, roadmapResults]);

  // Só profile + lista de objetivos -- 2 chamadas, não "2 + 1 por
  // objetivo". Cabeçalho, ofensiva e lembrete não dependem de roadmap
  // nenhum, então não faz sentido segurá-los esperando o mais lento dos
  // N roadmaps terminar (ver DashboardScreen: só a área da missão em
  // destaque usa `roadmapsLoading`, o resto usa só este `isLoading`).
  const isLoading = profileQuery.isLoading || goalsQuery.isLoading;
  const roadmapsLoading = goalsQuery.isLoading || roadmapResults.some((r) => r.isLoading);

  return {
    profile: profileQuery.data ?? null,
    featured,
    others,
    dueReviewCount: reviewsQuery.data?.length ?? 0,
    nextReminder: nextReminder.data,
    isLoading,
    roadmapsLoading,
  };
}
