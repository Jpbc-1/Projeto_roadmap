import React, { useState } from 'react';
import { View, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { useFonts, SpaceGrotesk_500Medium, SpaceGrotesk_600SemiBold, SpaceGrotesk_700Bold } from '@expo-google-fonts/space-grotesk';
import { Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold } from '@expo-google-fonts/inter';
import { colors } from './src/theme/colors';
import DashboardScreen from './src/screens/DashboardScreen';
import RotinaScreen from './src/screens/RotinaScreen';
import ObjetivosScreen from './src/screens/ObjetivosScreen';
import ComingSoonScreen from './src/screens/ComingSoonScreen';
import BottomNav from './src/components/BottomNav';

// 1. IMPORTAMOS O TANSTACK QUERY
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// 2. CRIAMOS O CLIENTE FORA DO COMPONENTE
// Isso garante que o cache não seja resetado a cada re-render da tela
const queryClient = new QueryClient();

export default function App() {
  const [activeTab, setActiveTab] = useState('inicio');

  const [fontsLoaded] = useFonts({
    SpaceGrotesk_500Medium,
    SpaceGrotesk_600SemiBold,
    SpaceGrotesk_700Bold,
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
  });

  if (!fontsLoaded) {
    return null;
  }

  return (
    // 3. ENVOLVEMOS O APP INTEIRO COM O PROVEDOR
    <QueryClientProvider client={queryClient}>
      <SafeAreaProvider>
        <SafeAreaView style={styles.safeArea} edges={['top']}>
          <View style={styles.screen}>
            {activeTab === 'inicio' && <DashboardScreen />}
            {activeTab === 'rotina' && <RotinaScreen />}
            {activeTab === 'objetivos' && <ObjetivosScreen />}
            {activeTab === 'comunidade' && <ComingSoonScreen title="Comunidade" icon="people-outline" />}
          </View>
          <BottomNav active={activeTab} onSelect={setActiveTab} />
        </SafeAreaView>
        <StatusBar style="dark" />
      </SafeAreaProvider>
    </QueryClientProvider>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.background,
  },
  screen: {
    flex: 1,
  },
});