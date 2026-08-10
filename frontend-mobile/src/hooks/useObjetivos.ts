import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { goalService } from '../services/goalService';
import { roadmapService, CompleteMissionInput, CreateMissionInput, UpdateMissionInput } from '../services/roadmapService';
import { knowledgeService, ReviewDifficulty } from '../services/knowledgeService';

export function useGoals() {
  return useQuery({ queryKey: ['goals'], queryFn: goalService.list });
}

export function useRoadmap(goalId: number | null) {
  return useQuery({
    queryKey: ['roadmap', goalId],
    queryFn: () => roadmapService.getRoadmap(goalId as number),
    enabled: goalId !== null,
  });
}

export function useDueReviews() {
  return useQuery({ queryKey: ['knowledge', 'due'], queryFn: knowledgeService.getDueReviews });
}

function useInvalidateRoadmap(goalId: number | null) {
  const queryClient = useQueryClient();
  return () => {
    queryClient.invalidateQueries({ queryKey: ['roadmap', goalId] });
  };
}

export function useCompleteMission(goalId: number | null) {
  const queryClient = useQueryClient();
  const invalidateRoadmap = useInvalidateRoadmap(goalId);
  return useMutation({
    mutationFn: ({ missionId, input }: { missionId: number; input?: CompleteMissionInput }) =>
      roadmapService.completeMission(missionId, input),
    onSuccess: () => {
      invalidateRoadmap();
      // Completar uma missão concede XP e pode mudar nível/streak --
      // isso vive no perfil de gamificação (useMyProfile), uma query
      // totalmente separada do roadmap. Sem isso, o cabeçalho da Home
      // ficava mostrando XP/streak velhos até algo *outro* forçar um
      // refetch do perfil.
      queryClient.invalidateQueries({ queryKey: ['users', 'me'] });
    },
  });
}

export function useCreateMission(goalId: number | null) {
  const invalidate = useInvalidateRoadmap(goalId);
  return useMutation({
    mutationFn: (input: CreateMissionInput) => roadmapService.createMission(input),
    onSuccess: invalidate,
  });
}

// O service já tinha updateMission/deleteMission prontos (o back suporta
// os dois), só não existia um hook que os chamasse -- ChapterDetailScreen
// só sabia completar e criar. Documento de visão é explícito: cada
// missão pode ser "Concluída, Editada, Criada manualmente, Removida" --
// faltavam 2 dessas 4.
export function useUpdateMission(goalId: number | null) {
  const invalidate = useInvalidateRoadmap(goalId);
  return useMutation({
    mutationFn: ({ missionId, input }: { missionId: number; input: UpdateMissionInput }) =>
      roadmapService.updateMission(missionId, input),
    onSuccess: invalidate,
  });
}

export function useDeleteMission(goalId: number | null) {
  const invalidate = useInvalidateRoadmap(goalId);
  return useMutation({
    mutationFn: (missionId: number) => roadmapService.deleteMission(missionId),
    onSuccess: invalidate,
  });
}

export function useAnswerReview() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ nodeId, difficulty }: { nodeId: number; difficulty: ReviewDifficulty }) =>
      knowledgeService.answerReview(nodeId, difficulty),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['knowledge', 'due'] });
      // ReviewResult inclui xp_earned (e às vezes um bônus diário) --
      // mesma razão do useCompleteMission: sem isso o perfil mostrado no
      // cabeçalho da Home fica desatualizado depois de uma revisão.
      queryClient.invalidateQueries({ queryKey: ['users', 'me'] });
    },
  });
}
