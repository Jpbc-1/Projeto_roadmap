import axios from 'axios';
import { getToken } from './authStorage';

const FALLBACK_API_URL = 'http://:8000/api/v1'; // colocar seu ip

export const API_URL = process.env.EXPO_PUBLIC_API_URL?.trim() || FALLBACK_API_URL;


export const api = axios.create({
  baseURL: API_URL,
  timeout: 10000,
});

api.interceptors.request.use(async (config) => {
  const token = await getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});
