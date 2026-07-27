import axios from 'axios';

// Quando você for publicar o app, essa URL muda para o seu servidor real.
export const api = axios.create({
  baseURL: 'http://192.168.1.10:3000', // IP da sua máquina + Porta do Backend
  timeout: 10000,
});

// Interceptor: Se o usuário estiver logado, injeta o token automaticamente em todas as requisições
api.interceptors.request.use((config) => {
  const token = "token_salvo_do_usuario"; // Depois usaremos o AsyncStorage ou SecureStore aqui
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});