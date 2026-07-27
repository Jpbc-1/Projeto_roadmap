# Dashboard — redesign

Tela inicial redesenhada em React Native + Expo + TypeScript.

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
index.ts                       → entrada real do app (registra o App.tsx)
App.tsx                        → raiz — SafeAreaProvider + WoodBackground + o frame único (SafeAreaView + BottomNav) + troca de aba
src/
  theme/colors.ts              → tokens: cor (paleta mural, contraste documentado — inclui primary vs primaryText, ver acima), espaçamento (grid 8px), tipografia
  components/
    WoodBackground.tsx           → textura de madeira/cortiça visível (gradientes + respingos + vinheta)
    PushPin.tsx                    → alfinete decorativo (Views puras, sem SVG)
    WashiTape.tsx                    → fita decorativa (View rotacionada translúcida)
    HomeHeader.tsx                   → avatar (emoji ou foto) + saudação + streak/nível + sino
    MissionCard.tsx                    → card de missão (hero): dificuldade, % do capítulo, nome, descrição, XP/tempo
    StreakProgress.tsx                   → streak + proteção + meta de longo prazo
    StudyReminder.tsx                      → faixa "Hoje às [hora] — [sessão]"
    ReviewCard.tsx                           → linha de revisão (cor roxa própria)
    MilestoneCard.tsx                          → "Próximo Marco" — nome, %, missões, recompensa em XP
    RoadmapCard.tsx                              → outro roadmap ativo + a missão dele para hoje (largura total)
    AvailabilityCard.tsx                           → dias da semana + período preferido (aba Rotina)
    NotificationCard.tsx                             → liga/desliga, frequência, não perturbe (aba Rotina)
    MonthHeatmap.tsx                                   → calendário de consistência do mês (aba Rotina)
    BottomNav.tsx                                        → nav inferior, com inset de área segura do Android
    NotebookBackground.tsx                                 → papel pautado + margem + furos (fundo da aba Objetivos)
    RoadmapSketch.tsx                                        → roadmap desenhado a lápis, via react-native-svg
    ReviewStack.tsx                                            → prévia da revisão (pilha de post-its)
    FlashcardReview.tsx                                          → revisão de verdade: carta + Again/Difícil/Médio/Fácil
  screens/
    DashboardScreen.tsx             → conteúdo da aba Início — envolve tudo em WoodBackground
    RotinaScreen.tsx                  → conteúdo da aba Rotina — também em WoodBackground
    ObjetivosScreen.tsx                → conteúdo da aba Objetivos — em NotebookBackground
    ComingSoonScreen.tsx               → placeholder genérico (só Comunidade agora)
```

## Integrar na sua pasta frontend-mobile

1. Substitua os arquivos equivalentes pelos desta entrega (mesmos caminhos).
2. Instale as dependências novas: `npx expo install react-native-svg`. `expo-font`, `@expo-google-fonts/space-grotesk`, `@expo-google-fonts/inter`, `react-native-safe-area-context`, `expo-linear-gradient` e `@expo/vector-icons` já deviam estar instalados de entregas anteriores.
3. Os dados (nível, XP, streak, missão) continuam hardcoded no `DashboardScreen` — troque pelos dados da sua API/estado quando integrar de verdade.

## Notas

- **Área segura do Android**: `BottomNav` agora lê `useSafeAreaInsets()` (do `react-native-safe-area-context`) e soma isso ao padding inferior — por isso o `App.tsx` precisa estar dentro de um `SafeAreaProvider` (já está). Isso resolve o menu ficando em cima dos botões/gestos do Android, e se ajusta sozinho em qualquer aparelho.
- **Versões**: `package.json` fixado no Expo SDK 54, pra bater com a versão que já tá instalada no seu celular (client 54.0.8). Quando o Expo Go do celular atualizar sozinho pra um SDK novo, rode `npx expo install expo@latest --fix` pra realinhar o projeto.
- Todo o projeto foi validado com `tsc --noEmit` sem erros antes da entrega.
