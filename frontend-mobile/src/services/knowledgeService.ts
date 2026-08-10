import { api } from './api';

export type ReviewDifficulty = 'again' | 'hard' | 'good' | 'easy';

export type DueReview = {
  node_id: number;
  goal_id: number;
  goal_title: string | null;
  topic_name: string;
  next_review_date: string;
  mastery_level: string;
};

export type ReviewResult = {
  node_id: number;
  topic_name: string;
  new_interval_days: number;
  new_easiness_factor: number;
  next_review_date: string;
  mastery_level: string;
  remaining_reviews_today: number;
  daily_bonus_awarded: boolean;
  xp_earned: number;
};

export const knowledgeService = {
  getDueReviews: async (): Promise<DueReview[]> => {
    const response = await api.get('/knowledge/due');
    return response.data;
  },

  answerReview: async (nodeId: number, difficulty: ReviewDifficulty): Promise<ReviewResult> => {
    const response = await api.post(`/knowledge/${nodeId}/review`, { difficulty });
    return response.data;
  },
};
