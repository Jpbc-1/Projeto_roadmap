import { api } from './api';

// Definimos o formato dos dados para o TypeScript nos ajudar
export type Mission = {
  id: string;
  title: string;
  description: string;
  isCompleted: boolean;
};

export const roadmapService = {
  // Pega a missão de hoje
  getDailyMission: async (): Promise<Mission> => {
    const response = await api.get('/missions/today');
    return response.data;
  },
  
  // Envia para o backend que o usuário completou a missão
  completeMission: async (missionId: string) => {
    const response = await api.post(`/missions/${missionId}/complete`);
    return response.data;
  }
};