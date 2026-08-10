import React, { createContext, useContext, useEffect, useState, useCallback } from 'react';
import { authService, slugifyUsername } from '../services/authService';
import { userService } from '../services/userService';
import { getToken, setToken, deleteToken } from '../services/authStorage';

type AuthedIdentity = {
  email: string;
  username: string | null;
};

type AuthStatus = 'checking' | 'authenticated' | 'unauthenticated';

type AuthContextValue = {
  status: AuthStatus;
  identity: AuthedIdentity | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName?: string) => Promise<void>;
  logout: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [status, setStatus] = useState<AuthStatus>('checking');
  const [identity, setIdentity] = useState<AuthedIdentity | null>(null);

  // Não existe um /auth/me dedicado no back -- GET /users/me devolve o
  // perfil de gamificação, mas exige o mesmo token válido, então serve
  // igual como checagem de boot: 401 = token velho/inválido, sucesso =
  // segue autenticado (e a gente aproveita email/username de lá mesmo).
  const hydrateFromToken = useCallback(async () => {
    const token = await getToken();
    if (!token) {
      setStatus('unauthenticated');
      return;
    }
    try {
      const profile = await userService.getMyProfile();
      setIdentity({ email: profile.email, username: profile.username });
      setStatus('authenticated');
    } catch {
      await deleteToken();
      setStatus('unauthenticated');
    }
  }, []);

  useEffect(() => {
    hydrateFromToken();
  }, [hydrateFromToken]);

  const login = useCallback(async (email: string, password: string) => {
    const { access_token } = await authService.login({ email, password });
    await setToken(access_token);
    await hydrateFromToken();
  }, [hydrateFromToken]);

  const register = useCallback(
    async (email: string, password: string, displayName?: string) => {
      const username = displayName ? slugifyUsername(displayName) : undefined;
      await authService.register({ email, password, username });
      // O back não devolve token no registro, só o usuário criado --
      // login em seguida com as mesmas credenciais pra já entrar
      // autenticado, sem pedir pra pessoa digitar tudo de novo.
      await login(email, password);
    },
    [login]
  );

  const logout = useCallback(async () => {
    await deleteToken();
    setIdentity(null);
    setStatus('unauthenticated');
  }, []);

  return (
    <AuthContext.Provider value={{ status, identity, login, register, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within an AuthProvider');
  return ctx;
}
