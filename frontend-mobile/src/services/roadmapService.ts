import { api } from './api';

// Conferido direto contra o backend real:
// app/api/v1/endpoints/goals.py, missions.py e os schemas em
// app/api/v1/schemas/roadmap.py e missions.py. Nenhum campo/rota aqui é
// chute — os nomes batem exatamente com o Pydantic do back.

export type MissionProgress = {
  id: number;
  title: string;
  description: string | null;
  estimated_minutes: number | null;
  order_index: number;
  completed: boolean;
  is_conceptual: boolean;
  created_by: string;
};

export type ChapterStatus = 'locked' | 'in_progress' | 'completed';

export type ChapterProgress = {
  id: number;
  title: string;
  order_index: number;
  status: ChapterStatus;
  created_by: string;
  is_locked_from_ai: boolean;
  missions: MissionProgress[];
};

export type RoadmapProgress = {
  id: number;
  version: number;
  current_chapter_id: number | null;
  current_mission_id: number | null;
  chapters: ChapterProgress[];
};

export type DifficultyRating = 'too_easy' | 'just_right' | 'too_hard';

export type CompleteMissionInput = {
  user_reflection?: string; // máx 2000 chars no back
  difficulty_rating?: DifficultyRating;
  satisfaction_rating?: number; // 1-5
};

export type Achievement = {
  id: number;
  name: string;
  description: string | null;
  required_condition: string;
  icon_url: string | null;
};

// Resposta de POST /missions/{id}/complete -- NÃO é um MissionProgress,
// é o registro de execução (XP ganho, se completou capítulo/objetivo,
// conquistas desbloqueadas na hora).
export type MissionExecution = {
  id: number;
  mission_id: number;
  completed_at: string;
  xp_rewarded: number;
  user_reflection: string | null;
  ai_feedback: string | null;
  difficulty_rating: string | null;
  satisfaction_rating: number | null;
  chapter_completed: boolean;
  goal_completed: boolean;
  newly_unlocked_achievements: Achievement[];
};

export type CreateMissionInput = {
  goal_id: number;
  chapter_id: number;
  title: string; // 3-255 chars
  description?: string; // máx 2000 chars
  estimated_minutes?: number; // 5-180
};

export type UpdateMissionInput = {
  title?: string;
  description?: string;
  estimated_minutes?: number;
};

// Resposta de POST /missions e PATCH /missions/{id}
export type Mission = {
  id: number;
  chapter_id: number;
  title: string;
  description: string | null;
  estimated_minutes: number | null;
  order_index: number;
  is_conceptual: boolean;
  created_by: string;
};

export const roadmapService = {
  getRoadmap: async (goalId: number): Promise<RoadmapProgress> => {
    const response = await api.get(`/goals/${goalId}/roadmap`);
    return response.data;
  },

  completeMission: async (missionId: number, input?: CompleteMissionInput): Promise<MissionExecution> => {
    const response = await api.post(`/missions/${missionId}/complete`, input ?? {});
    return response.data;
  },

  createMission: async (input: CreateMissionInput): Promise<Mission> => {
    const response = await api.post('/missions', input);
    return response.data;
  },

  updateMission: async (missionId: number, input: UpdateMissionInput): Promise<Mission> => {
    const response = await api.patch(`/missions/${missionId}`, input);
    return response.data;
  },

  deleteMission: async (missionId: number): Promise<void> => {
    await api.delete(`/missions/${missionId}`);
  },
};