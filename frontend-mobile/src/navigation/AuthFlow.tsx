import React, { useState } from 'react';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';

export default function AuthFlow() {
  const [mode, setMode] = useState<'login' | 'register'>('login');

  return mode === 'login' ? (
    <LoginScreen onNavigateToRegister={() => setMode('register')} />
  ) : (
    <RegisterScreen onNavigateToLogin={() => setMode('login')} />
  );
}
