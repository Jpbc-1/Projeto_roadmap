import { api } from './api';

export type ChapterStatus = 'locked' | 'in_progress' | 'completed';

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

export type CreateMissionInput = {
  goal_id: number;
  chapter_id: number;
  title: string;
  description?: string | null;
  estimated_minutes?: number | null;
};

export type UpdateMissionInput = {
  title?: string;
  description?: string | null;
  estimated_minutes?: number | null;
};

export type CompleteMissionInput = {
  user_reflection?: string | null;
  difficulty_rating?: 'too_easy' | 'just_right' | 'too_hard' | null;
  satisfaction_rating?: number | null; // 1-5
};

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

export type MissionExecution = {
  id: number;
  mission_id: number;
  completed_at: string;
  xp_rewarded: number;
  user_reflection: string | null;
  ai_feedback: string | null;
  difficulty_rating: string | null;
  satisfaction_rating: number | null;
};

export const roadmapService = {
  getRoadmap: async (goalId: number): Promise<RoadmapProgress> => {
    const response = await api.get(`/goals/${goalId}/roadmap`);
    return response.data;
  },

  // Corpo vazio é válido -- os 3 campos são opcionais (o back deixa o
  // front decidir quando vale a pena perguntar reflexão/dificuldade
  // pra não cansar o usuário a cada missão completada).
  completeMission: async (missionId: number, input: CompleteMissionInput = {}): Promise<MissionExecution> => {
    const response = await api.post(`/missions/${missionId}/complete`, input);
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
