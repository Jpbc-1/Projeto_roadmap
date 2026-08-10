import { api } from './api';

export type PriorKnowledgeLevel = 'beginner' | 'intermediate' | 'advanced';

// "pending" e "processing" são o meu melhor palpite pros estados
// intermediários (o backend com certeza tem "awaiting_info", "completed"
// e "failed" -- vistos direto no código; os dois de "ainda não terminei
// de gerar" eu não confirmei ao pé da letra). GoalProcessingScreen trata
// qualquer valor que não seja um dos 3 confirmados como "ainda
// processando", então um nome diferente aqui não quebra o polling —
// só vale conferir contra o Goal.generation_status real no seu banco.
export type GenerationStatus = 'pending' | 'processing' | 'awaiting_info' | 'completed' | 'failed';

export type Goal = {
  id: number;
  title: string | null;
  context_prompt: string;
  target_date: string | null;
  status: string;
  category: string | null;
  involves_learning: boolean;
  generation_status: GenerationStatus;
  generation_error: string | null;
  weekly_active_days: number | null;
  daily_time_minutes: number | null;
  prior_knowledge_level: PriorKnowledgeLevel | null;
  estimated_completion_weeks: number | null;
  pending_questions: string[] | null;
  created_at: string;
};

export type CreateGoalInput = {
  context_prompt: string;
  target_date?: string | null; // "YYYY-MM-DD"
  weekly_active_days?: number | null;
  daily_time_minutes?: number | null;
  prior_knowledge_level?: PriorKnowledgeLevel | null;
};

export class InsufficientCreditsError extends Error {
  constructor(message: string) {
    super(message);
    this.name = 'InsufficientCreditsError';
  }
}

export const goalService = {
  create: async (input: CreateGoalInput): Promise<{ goal: Goal; message: string }> => {
    try {
      const response = await api.post('/goals', input);
      return response.data;
    } catch (error: any) {
      // POST /goals cobra crédito ANTES de criar o objetivo -- 402 é o
      // único jeito de "não tenho crédito" chegar aqui, então vale um
      // tipo de erro próprio em vez de deixar o axios genérico estourar.
      if (error?.response?.status === 402) {
        throw new InsufficientCreditsError(
          error.response.data?.detail ?? 'Créditos insuficientes para criar um novo objetivo.'
        );
      }
      throw error;
    }
  },

  get: async (goalId: number): Promise<Goal> => {
    const response = await api.get(`/goals/${goalId}`);
    return response.data;
  },

  list: async (): Promise<Goal[]> => {
    const response = await api.get('/goals');
    return response.data;
  },

  // Mesma ordem/tamanho de goal.pending_questions -- string vazia numa
  // posição é uma pergunta pulada, não quebra nada no back.
  answerQuestions: async (goalId: number, answers: string[]): Promise<{ message: string }> => {
    const response = await api.post(`/goals/${goalId}/answers`, { answers });
    return response.data;
  },
};
