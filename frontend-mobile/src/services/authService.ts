import { api } from './api';

export type User = {
  id: number;
  email: string;
  username: string | null;
};

export type LoginInput = {
  email: string;
  password: string;
};

export type RegisterInput = {
  email: string;
  password: string;
  username?: string | null;
};

/** Vira um "nome_como_esse" a partir do que a pessoa digitar em "Nome" —
 * o back não tem um campo de nome de exibição separado do username, e
 * username é validado por `^[a-zA-Z0-9_]+$` (3-30 chars). Ao invés de
 * simplesmente descartar o que a pessoa escreveu, deriva um username
 * válido dele. Fica claro no rótulo do campo (RegisterScreen) que é
 * disso que se trata. */
export function slugifyUsername(name: string): string | undefined {
  const slug = name
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '') // remove acentos
    .trim()
    .replace(/\s+/g, '_')
    .replace(/[^a-zA-Z0-9_]/g, '')
    .slice(0, 30);
  return slug.length >= 3 ? slug : undefined;
}

export const authService = {
  register: async (input: RegisterInput): Promise<User> => {
    const response = await api.post('/auth/register', input);
    return response.data;
  },

  // /auth/login espera application/x-www-form-urlencoded (OAuth2PasswordRequestForm
  // no FastAPI), não JSON -- e o campo se chama "username" mesmo sendo o
  // e-mail. Isso é bem diferente de todo o resto da API, então fica só
  // aqui, escondido atrás de uma função com nome normal.
  login: async (input: LoginInput): Promise<{ access_token: string; token_type: string }> => {
    const body = new URLSearchParams();
    body.append('username', input.email);
    body.append('password', input.password);

    const response = await api.post('/auth/login', body.toString(), {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    return response.data;
  },
};
