import { api } from './api';

// Não existe /auth/me dedicado no back -- este é o mesmo endpoint de
// perfil de gamificação (exige o mesmo token válido), só que agora
// como um service de verdade em vez de uma chamada solta dentro do
// AuthContext. GET /users/me é a única rota aqui.
export type GamificationProfile = {
  user_id: number;
  username: string | null;
  email: string;
  total_xp: number;
  current_level: number;
  current_streak: number;
  max_streak: number;
  last_activity_date: string | null;
};

export const userService = {
  getMyProfile: async (): Promise<GamificationProfile> => {
    const response = await api.get('/users/me');
    return response.data;
  },
};
