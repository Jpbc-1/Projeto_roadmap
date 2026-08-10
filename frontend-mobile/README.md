# Roadmap AI — App Mobile

App em React Native + Expo + TypeScript. Transforma um objetivo digitado
pela pessoa num plano de capítulos e missões diárias — "tipo Duolingo,
mas pra qualquer objetivo da vida".

Se vocês querem entender a arquitetura e o raciocínio por trás do
código (por que não tem React Navigation, como a camada de dados
funciona, o sistema de design), tem um guia de onboarding completo à
parte — peçam pro tech lead. Este README é só "como colocar isso
rodando na sua máquina". O histórico detalhado de cada rodada de
desenvolvimento está preservado mais abaixo, na seção
[Histórico de desenvolvimento](#histórico-de-desenvolvimento).

## Stack

- **Node.js 18+** (recomendado 20 LTS)
- **Expo SDK 54** + **React Native 0.81** + **TypeScript**
- **TanStack Query (react-query)** como camada de dados inteira — sem
  Redux, sem Zustand
- Sem React Navigation — a navegação é estado local em React (ver o
  guia de onboarding pra entender por quê)

Este projeto usa **Expo Dev Client** (não Expo Go puro) — reparem em
`expo-dev-client` no `package.json`. Na prática isso não muda o
`expo start` do dia a dia, mas importa se algum dia vocês forem
adicionar um módulo nativo (ver aviso no fim deste README).

## Pré-requisitos

- Node.js 18 ou superior e npm
- Um backend do Roadmap AI rodando e acessível (ver o README do
  backend) — o app não funciona sozinho, toda a lógica de objetivo/
  roadmap/missão vem da API
- Pra rodar em celular físico: o app **Expo Go** (ou um dev client
  próprio) instalado no aparelho, na mesma rede Wi-Fi que o computador
- Pra rodar em emulador: Android Studio (emulador Android) e/ou Xcode
  (simulador iOS, só em Mac)

## Passo a passo

### 1. Instale as dependências

```bash
cd frontend-mobile
npm install
```

### 2. Configure o `.env`

```bash
cp .env.example .env
```

Abra o `.env` e ajuste `EXPO_PUBLIC_API_URL` pro endereço do seu
backend. O valor certo depende de onde o app vai rodar:

| Onde o app roda | `EXPO_PUBLIC_API_URL` |
|---|---|
| Emulador Android | `http://10.0.2.2:PORTA/api/v1` (`10.0.2.2` é como o emulador Android enxerga o `localhost` da sua máquina) |
| Simulador iOS | `http://localhost:PORTA/api/v1` (o simulador iOS já enxerga `localhost` da máquina normalmente) |
| Celular físico, mesma Wi-Fi | `http://SEU_IP_LOCAL:PORTA/api/v1` (descubram o IP local da máquina — `ipconfig` no Windows, `ifconfig`/`ip a` no Mac/Linux) |
| Backend publicado | `https://api.seuapp.com/api/v1` |

Troquem `PORTA` pela porta que o backend está usando (`3000` se
seguirem o README padrão do backend). **O prefixo `EXPO_PUBLIC_` é
obrigatório** — é o que faz o Expo injetar a variável no bundle do app;
sem ele, a variável não chega no código em runtime, só fica disponível
durante o build.

> Sem `.env` configurado, o app cai num IP hardcoded de fallback
> (`services/api.ts`) que quase certamente não é o seu backend — se
> "nada carrega" e vocês não sabem por quê, confiram isso primeiro.

### 3. Rode o app

```bash
npx expo start
```

Isso abre o Metro Bundler com um QR code no terminal. Daí:

- **Celular físico**: abram o app Expo Go e leiam o QR code (Android:
  dentro do próprio app Expo Go; iOS: pela câmera nativa).
- **Emulador Android**: com o emulador já aberto, apertem `a` no
  terminal onde o Metro está rodando (ou `npm run android`).
- **Simulador iOS** (só Mac): apertem `i` no terminal (ou
  `npm run ios`).

### 4. Confira se conectou com o backend

Abram o app — a primeira tela deveria ser login/registro. Se aparecer
uma tela de erro de rede ou o app ficar travado em carregamento, é
quase sempre `EXPO_PUBLIC_API_URL` errado ou o backend não estar
acessível dali (ver tabela de erros comuns abaixo).

## Checagem de tipos

```bash
npm run typecheck
```

Roda `tsc --noEmit` — confere os tipos do projeto inteiro sem gerar
nenhum arquivo. Rodem isso antes de abrir um PR; é o mais perto de teste
automatizado que o projeto tem hoje (não existe nenhuma suíte de teste
de verdade ainda — ver seção "O que ainda falta" abaixo).

## Erros comuns ao rodar pela primeira vez

| Sintoma | Causa provável |
|---|---|
| App abre mas login/registro dá erro de rede | `EXPO_PUBLIC_API_URL` errado pro ambiente onde o app está rodando (ver tabela do passo 2) — o erro mais comum é usar `localhost` num celular físico, que aponta pro próprio celular, não pra sua máquina. |
| Emulador Android não conecta em nada | Confiram se usaram `10.0.2.2`, não `localhost`, e se o backend subiu com `--host 0.0.0.0` (ver README do backend). |
| Celular físico não conecta | Celular e computador precisam estar na **mesma rede Wi-Fi**; redes de convidado costumam isolar dispositivos entre si e bloquear isso mesmo estando "na mesma rede" visualmente. |
| `npx expo start` reclama de versão de pacote incompatível | As versões no `package.json` já foram conferidas contra o que o Expo SDK 54.0.36 espera (ver nota no changelog abaixo sobre a correção do `expo-secure-store`). Se ainda assim aparecer um aviso de incompatibilidade, rodem `npx expo install --check` (precisa de internet) — ele confere contra o registro do Expo e sugere o comando de correção. |
| Erro ao tentar usar câmera, notificação push, haptics, ou qualquer recurso nativo que "deveria existir" | Provavelmente o módulo não está instalado (ver aviso abaixo) — bibliotecas nativas exigem rebuild do dev client, não só `npm install`. |
| Build EAS vai pro projeto errado / pede permissão de outro dono | O `app.json` já vem com um `eas.projectId` de um projeto EAS específico (herdado de quando este app foi criado). Se vocês forem fazer builds próprios, rodem `eas init` pra vincular a um projeto EAS de vocês antes. |

## O que ainda falta (pra não assumirem que já existe)

- **Zero testes automatizados** — nem unitário nem end-to-end. O
  arquivo `src/utils/journeyMapLayout.ts` é o candidato mais fácil pra
  começar (é lógica pura, sem depender de React Native pra testar).
- **Push notification real não está plugado** — nem aqui, nem no
  backend (é stub dos dois lados). O que existe hoje é só uma leitura
  local do próximo lembrete, mostrada no dashboard.
- **`react-native-reanimated`, `expo-haptics` e `expo-splash-screen`
  não estão instalados.** São módulos nativos — instalar qualquer um
  deles exige reconstruir o dev client (`npx expo prebuild` e depois
  rodar de novo via EAS ou localmente), não basta `npm install`. Toda
  animação do app hoje usa só o `Animated` nativo do React Native ou
  SVG animado, exatamente pra não depender de rebuild.
- **CRUD de capítulo não existe** (só de missão) — o backend só expõe
  leitura de capítulo hoje.

## Estrutura do projeto (resumo)

```
frontend-mobile/
├── App.tsx                # Raiz: providers, navegação em 3 níveis
├── src/
│   ├── theme/                # Sistema de design (cor, espaçamento, tipografia)
│   ├── context/                  # Sessão de autenticação
│   ├── navigation/                  # Fluxos de auth e onboarding
│   ├── services/                       # Chamadas HTTP, uma função por endpoint
│   ├── hooks/                             # react-query por cima dos services
│   ├── utils/                                # Lógica pura (datas, geometria do mapa)
│   ├── components/                              # UI reutilizável
│   └── screens/                                    # Telas de verdade
└── app.json                # Configuração do Expo
```

Pra entender **por que** está organizado assim — inclusive por que não
tem React Navigation, e o caminho completo de ponta a ponta de criar um
objetivo e completar uma missão — consultem o guia de onboarding do
frontend.

---

## Histórico de desenvolvimento

> A partir daqui é o registro histórico de cada rodada de trabalho no
> projeto, mantido como estava — decisões, trade-offs e o "porquê" por
> trás de cada mudança, na ordem em que aconteceram (mais recente
> primeiro). Não é guia de setup; é o diário de bordo do projeto.

## Décima primeira rodada — mapa de aventura a grafite na aba Objetivos, missão editável, e uma passada de performance

Pedido desta rodada: aplicar o design de referência (`Caderno_com_design_grafite`, um protótipo Figma Make) na aba Objetivos, melhorar o que desse, e prestar atenção em performance — "tipo um Duolingo pra vida", então precisa dar vontade de voltar.

Antes de mexer em qualquer coisa, uma auditoria: **o projeto não instalava**. `expo-secure-store: ~14.0.4` no `package.json` não existe no registro do npm (o SDK 54 publica `~15.0.8` — deve ter sido digitado errado em algum momento). Corrigido; é a única mudança de versão nesta rodada, tudo o mais já estava certo. Também não existia `.gitignore` nenhum — `node_modules`, `.env`, builds nativos, tudo isso ia parar no git do jeito que estava. Adicionado.

### O mapa em si (o pedido principal)

A referência mostra um "mapa de aventura" desenhado à mão — montanha/trilha sinuosa ligando os capítulos, cada um com um estado visual diferente (concluído = colorido com carimbo, atual = ganhando cor aos poucos, futuro = só esboço preto e branco, e o que a IA ainda nem gerou = neblina). Isso substituiu o `JourneyPath` anterior, que era uma lista vertical simples de círculos.

Diferença importante em relação à referência: lá os 4 capítulos têm posição x/y fixa, escritas à mão no protótipo. Isso não existe nos dados reais — um roadmap tem N capítulos, cada um só com `status` (locked/in_progress/completed) e `order_index`, sem coordenada nem tema visual. Então o mapa é **geometria calculada**, não coordenadas copiadas (ver `src/utils/journeyMapLayout.ts`, novo): uma trilha em zigue-zague ancorada no capítulo atual, com Catmull-Rom convertido pra Bézier cúbica pra suavizar a curva entre qualquer quantidade de pontos. Igual ao roadmap de verdade, a janela visível é só um recorte (histórico recente + atual + próximos + neblina) — o documento de visão já dizia que "a IA gera só alguns capítulos por vez", capítulos concluídos mais antigos viram um resumo em texto, não nós competindo por espaço.

Decisões que se afastam da referência de propósito:
- **Sem filtro de SVG (`feTurbulence`/`feDisplacementMap`)**: o `react-native-svg` não sustenta isso de forma confiável em runtime no celular, e mesmo que sustentasse, filtro pesado repetido em dezenas de elementos é exatamente o tipo de coisa que devia ser evitada dado o pedido de performance. A textura "desenhada à mão" vem de duas linhas sobrepostas com opacidade/espessura levemente diferentes (mesma ideia que o extinto `RoadmapSketch` já usava) — zero custo de runtime.
- **Ícone por capítulo (novo, `src/utils/chapterVisuals.ts`)**: o back não manda ícone nenhum por capítulo, só `title`. Em vez de inventar um campo novo na API, o ícone (Ionicons, não emoji — consistente com o resto do app) é derivado do `chapter.id`: determinístico, mesmo capítulo sempre com o mesmo símbolo, e usado tanto no mapa quanto no cabeçalho do `ChapterDetailScreen`.
- **Sem tema por categoria (montanha vs. floresta vs. cidade)**: o documento de visão sugere isso, e o `Goal` até tem um campo `category`, mas não tenho os valores reais que o back usa nesse campo — arriscar comparações de string contra um enum que eu não conheço ia gerar mapas "sem tema" silenciosamente pra qualquer categoria que eu não adivinhasse certo. Fica de fora até o taxonomy de categorias estar confirmado.
- **Capítulos bloqueados agora são tocáveis** (não eram no `JourneyPath` anterior) — dá pra espiar o próximo capítulo antes de chegar nele, léitura/missões incluídas, só sem poder concluir nada. Isso segue a própria referência (só "neblina" é intocável lá) e é também um gancho de curiosidade genuíno.

O progresso do capítulo atual anima de verdade: conforme missões são concluídas, o nó ganha cor (opacidade de um círculo colorido por cima do esboço, de 14% a 88%) e o anel de progresso ao redor preenche — via `Animated.createAnimatedComponent` do próprio `react-native-svg`, sem precisar do Reanimated pra isso.

### `ChapterDetailScreen`: faltavam 2 dos 4 verbos que o documento de visão promete

"Cada missão pode ser: Concluída, Editada, Criada manualmente, Removida" — só concluir e criar já existiam. `roadmapService.updateMission`/`deleteMission` já existiam no arquivo de serviço, só não tinham hook nem UI que os chamasse. Agora têm (`useUpdateMission`/`useDeleteMission`, novos, em `useObjetivos.ts`): lápis pra editar o texto inline, lixeira com confirmação (`Alert.alert`) pra remover. Também ganhou uma barra de progresso pro capítulo atual e um selo "Concluído" pro capítulo já fechado — nenhum dos dois existia antes.

O capítulo INTEIRO virar concluído (última missão pendente marcada) dispara uma comemoração — confete simples (`CelebrationBurst`, novo componente, só `Animated` nativo, sem lib de partícula nova) + uma faixa "Capítulo concluído!" por 2 segundos. Cada missão isolada só ganha um bounce pequeno no próprio checkbox (spring de escala) — reservar o confete pro marco maior evita que a recompensa banalize rápido; é o tipo de reforço variável que faz um hábito grudar em vez de só funcionar.

### Revisões: a pilha que devia encolher, agora encolhe de verdade

O documento de visão descreve isso explicitamente: "quanto menos revisões restarem, menor fica a pilha... o usuário sente que está limpando sua mesa de estudos". O `ReviewPostIt` (o gatilho, no topo da aba) agora mostra de 1 a 3 camadas de post-it empilhadas dependendo da contagem. O `FlashcardReview` (a sessão em si) ganhou: transição animada entre cartas (a respondida sai deslizando pra cima e sumindo, a próxima entra de baixo — duas animações independentes compostas com `Animated.add`/`Animated.multiply`), uma pilha visual atrás da carta atual que também encolhe a cada resposta, e um estado final "Mesa limpa! ✨" com confete antes de fechar sozinho, em vez de só desaparecer.

### Performance — o pedido de "não deixar a pessoa chateada esperando"

- **URL da API estava fixa num IP local** (`192.168.1.10`, hardcoded) — isso não é ajuste de performance, é um bug que faz TODA requisição falhar pra qualquer rede que não seja a de quem escreveu aquela linha, e falha de rede com retry vira exatamente o tipo de espera longa que o pedido queria evitar. Agora lê de `EXPO_PUBLIC_API_URL` (env var pública do Expo, sem depender de pacote novo — ver `.env.example`, novo), com aquele IP como fallback só pra nunca quebrar sem configuração nenhuma.
- **`QueryClient` sem configuração nenhuma** = `staleTime: 0` (qualquer troca de aba refaz a requisição, spinner de novo toda vez) e `retry: 3` com backoff exponencial (quase 10s de espera muda antes de qualquer erro aparecer numa rede ruim). Ajustado pra `staleTime: 60s`, `gcTime: 10min`, `retry: 1`.
- **`AppState` ligado ao `focusManager`** do react-query — sem isso, o `refetchOnWindowFocus` (que já vem `true` por padrão) nunca dispara de verdade no React Native, porque não existe evento de `visibilitychange` como na web. É o padrão documentado pela própria lib pra RN.
- **Dashboard não trava mais esperando TODOS os roadmaps**: com N objetivos, a Início disparava 1 (perfil) + 1 (lista) + N (um roadmap por objetivo) + 2 (revisões/lembrete) requisições em paralelo, mas só desenhava QUALQUER COISA depois que a mais lenta das N terminasse — cabeçalho, ofensiva e lembrete não dependem de roadmap nenhum. Agora só perfil+lista bloqueiam a tela; a área da missão em destaque tem seu próprio esqueleto de carregamento (`roadmapsLoading`) e pipoca assim que o roadmap certo chega, sem seguraro resto.
- **Tela em branco enquanto as fontes carregam**: `if (!fontsLoaded) return null` não desenhava nada, nem a cor de fundo — no aparelho, isso pisca branco antes do app aparecer de verdade. Agora reaproveita o `LoadingGate` (cor de marca) nesse instante.
- **Trocar de marcador (objetivo) agora é instantâneo**: assim que o roadmap que você está olhando termina de carregar, os outros objetivos são pré-buscados em segundo plano (com um respiro entre cada um). Trocar de aba deveria parecer abrir outro caderno que já estava ali na mesa, não carregar algo novo.

### Limpeza (sem mudar comportamento nenhum)

Achei 8 arquivos de componente sem nenhuma referência no projeto — alguns nem compilavam mais (`CourseCard`/`TodayItem` usavam tokens de cor que não existem desde a Oitava rodada). Dois deles (`RoadmapSketch`, `ReviewStack`) tinham sido substituídos por `JourneyPath`/`ReviewPostIt` numa rodada que não ficou documentada aqui — o README dizia uma coisa, o código já fazia outra havia um tempo. Removidos os 8; `tsc --noEmit` seguiu limpo.

### O que não fiz (e por quê)

- **CRUD de capítulo** (criar/editar/apagar um capítulo manualmente, como a referência tem via um botão "+ capítulo"): o back só expõe leitura de capítulo (`getRoadmap`) — criar/editar/apagar existe só pra missão. O próprio documento de visão também só promete os 4 verbos pra missão, nunca pra capítulo; a referência ter isso é mais uma liberdade de protótipo sem back de verdade por trás do que uma promessa de produto.
- **`react-native-reanimated`, `expo-haptics`, `expo-splash-screen`**: melhorariam a sensação de toque/abertura do app, mas nenhum dos três está instalado hoje, e todos são módulos nativos — adicionar exigiria reconstruir o dev client (`expo prebuild`/EAS), coisa que não dá pra validar sem um aparelho/emulador de verdade na mão. Toda animação nova nesta entrega usa só o `Animated` que o projeto já usa (`PushPin`/`WashiTape`) ou SVG animado nativamente, pra não depender de um rebuild pra funcionar.

## Décima rodada — aba Objetivos: caderno, esboço a grafite, e revisão de verdade

Primeira vez mexendo fora da Início/Rotina — você pediu especificamente essa aba, com tema de "coisas que ajudam a estudar na vida real". Três peças:

- **`NotebookBackground` (novo)**: papel pautado (linhas horizontais geradas em loop, não hardcoded uma por uma), linha vermelha de margem, furos de espiral — material bem diferente do quadro de cortiça da Início, só que na mesma família de "objeto físico de estudo".
- **`RoadmapSketch` (novo)**: o roadmap desenhado a lápis — usa `react-native-svg` (dependência nova, pesou a decisão mas um caminho sinuoso de verdade não dá pra fingir só com Views retangulares). Traço duplo levemente deslocado pra parecer risco de grafite, não vetor limpo. Três estados: concluído (círculo com miolo verde), atual (círculo duplo, com um "lápis" ao lado), bloqueado (círculo tracejado, mais apagado).
- **`ReviewStack` + `FlashcardReview` (novos)**: a prévia é uma pilha de post-its levemente abertos em leque; ao tocar, entra numa revisão de verdade — carta por carta, "toque pra ver a resposta", e depois os 4 botões de avaliação **Again / Difícil / Médio / Fácil** (o sistema clássico do Anki). Sem motor de repetição espaçada de verdade por trás (isso é backend), mas a interação em si — julgar a própria resposta antes do baralho avançar — é a mecânica real, não só uma prévia estática.

### Mudança de arquitetura: fundo passou a ser por tela, não global

Até a rodada passada, `App.tsx` envolvia tudo num `WoodBackground` só. Como a Objetivos precisa de um material completamente diferente (caderno, não madeira), cada tela agora se envolve no próprio fundo (`DashboardScreen` e `RotinaScreen` em `WoodBackground`, `ObjetivosScreen` em `NotebookBackground`). `App.tsx` ficou mais simples — só o frame (SafeAreaView + BottomNav) — e isso não exigiu tocar no conteúdo da Rotina, só adicionar o wrapper de volta (você pediu pra não alterar Rotina agora; isso é ajuste técnico, não redesign).

### Cores novas, mesma disciplina

`graphite` (cinza grafite, 8.9:1 no papel) pro esboço; 4 cores de avaliação (`ratingAgain`/`ratingHard`/`ratingMedium`/`ratingEasy`, todas ≥4.5:1 com texto branco) — essa é uma escala genuinamente à parte das 5 famílias do resto do app, não forcei encaixe.

## Nona rodada — mais personalidade, quadro de verdade

Sua reação de "faltou personalidade" fazia sentido — a rodada anterior tinha a paleta certa mas ainda lia como app genérico com fundo marrom. Essa rodada é sobre isso especificamente. Fiquei só na tela inicial, como combinado.

- **Textura bem mais presente**: `WoodBackground` agora tem respingos (speckles) espalhados simulando cortiça, veios mais visíveis, e uma vinheta sutil nas bordas — não é mais "quase imperceptível", dá pra ver que é um quadro.
- **A missão principal virou post-it de verdade**: amarelo, levemente torto (`rotate: -1.5deg`), com alfinete em cima E uma fita washi no canto, sombra "dura" (não desfocada) pra parecer papel physicamente levantado do quadro — era o detalhe que você tinha gostado e eu não tinha replicado.
- **"Suas outras missões" virou cartõezinhos coloridos**: cada card puxa de uma paleta de 4 cores pastéis (azul, rosa, verde, pêssego — o amarelo ficou reservado pra missão principal), com rotação alternada e ora alfinete ora fita, tipo mural de investigação — a referência que você deu bateu bem com "notas de cores diferentes presas meio tortas".
- **Marco também ganhou alfinete** — sem inclinação (fica mais "oficial" entre os cartões tortos).
- **Streak com mais vida**: o vermelho antigo (`#A8330A`) tava opaco demais pra ícone/preenchimento. Separei em dois: `streak` (`#D63A08`, bem mais vibrante — usado em ícone, marcador, barra) e `streakText` (o tom antigo, mais escuro — usado só onde precisa ser texto de verdade, tipo o número do streak). Mesmo raciocínio do laranja de marca: uma cor pra chamar atenção como preenchimento, outra pra funcionar como texto.
- **Nível não é mais só uma estrela muda**: o pill agora mostra "Nv. 12" por extenso (ícone + rótulo + número), em vez de confiar que uma estrela sozinha comunicasse "isso é seu nível".
- **Cantos mais retos, sombra de papel em todo card**: `StreakProgress`, `ReviewCard` e `MilestoneCard` foram de cantos bem arredondados pra cantos mais retos (mesmo raio dos post-its) e ganharam a mesma sombra "física" — antes destoavam do resto por parecerem plástico de app, não papel de quadro.

### Dois bugs de contraste a mais, achados na auditoria desta rodada

Mesmo padrão do laranja de marca (rodada passada): cor viva o bastante pra chamar atenção como preenchimento não necessariamente funciona como texto.
- O vermelho vivo do streak, usado como texto (número do streak, tag "Fácil"), caía pra ~2.9:1. Resolvido com o par `streak`/`streakText` acima.
- Os 5 pastéis dos cartões de roadmap: `textSecondary` padrão caía pra 4.2:1 no rosa (abaixo do mínimo). Criei `textSecondaryOnPastel`, um tom mais escuro que se mantém acima de 5.5:1 nos 5 tons.

## Oitava rodada — identidade visual "mural" + auditoria de contraste

Reskin completo a partir das duas telas de referência que você mandou: fundo de madeira, cards cor de pergaminho, tipografia com mais personalidade. Estrutura interna (hierarquia, grid de 8px, sistema de 5 cores por significado) continua a mesma — só a pele mudou.

- **Paleta nova, mesmas 5 famílias de significado**: laranja assumiu o papel de marca/roadmap (era azul), dourado continua XP/nível, ferrugem (vermelho-alaranjado, propositalmente diferente do laranja de marca) é streak, roxo é revisão, verde é conquista/troféu. No seu mockup o roxo aparecia tanto em "+XP" quanto no botão "Revisar" — corrigi isso: XP voltou pro dourado, roxo ficou só com revisões.
- **Bug de contraste real, encontrado e corrigido**: o laranja vibrante (`primary`) só passa no teste de contraste quando usado como preenchimento sólido com texto escuro em cima (botão "Começar Missão", 5.95:1) — usado como TEXTO ou BORDA sobre fundo claro (aba ativa do menu, dia de hoje no calendário, chip selecionado), a razão cai pra ~2.7:1, bem abaixo do mínimo. Criei um token separado, `primaryText` (laranja mais escuro, 5.7–6.8:1 nesses mesmos contextos), e troquei todo lugar que usava o laranja vibrante como texto/borda. Isso incluía o **item ativo do menu inferior** — hoje ficaria ilegível sem essa correção.
- **`WoodBackground` (novo)**: 3 gradientes verticais quase transparentes sobrepostos à cor sólida — textura de veio de madeira "quase imperceptível", sem imagem nem dependência nova.
- **`PushPin` (novo)**: alfinete decorativo feito só com Views (círculo + brilho + sombra) — sem precisar de `react-native-svg`. Usado no card de missão, como no seu mockup.
- **`HomeHeader` (novo, substitui a antiga `StatsBar` + cabeçalho)**: avatar + saudação em 2 linhas (isso é o que deixa espaço pros pills de streak/nível + sino caberem do lado). Avatar aceita emoji (🦊, 🍊, o que você quiser) OU foto real — cobre as 3 opções que você mencionou.
- **`MilestoneCard` (novo)**: implementação de verdade do "Próximo Marco" — nome do marco, % (verde, fonte de destaque), progresso em missões, recompensa em XP.
- **`StudyReminder` (novo)**: a faixa "Hoje às 19:00 — Sessão de estudos".
- **`RoadmapCard` mudou de card estreito com scroll horizontal pra linha de largura total**, empilhadas verticalmente — como no seu mockup. E removi a duplicata: antes o roadmap em destaque (Python) aparecia de novo aqui embaixo; agora só os OUTROS roadmaps (SQL, Estatística) aparecem, sem repetir o que já tá no card principal.
- **Botão "Ver todos os roadmaps"**: botão de verdade (borda tracejada) depois dos 2 cards, não só um link.
- **Eyebrow simplificado**: "Cap. 3 · Python para Dados" no lugar de "Python para Dados · Cap 3/8" — a fração de capítulo saiu, a barra de % já cobre isso.
- **Botão da missão mais alto**: 56px em vez de 48px.
- **Dificuldade**: tag "Fácil" nova no card de missão — abre espaço pra, no futuro, a missão do dia 1 ser sinalizada como fácil de verdade, não só na prática.

## Sétima rodada — tipografia, hierarquia e o sistema de troféus

Essa foi grande — tocou quase todo arquivo do projeto. Resumo:

- **Duas famílias tipográficas**: **Space Grotesk** (títulos, nomes de missão, e todo número que funciona como "placar emocional" — nível, streak, XP, troféus, % do capítulo) e **Inter** (tudo que se lê — descrições, texto de notificação, corpo em geral). Escolhi essas duas porque Space Grotesk tem números com bastante personalidade sem virar caricatura, e Inter é hoje o padrão de neutralidade/legibilidade em UI. Carregadas via `@expo-google-fonts` — ver `App.tsx`.
- **Números separados do texto**: em vez de "8 dias seguidos" como uma frase só, agora é `8` (Space Grotesk, cor do sistema) + `dias seguidos` (Inter, neutro) como dois elementos. Mesma lógica em nível, troféus, XP e % do capítulo. Isso é literalmente o que dá "tratamento especial" ao número — ele não é só maior, é de uma família tipográfica diferente do resto da frase.
- **Corpo do texto com piso de 16px**: `typography.body` subiu de 14 pra 16px. Isso é só pra texto que a pessoa efetivamente LÊ (descrição da missão, texto de exemplo de notificação, subtítulos de tela) — não afeta rótulos pequenos tipo tag ou label de navegação, que são escaneados, não lidos, e continuam menores.
- **Hierarquia do card de missão**: agora é nome da missão (grande, Space Grotesk) > descrição curta (Inter, 16px) > metadados (XP, tempo — menor ainda). Antes era uma frase motivacional genérica ("Vamos continuar sua jornada"); agora é o nome real da missão, que é uma resposta mais direta a "qual é minha próxima missão?".
- **Sistema de troféus**: implementado como o documento descreve — nível usa a cor de XP (nível é XP tornado visível, não um sistema à parte) e troféus usam a cor de conquista (verde), que já existia na paleta pra outras coisas — não precisei inventar cor nova. `StatsBar` foi de "3 conquistas" genérico pra "Troféus" de verdade.
- **"Revisão espaçada" → "Revisão"**: nome mais curto, mesma função.

### Uma coisa que não fiz

Marcos/troféus como uma TELA própria (lista de todos os marcos conquistados, histórico, etc.) — isso é conteúdo suficiente pra merecer uma aba/tela dedicada, não um acréscimo na home. O que entrou aqui foi só a contagem no `StatsBar`, que já é a versão "clean" disso no dashboard. Se quiser essa tela também, é só pedir.

## Sexta rodada — aba Rotina + navegação de verdade

Construí a aba Rotina a partir do que o documento descreve: usuário organiza seus horários, a IA usa isso pra sugerir o melhor momento pras missões. E aproveitei pra ligar a navegação de verdade — antes o `BottomNav` era só visual; agora tocar nas abas realmente troca de tela.

- **`AvailabilityCard` (novo)**: dias da semana + período do dia (manhã/tarde/noite) — o dado bruto que a IA usaria pra sugerir horário. Azul (roadmap/planejamento), consistente com o resto do app.
- **`NotificationCard` (novo)**: liga/desliga, frequência em 3 níveis (Poucas/Moderadas/Frequentes — nunca um número exato, é isso que "limitada em frequência" pede), horário de não perturbe, e um exemplo real do tom da notificação — pra provar visualmente que o texto não usa culpa ("Sua missão de hoje tá te esperando 👋", não "Você esqueceu de novo?").
- **`MonthHeatmap` (novo)**: a mesma ideia de consistência do streak, só que no mês inteiro — calendário real (não um heatmap abstrato), com um pontinho laranja (cor do streak) nos dias com missão concluída. Resolve o "organizar o mês" que você mencionou lá atrás.
- **Navegação de verdade**: `activeTab` e o `BottomNav` saíram de dentro do `DashboardScreen` e subiram pro `App.tsx` — agora existe um frame só (SafeAreaView + BottomNav) compartilhado pelas 4 abas, e cada tela (`DashboardScreen`, `RotinaScreen`, e um `ComingSoonScreen` genérico pras 2 abas que ainda não foram construídas) é só o conteúdo. Continua sem depender de React Navigation ou Expo Router — troque por uma dessas bibliotecas quando for integrar de verdade; as telas em si não precisam mudar.
- **Nenhuma cor nova**: tudo usa os tokens que já existiam (`primary`, `streak`, `textPrimary`, etc.) — nada disso precisou de novo teste de contraste.

## Quinta rodada — corrigindo de novo: são roadmaps, não capítulos

Na rodada passada eu modelei "Sua jornada" como os capítulos de UM roadmap (concluído/atual/bloqueado). Errado — a ideia é uma pessoa poder ter mais de um roadmap ativo ao mesmo tempo (um objetivo = um roadmap), cada um com sua própria missão do dia. A home destaca uma missão (a do roadmap em foco) e mostra as dos outros roadmaps embaixo.

- **`RoadmapCard` (novo, substitui `ChapterCard`)**: cada card é outro roadmap ativo + a missão de HOJE daquele roadmap — não capítulos de um só roadmap. Hierarquia invertida em relação ao `CourseCard` original: a missão agora é o texto em destaque (negrito, maior), o nome do roadmap é só o rótulo pequeno acima — porque "a missão é sempre o elemento mais importante", mesmo nesses cards secundários.
- **Cor unificada, não uma por roadmap**: todo `RoadmapCard` usa o mesmo azul (que já significa "roadmap" em todo o app), em vez de uma cor diferente por assunto como antes. Os cards se diferenciam pelo ícone e pelo texto, não pela cor — mais consistente com "uma cor, um significado" e com "nada depende só da cor".
- **Paleta**: mantive a que já tinha (testada, cada sistema com uma cor só), mas sem seguir os tons literais do documento à risca — você disse que eu tenho liberdade aí, e os que escolhi já cobrem o princípio. Se quiser outra direção de cor, é só pedir.

## Quarta rodada — alinhado à essência do produto

Reescrita a partir do documento de essência do Roadmap AI que você mandou. Duas coisas motivaram isso: o app é "um roadmap → capítulos → missões" (não vários cursos paralelos, como eu tinha modelado antes), e a paleta de cor já vem definida no próprio produto — eu não deveria ter inventado uma.

- **Paleta agora é a do produto**: 🔵 azul = roadmap/planejamento (também virou a cor de marca — faz sentido, já que o produto inteiro gira em torno do roadmap), 🟡 amarelo = XP/recompensa, 🟠 laranja = streak/consistência, 🟣 roxo = revisões/conhecimento (antes eu tinha deixado neutro — agora tem cor própria), 🟢 verde = conquista/objetivo concluído. Contraste recalculado do zero pras cores novas, documentado em `colors.ts`.
- **`ChapterCard` (novo, substitui `CourseCard`)**: "Crescendo aos poucos" virou "Sua jornada" — mostra os capítulos do MESMO roadmap da missão em destaque (concluído / atual / bloqueado), não roadmaps diferentes. É a correção definitiva da duplicação da rodada passada: agora só existe um roadmap na tela, e essa seção é o mapa dele.
- **`ReviewCard` (novo, substitui `TodayItem`)**: revisão espaçada ganhou a cor roxa própria do sistema, em vez do cinza neutro genérico.
- **Sem número de XP no topo**: `StatsBar` ficou só com Nível e Conquistas. O documento é explícito — "o foco não é acumular pontos, o foco é mostrar evolução" — então XP aparece como recompensa pontual no card da missão (onde já estava), não como total fixo disputando atenção lá em cima.
- **Mensagem da missão mais calma**: troquei "Bora pra missão de hoje! 👀" por "Vamos continuar sua jornada" — o documento pede "calma, clareza, progresso" e reforça que nada deve competir com a missão; tom de mentor combina mais com isso do que energia de torcida.

## O que mudou nesta rodada

- **Cor com significado único**: cada cor tem um job só e nunca é reaproveitada — roxo (marca/navegação), verde (ação positiva), laranja (streak), âmbar (XP), azul/verde-água (categorias de trilha). Nível e badges ficaram neutros (cinza) de propósito: são estatísticas de perfil, não mecânicas centrais, então não competem pelas cores reservadas. Ver os comentários em `src/theme/colors.ts`.
- **Contraste testado, não estimado**: rodei um script WCAG (luminância relativa → razão de contraste) em cada par texto/fundo e ícone/fundo realmente usado no app. Vários valores originais falhavam (laranja e âmbar em particular, ~2:1) — todos foram escurecidos até passar. Texto normal ≥ 4.5:1, ícones/gráficos ≥ 3:1. Os números ficaram documentados como comentário ao lado de cada cor.
- **Nenhuma informação só por cor**: streak = ícone de chama + número; XP = ícone de raio + número; trilha ativa no menu = ícone preenchido + negrito, não só a cor; link "Ver todos" ganhou uma setinha.
- **Espaçamento em grid de 8px**: `spacing` agora tem 4 valores só (8/16/24/32), e todo padding/margin/gap do app usa um deles — sem exceção, sem "12" ou "14" soltos.
- **Áreas tocáveis ≥ 44px**: itens do menu inferior e botão da missão têm `minHeight: 48`; o link "Ver todos" ganhou `hitSlop` pra compensar o texto pequeno.
- **Progresso por % do capítulo**: o card de missão mostra uma barra + "% do capítulo" — sem fração de missão (nem "3/5"), pra não ler como uma contagem regressiva de trabalho restante.
- **Proteção de streak visível**: `StreakProgress` mostra um selo de "proteções" disponíveis, deixando claro que uma falha ocasional não zera tudo.
- **Curto prazo + longo prazo juntos**: o streak mostra o número de dias seguidos (curto prazo) E uma barra até a próxima meta grande, tipo 30 dias (longo prazo), no mesmo componente.
- **Mensagem sem culpa**: troquei "Vá estudar seu vagabundo!" por "Bora pra missão de hoje! 👀" — mantém a energia informal, tira o tom de deboche.
- **Bottom nav não fica mais em cima dos botões do Android**: usa `useSafeAreaInsets()` de verdade agora (ver nota sobre `react-native-safe-area-context` abaixo).

## Terceira rodada — corrigindo uma duplicação

"Vocabulário rápido" (item da rodada anterior) e os cards de "Crescendo aos poucos" eram, na prática, a mesma coisa: cada card de trilha já é "roadmap + missão daquele roadmap para hoje" (`title` = nome do roadmap, `subtitle` = missão específica de hoje — não é uma descrição genérica de curso). Mostrar isso duas vezes, em duas seções diferentes, é inconsistente e confuso.

Resultado: `TodayItem` agora aparece uma vez só, com a Revisão espaçada (que é, de fato, uma mecânica à parte — não pertence a um roadmap específico). Sem cabeçalho de seção nem "Ver todos" próprio: é uma linha só, autoexplicativa, e tocar nela leva direto pra fila de revisões.

## Segunda rodada

- **`TodayItem` (novo)**: linha compacta e neutra pra sinalizar algo do dia que não é uma missão de roadmap. Ver correção na seção acima — a versão com 2 itens (revisão + "outra missão") foi simplificada depois por duplicar o que já aparece em "Crescendo aos poucos".
- **Sem "criar novo roadmap" no dashboard**: cogitado e descartado — é uma ação grande e pouco frequente (configuração), não algo do dia a dia. Faz mais sentido dentro da aba Objetivos do que competindo por espaço aqui.
- **Notificações e organização de dia/mês**: ficam pra aba Rotina (já existe no menu inferior) — o dashboard continua sendo só "o que fazer agora".

### O que ficou de fora (não é código de tela)

Três itens da lista são regras de produto/conteúdo/backend, não algo que um componente de tela resolve sozinho — sinalizando aqui pra não fingir que "implementei" algo que na verdade depende de outra camada:
- **Missão do dia 1 fácil**: é uma decisão de quem escreve o currículo/conteúdo das missões, não do componente `MissionCard`. O componente aceita qualquer `chapterProgress`/`message`; a dificuldade real da missão 1 é uma escolha de conteúdo.
- **Notificações por comportamento, personalizadas por horário, limitadas em frequência**: isso é um sistema de notificação (trigger + agendamento + backend), fora do escopo de uma tela. Se quiser, te ajudo a desenhar isso separadamente.
- **Sem culpa/vergonha em notificações**: mesma dependência — só dá pra garantir isso no texto do `MissionCard` (já ajustado) e, quando for escrever as notificações de verdade, seguir o mesmo princípio.

## Estrutura

```
index.ts                          → entrada real do app (registra o App.tsx)
App.tsx                           → raiz — QueryClient, fontes, SafeAreaProvider, AuthProvider, troca de aba
src/
  theme/colors.ts                 → tokens: cor (paleta mural + caderno, contraste documentado), espaçamento (grid 8px), tipografia
  context/
    AuthContext.tsx                  → sessão (token no SecureStore) + estado checking/authenticated/unauthenticated
  navigation/
    AuthFlow.tsx                     → login/registro pra quem não está autenticado
    OnboardingFlow.tsx                 → cria o primeiro objetivo pra quem ainda não tem nenhum
  services/                        → uma função por chamada de API; nada de estado, só `api.ts` (axios) + tipos
    api.ts, authService.ts, authStorage.ts, userService.ts, goalService.ts,
    roadmapService.ts, knowledgeService.ts, reminderService.ts, calendarEventService.ts
  hooks/                           → react-query em cima dos services (queries + mutations com invalidation)
    useDashboard.ts, useObjetivos.ts, useAgenda.ts
  utils/
    dateUtils.ts                     → conversões de hora/data usadas em Início e Rotina
    journeyMapLayout.ts                → geometria do mapa de aventura da aba Objetivos (puro, sem RN/SVG)
    chapterVisuals.ts                    → ícone determinístico por capítulo (usado no mapa e no detalhe)
  components/
    WoodBackground.tsx               → textura de madeira/cortiça (aba Início/Rotina)
    DeskBackground.tsx, DeskProps.tsx   → mesa de estudos (telas de autenticação/onboarding)
    PushPin.tsx, WashiTape.tsx             → alfinete / fita decorativos (Views puras, sem SVG)
    NotebookBackground.tsx                   → papel pautado + margem + furos (aba Objetivos)
    AgendaBackground.tsx                       → fundo da aba Rotina
    HomeHeader.tsx                    → avatar + saudação + streak/nível + sino (Início)
    MissionCard.tsx                     → card de missão em destaque (hero)
    StreakProgress.tsx                    → streak + proteção + meta de longo prazo
    StudyReminder.tsx                       → faixa "Hoje às [hora] — [sessão]"
    ReviewCard.tsx                            → linha de revisão no dashboard (cor roxa própria)
    MilestoneCard.tsx                           → "Próximo Marco" — nome, %, missões, recompensa em XP
    RoadmapCard.tsx                               → outro roadmap ativo + a missão dele para hoje
    BottomNav.tsx                     → nav inferior, com inset de área segura do Android
    JourneyPath.tsx                     → mapa de aventura a grafite da aba Objetivos (react-native-svg)
    ReviewPostIt.tsx                      → gatilho de revisão (pilha de post-its, 1–3 camadas)
    FlashcardReview.tsx                     → sessão de revisão de verdade (Again/Difícil/Médio/Fácil)
    CelebrationBurst.tsx                      → confete reutilizável pra momentos de conclusão
    NotepadCard.tsx                   → bloquinho usado no fluxo de criar objetivo/onboarding
    AuthButton.tsx, AuthTextField.tsx   → controles das telas de login/registro
    WeekStrip.tsx, DayTimeline.tsx, AgendaEventCard.tsx,
    MonthCalendarPicker.tsx, NewCompromissoModal.tsx, UpcomingChip.tsx
                                       → aba Rotina (semana, linha do tempo do dia, criar compromisso)
  screens/
    DashboardScreen.tsx              → conteúdo da aba Início
    RotinaScreen.tsx                   → conteúdo da aba Rotina
    ObjetivosScreen.tsx                  → conteúdo da aba Objetivos (marcadores + mapa + revisões)
    ChapterDetailScreen.tsx                → página do capítulo: missões, progresso, editar/apagar
    GoalIntakeScreen.tsx               → criar um objetivo novo (descrição pra IA gerar o roadmap)
    GoalProcessingScreen.tsx             → espera a IA terminar de gerar o roadmap
    LoginScreen.tsx, RegisterScreen.tsx   → autenticação
    ComingSoonScreen.tsx               → placeholder genérico (Comunidade)
```

## Rodando localmente

1. `npm install`.
2. Copie `.env.example` pra `.env` e ajuste `EXPO_PUBLIC_API_URL` pro endereço do seu backend (emulador Android, celular físico, ou servidor publicado — o `.env.example` tem um exemplo de cada). Sem esse arquivo, o app cai no IP de fallback hardcoded em `src/services/api.ts`, que quase certamente não é o seu.
3. `npx expo start` (ou `npx expo run:ios` / `run:android` se precisar reconstruir o dev client — só necessário se alguma dependência NATIVA mudar; nenhuma mudou nesta rodada).

## Notas

- **Área segura do Android**: `BottomNav` lê `useSafeAreaInsets()` (do `react-native-safe-area-context`) e soma isso ao padding inferior — por isso o `App.tsx` precisa estar dentro de um `SafeAreaProvider` (já está).
- **`.env` nunca é commitado** (`.gitignore` cobre isso) — só o `.env.example` é versionado, como referência.
- **`expo-secure-store` estava travado numa versão (`~14.0.4`) que não existe no npm** — o `npm install` falhava direto pra qualquer pessoa clonando o projeto do zero. Corrigido pra `~15.0.8` (a versão que o próprio Expo SDK 54.0.36 declara como compatível — conferido via `bundledNativeModules.json` do pacote `expo`, não chute).
- Todo o projeto foi validado com `tsc --noEmit` sem erros e com `npx expo export` (bundle real via Metro, 936 módulos) antes da entrega.