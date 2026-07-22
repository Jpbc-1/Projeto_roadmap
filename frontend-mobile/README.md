# Dashboard — redesign

Tela inicial redesenhada em React Native + Expo + TypeScript.

## O que mudou

- **Um foco só na tela**: o card de missão é o único elemento "hero" — tudo o resto tem menos peso visual, então o olho sabe onde ir primeiro.
- **Card de missão com menos camadas**: de 5 blocos de texto pra 3 (contexto do capítulo/missão, a frase principal, XP/tempo).
- **Streak com uma visualização só**: uma barra de progresso com marcador de chama, no lugar dos dois indicadores (checkmarks + slider) que competiam entre si no original.
- **Paleta com uma função por cor**: roxo = marca/navegação, verde = ação positiva (finalizar missão), laranja = streak, âmbar = XP. Cada cor tem um job só — o botão de finalizar deixou de ser vermelho, que normalmente sinaliza erro.
- **Cards de trilha consistentes**: mesmo tratamento de ícone nos dois cards, com uma barra de progresso preenchendo o espaço em branco que sobrava.

Tudo (cores, espaçamento, tipografia) vem de `src/theme/colors.ts` — pra mudar a identidade visual inteira, é só editar esse arquivo.

## Estrutura

```
index.ts                       → entrada real do app (registra o App.tsx)
App.tsx                        → componente raiz, renderiza a DashboardScreen
src/
  theme/colors.ts              → tokens: cor, espaçamento, tipografia
  components/
    StatsBar.tsx                → nível, streak, badges (3 pills consistentes)
    MissionCard.tsx              → card de missão (hero da tela)
    StreakProgress.tsx            → streak challenge, visualização única
    CourseCard.tsx                 → card de trilha/curso reutilizável
    BottomNav.tsx                   → nav inferior — só visual, ver nota abaixo
  screens/
    DashboardScreen.tsx             → compõe tudo, com dados de exemplo
```

## Rodar isolado (preview)

```bash
npm install
npx expo start
```

Escaneia o QR code com o app Expo Go no Android pra ver rodando no celular.

## Integrar na sua pasta frontend-mobile já existente

1. Copie a pasta `src/` pra dentro do seu projeto (ou só os arquivos que ainda não existem).
2. Instale as duas dependências extras que esse dashboard usa: `npx expo install expo-linear-gradient @expo/vector-icons`.
3. Troque a URL do avatar em `DashboardScreen.tsx` pela foto real do usuário.
4. Os dados (nível, XP, streak, missão) estão hardcoded no `DashboardScreen` — troque pelos dados vindos da sua API/estado (Context, Zustand, Redux, o que você já usa).
5. `BottomNav` é só visual, sem rotas de verdade. Troque `onSelect` pela navegação real do seu projeto (React Navigation ou Expo Router).

## Notas

- Ícones vêm do `@expo/vector-icons` (Ionicons) — é uma dependência separada, não vem pré-instalada; por isso entra no passo 2 acima.
- O `SafeAreaView` usado é o nativo do React Native (funciona bem no iOS; no Android não faz nada, mas também não quebra nada). Se quiser um controle mais preciso de área segura no Android, o pacote `react-native-safe-area-context` é o próximo passo.
- **Versões**: o `package.json` tá fixado no Expo SDK 57 (o atual). O app Expo Go instalado no seu celular só abre projetos na mesma versão de SDK que ele suporta — se depois de um tempo o Expo lançar um SDK novo e o Expo Go do celular atualizar sozinho pela Play Store, esse projeto vai passar a dar erro de "incompatible version" até você rodar `npx expo install expo@latest --fix` pra atualizar o projeto junto.
- Todo o projeto foi validado com `tsc --noEmit` sem erros antes da entrega.
