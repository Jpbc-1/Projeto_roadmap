import React, { useCallback, useEffect, useState } from 'react';
import { ActivityIndicator, AppState, AppStateStatus, Platform, View, StyleSheet } from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { useFonts, SpaceGrotesk_500Medium, SpaceGrotesk_600SemiBold, SpaceGrotesk_700Bold } from '@expo-google-fonts/space-grotesk';
import { Inter_400Regular, Inter_500Medium, Inter_600SemiBold, Inter_700Bold } from '@expo-google-fonts/inter';
import { Caveat_600SemiBold, Caveat_700Bold } from '@expo-google-fonts/caveat';
import NetInfo from '@react-native-community/netinfo';
import { QueryClient, QueryClientProvider, focusManager, useQuery, onlineManager } from '@tanstack/react-query';
import { persistQueryClient } from '@tanstack/react-query-persist-client';
import { createAsyncStoragePersister } from '@tanstack/query-async-storage-persister';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { colors } from './src/theme/colors';
import { AuthProvider, useAuth } from './src/context/AuthContext';
import { usePushNotifications } from './src/hooks/usePushNotifications';
import AuthFlow from './src/navigation/AuthFlow';
import OnboardingFlow from './src/navigation/OnboardingFlow';
import { goalService } from './src/services/goalService';
import DashboardScreen from './src/screens/DashboardScreen';
import RotinaScreen from './src/screens/RotinaScreen';
import ObjetivosScreen from './src/screens/ObjetivosScreen';
import ComingSoonScreen from './src/screens/ComingSoonScreen';
import BottomNav from './src/components/BottomNav';
import OfflineBanner from './src/components/OfflineBanner';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      // Padrão do react-query é staleTime: 0 -- qualquer troca de aba ou
      // volta ao app dispara um refetch na hora, o que na prática
      // significa "spinner de novo" toda vez que a pessoa só espiou
      // outra tela e voltou. 1 min é recente o bastante pra esse app
      // (nada aqui muda segundo a segundo) e evita esse refetch
      // desnecessário; quem realmente mudou algo já vê a tela atualizar
      // sozinha via invalidateQueries nas mutations.
      staleTime: 60_000,
      // Também acima do padrão (5 min) -- reabrir uma aba que você
      // olhou há pouco (ex: voltar de Rotina pra Objetivos) deveria
      // mostrar o que já estava ali, não recomeçar do zero.
      gcTime: 10 * 60_000,
      // Padrão é 3 tentativas com backoff exponencial: numa rede ruim
      // isso empurra o "algo deu errado" pra quase 10s depois do
      // primeiro toque, exatamente o tipo de espera que deixa alguém
      // chateado. 1 nova tentativa já cobre uma falha passageira sem
      // segurar a pessoa por tanto tempo.
      retry: 1,
      refetchOnReconnect: true,
    },
  },
});

// Cria o mecanismo para salvar o cache em disco via AsyncStorage
const persister = createAsyncStoragePersister({
  storage: AsyncStorage,
});

// Conecta o queryClient ao persister, garantindo que a fila
// sobreviva ao fechar o app
persistQueryClient({
  queryClient,
  persister,
});

// Avisa o react-query sempre que a internet cair ou voltar
onlineManager.setEventListener((setOnline) => {
  return NetInfo.addEventListener((state) => {
    // O "!!"" garante que o valor repassado seja estritamente booleano
    setOnline(!!state.isConnected);
  });
});

// react-query espera um evento tipo 'visibilitychange' da web pra saber
// quando refazer as queries "stale" ao focar -- no React Native isso
// não existe, então refetchOnWindowFocus (que já vem true por padrão)
// nunca dispara sozinho. Esse é o hook recomendado pela própria
// documentação do react-query pra RN: escuta o AppState e informa o
// focusManager manualmente. Sem isso, voltar pro app depois de um
// tempo em segundo plano mostra dado desatualizado até algo mais forçar
// um refetch.
function onAppStateChange(status: AppStateStatus) {
  if (Platform.OS !== 'web') {
    focusManager.setFocused(status === 'active');
  }
}

function LoadingGate() {
  return (
    <View style={styles.loadingGate}>
      <ActivityIndicator color={colors.primaryText} />
    </View>
  );
}

function MainTabs() {
  const [activeTab, setActiveTab] = useState('inicio');
  return (
    <>
      <View style={styles.screen}>
        {activeTab === 'inicio' && <DashboardScreen />}
        {activeTab === 'rotina' && <RotinaScreen />}
        {activeTab === 'objetivos' && <ObjetivosScreen />}
        {activeTab === 'comunidade' && <ComingSoonScreen title="Comunidade" icon="people-outline" />}
      </View>
      <BottomNav active={activeTab} onSelect={setActiveTab} />
    </>
  );
}

/** Só é alcançado com status === 'authenticated' -- decide entre o
 * fluxo de criar o primeiro objetivo e as abas principais. */
function AuthenticatedGate() {
  const goalsQuery = useQuery({ queryKey: ['goals'], queryFn: goalService.list });
  const [onboardingJustFinished, setOnboardingJustFinished] = useState(false);
  const handleOnboardingComplete = useCallback(() => setOnboardingJustFinished(true), []);

  if (goalsQuery.isLoading) return <LoadingGate />;

  // Se a lista falhar (rede etc.), é mais seguro deixar a pessoa entrar
  // no app principal do que travá-la num loading infinito ou forçar
  // onboarding pra alguém que já tem objetivos -- as próprias abas
  // sabem lidar com uma lista vazia/erro localmente.
  const hasGoals = (goalsQuery.data?.length ?? 0) > 0;
  if (!hasGoals && !onboardingJustFinished && !goalsQuery.isError) {
    return <OnboardingFlow onComplete={handleOnboardingComplete} />;
  }
  return <MainTabs />;
}

function AppShell() {
  const { status } = useAuth();

  usePushNotifications(status === 'authenticated');

  if (status === 'checking') return <LoadingGate />;
  if (status === 'unauthenticated') return <AuthFlow />;
  return <AuthenticatedGate />;
}

export default function App() {
  const [fontsLoaded] = useFonts({
    SpaceGrotesk_500Medium,
    SpaceGrotesk_600SemiBold,
    SpaceGrotesk_700Bold,
    Inter_400Regular,
    Inter_500Medium,
    Inter_600SemiBold,
    Inter_700Bold,
    Caveat_600SemiBold,
    Caveat_700Bold,
  });

  useEffect(() => {
    const subscription = AppState.addEventListener('change', onAppStateChange);
    return () => subscription.remove();
  }, []);

  if (!fontsLoaded) {
    // Antes disto era `return null` -- ou seja, nada montava, nem a cor
    // de fundo do app, só uma tela em branco (a cor padrão do sistema)
    // até as fontes (locais, mas ainda assim não instantâneas em
    // aparelhos mais fracos) terminarem de carregar. Reaproveitar o
    // LoadingGate aqui faz esse instante inicial já nascer com a cor
    // certa em vez de piscar branco antes do app "de verdade" aparecer.
    return <LoadingGate />;
  }

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <SafeAreaProvider>
          <SafeAreaView style={styles.safeArea} edges={['top']}>
            <OfflineBanner />
            <AppShell />
          </SafeAreaView>
          <StatusBar style="dark" />
        </SafeAreaProvider>
      </AuthProvider>
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
  loadingGate: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: colors.background,
  },
});
