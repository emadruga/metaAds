# Solicitação de Expansão de Escopos — Meta App Review
**Aplicativo:** MetaAds Intelligence (metads.app)
**Data:** 2026-03-12
**Propósito geral do app:** Plataforma SaaS de inteligência competitiva para análise de anúncios veiculados na Meta Ads Library. Permite que anunciantes e profissionais de marketing monitorem estratégias de concorrentes, identifiquem padrões vencedores de copy e criativo, e tomem decisões de campanha baseadas em dados públicos disponíveis na Meta Ads Library.

---

## 1. `business_management`

### Análise da política
`business_management` fornece acesso à API do Business Manager, incluindo resolução de ativos de negócios e autenticação de conta. A Meta exige uso restrito à gestão legítima de negócios do usuário autenticado.

### Como o app usa essa permissão
`business_management` é a permissão que habilita o MetaAds Intelligence a receber resultados reais do endpoint `/ads_archive` da Graph API. Sem esse escopo, chamadas autenticadas ao endpoint retornam `{"data": []}` — mesmo com `ads_read` presente — comportamento amplamente documentado pela comunidade de desenvolvedores Meta.

O uso específico inclui:

1. **Acesso completo à Meta Ads Library via `/ads_archive`**: permite executar buscas por `search_terms` e `search_page_ids` e receber resultados populados. Sem `business_management`, o endpoint retorna array vazio independentemente dos parâmetros;
2. **Resolução de `page_id` a partir de username de página**: o app usa `GET /{page-username}?fields=id` para converter nomes de anunciantes em IDs numéricos — necessário para a estratégia `search_page_ids`, que retorna 100% dos anúncios de um anunciante específico (muito mais precisa que `search_terms`, que só encontra anúncios cujo copy menciona o termo buscado);
3. **Validação de token antes de cada ciclo de coleta**: o app verifica `GET /me?fields=id,name` para confirmar que o token ativo é válido antes de disparar uma coleta automática periódica, evitando ciclos de falha silenciosa.

### Experiência do usuário (ponta a ponta)
1. Usuário cria conta no metads.app e conecta sua conta Facebook via OAuth com o escopo `business_management`;
2. O app confirma token válido com `GET /me` e exibe o nome da conta conectada no painel;
3. Usuário cria um nicho de análise (ex.: "editores de vídeo com IA") e adiciona palavras-chave de concorrentes;
4. Ao disparar uma coleta, o app chama `GET /ads_archive?search_terms=OpusClip&ad_reached_countries=US&fields=...` e recebe anúncios reais;
5. O painel exibe os anúncios coletados com métricas de longevidade, CTAs detectados e padrões de copy;
6. Uma coleta automática é disparada a cada 3 horas via EventBridge, mantendo o repositório atualizado.

### Chamadas de API de teste realizadas
```
GET /me?fields=id,name
GET /ads_archive?search_terms=video+editor+ai&ad_reached_countries=US&ad_active_status=ALL
  &fields=id,page_name,ad_creative_bodies,ad_creative_link_titles,
          ad_delivery_start_time,ad_delivery_stop_time,platforms,ad_snapshot_url
  &limit=50
GET /{page-username}?fields=id,name
```

### Você concorda que está em conformidade com o uso permitido?
✅ **Sim.** O escopo `business_management` é utilizado exclusivamente para habilitar o acesso à Meta Ads Library (repositório público de anúncios), validar o token do usuário autenticado e resolver IDs de páginas públicas. Nenhum dado de Business Manager de terceiros é acessado. Todos os dados coletados são provenientes do repositório público da Meta Ads Library e armazenados exclusivamente para uso do próprio usuário autenticado.

---

### 🎬 Script do Screencast — `business_management`

> **Duração alvo:** 2–3 minutos
> **Ferramenta sugerida:** Loom, QuickTime + OBS, ou Screen Studio
> **Resolução mínima:** 1280×720. Prefira 1920×1080.
> **Narração:** Obrigatória em inglês (pode ser legendada). Fale devagar e em voz alta.
> **Importante:** Mostre a URL do navegador em todos os momentos. Não corte telas abruptamente.

---

#### ⚠️ PRÉ-REQUISITO OBRIGATÓRIO ANTES DE GRAVAR

**Você ainda não tem `business_management` aprovado — e é exatamente por isso que está submetendo este review.** O vídeo deve demonstrar o que o app *fará* com a permissão quando aprovada. Para isso, a Meta fornece o mecanismo de **Test Users** do Facebook App Dashboard, que permite usar qualquer escopo solicitado antes da aprovação.

**Passos obrigatórios antes de ligar o gravador:**

**Passo 1 — Adicionar `business_management` ao OAuth do app**

No Clerk Dashboard → SSO Connections → Facebook → editar os escopos solicitados. Adicione `business_management` à lista. Sem isso, o diálogo OAuth não vai mostrar a permissão.

Alternativamente, se o OAuth é configurado diretamente no código, garanta que o parâmetro `scope` da URL de autorização inclua `business_management`:
```
scope=public_profile,ads_read,business_management
```

**Passo 2 — Criar um Test User no Facebook App Dashboard**

1. Acesse `https://developers.facebook.com/apps/{seu-app-id}/roles/test-users/`
2. Clique em **"Add"** → crie um test user (ex.: `Test User 1`)
3. Clique em **"Edit"** → **"Get an access token for this test user"**
4. Na janela que abre, **marque `business_management` e `ads_read`** → confirme
5. Copie o access token gerado — ele tem `business_management` concedido mesmo sem aprovação

**Passo 3 — Configurar o token no Secrets Manager para o teste**
```bash
aws secretsmanager put-secret-value \
  --profile metads --region us-east-1 \
  --secret-id metaads/dev/meta-api \
  --secret-string '{"access_token": "TOKEN_DO_TEST_USER_AQUI"}'
```

**Passo 4 — Fazer login no app com o test user**

Na tela de login do metads.app, use "Continue with Facebook" e entre com as credenciais do test user criado. O OAuth mostrará `business_management` na lista de permissões e o concederá ao confirmar.

**Por que isso funciona:** Test users são uma feature oficial do Meta Developer Platform. Permissões não aprovadas funcionam normalmente para test users — é o ambiente de desenvolvimento/staging que a Meta disponibiliza para exatamente esse propósito (gravar demos, testar integrações, submeter reviews).

---

#### CENA 1 — Contexto: o que é o app (0:00–0:20)

**O que mostrar na tela:**
- Abra o browser em `https://metads.app`
- A landing page do app deve estar visível

**Narração:**
> "This is MetaAds Intelligence — a competitive analysis platform for digital marketers. It lets users monitor competitor ads from Meta's public Ad Library. I'll now demonstrate how the app uses the `business_management` permission."

---

#### CENA 2 — Fluxo de login OAuth com `business_management` visível (0:20–0:55)

**O que mostrar na tela:**
1. Clique em "Sign In" / "Get Started"
2. A tela de login do Clerk aparece — clique em "Continue with Facebook"
3. **A janela de consentimento OAuth do Facebook abre**
   - Pause 2–3 segundos aqui — esta é a cena mais importante para o revisor
   - O diálogo deve listar `business_management` entre as permissões solicitadas
   - Role a tela se necessário para mostrar a lista completa
4. Clique em "Continue" / "Allow"
5. O browser redireciona para o painel do app já autenticado

**Narração:**
> "The user signs in with Facebook. The standard Meta OAuth consent dialog appears, listing the permissions the app requests — including `business_management`. The user reviews and approves. They are redirected back to the app."

---

#### CENA 3 — Validação do token no painel (0:55–1:15)

**O que mostrar na tela:**
1. O painel principal do MetaAds é exibido após o login
2. Aponte com o cursor para o nome do usuário logado
3. Abra o DevTools (F12) → aba Console ou Network e mostre uma chamada `GET /me` com resposta `200 OK` contendo `id` e `name`

**Narração:**
> "After login, the app calls `GET /me` using the `business_management` scope to validate the token and confirm the connected account. This runs before every automatic collection cycle to prevent silent failures."

---

#### CENA 4 — Criar nicho e disparar coleta (1:15–2:00)

**O que mostrar na tela:**
1. Clique em "Criar Nicho"
2. Preencha nome: `"AI Video Editors"` e palavras-chave: `OpusClip`, `video editing ai`
3. Salve — o nicho aparece na lista
4. Entre no nicho e clique em **"Coletar agora"**
5. Loading por 3–5 segundos
6. Anúncios aparecem: cards com nome de anunciante, copy, data de início

**Narração:**
> "The user creates a competitive niche with keywords to monitor. Clicking 'Collect now' triggers a call to `GET /ads_archive`. With `business_management` granted, the API returns real ad data — without it, the same call returns an empty array."

---

#### CENA 5 — Mostrar o JSON da resposta no DevTools (2:00–2:25)

**O que mostrar na tela:**
1. Abra DevTools → aba Network
2. Dispare uma nova coleta
3. Localize a requisição para o seu API Gateway
4. Clique nela e mostre a response: `{"data": [...]}` com anúncios reais dentro

**Narração:**
> "In the network tab, we can see the API call returning real ad data in the `data` array. This is the key behavior enabled by `business_management` — without this permission, this array is empty."

---

#### CENA 6 — Encerramento (2:25–2:45)

**O que mostrar na tela:**
- Lista de anúncios coletados, rolando devagar
- Nomes de páginas reais visíveis (OpusClip, Descript etc.)

**Narração:**
> "All data displayed comes exclusively from Meta's public Ad Library — identical to what's visible at facebook.com/ads/library. The `business_management` permission is used solely to authenticate API calls and receive non-empty responses. No private business data of third parties is accessed at any point."

---

#### Checklist antes de gravar
- [ ] `business_management` adicionado aos escopos solicitados no OAuth do app
- [ ] Test user criado no Facebook App Dashboard com `business_management` + `ads_read` concedidos
- [ ] Token do test user configurado no Secrets Manager (`metaads/dev/meta-api`)
- [ ] Nicho vazio preparado para mostrar coleta do zero
- [ ] DevTools aberto e pronto para mostrar a chamada de API e resposta JSON
- [ ] Browser em tela cheia, sem outras abas abertas
- [ ] URL `metads.app` visível em todos os momentos
- [ ] Narração em inglês, clara, sem ruído de fundo
- [ ] MP4 (H.264), máximo 100 MB

---

## 2. `ads_read`

### Análise da política
`ads_read` permite leitura de dados de anúncios e campanhas. A Meta exige que seja usado para análise e relatórios em benefício do anunciante autenticado ou com autorização explícita de clientes.

### Como o app usa essa permissão
`ads_read` é o escopo que autoriza a leitura dos campos de anúncios retornados pelo endpoint `/ads_archive`. Enquanto `business_management` desbloqueia o retorno de resultados não-vazios, `ads_read` garante que os campos de conteúdo dos anúncios (copy, datas, plataformas) sejam incluídos na resposta.

O uso específico inclui:

1. **Coleta de anúncios públicos da Meta Ads Library**: o app busca anúncios por palavra-chave (`search_terms`) e por ID de página anunciante (`search_page_ids`), recuperando campos como `ad_creative_bodies`, `ad_creative_link_titles`, `ad_creative_link_descriptions`, `ad_delivery_start_time`, `ad_delivery_stop_time`, `platforms` e `ad_snapshot_url`;
2. **Cálculo de longevidade**: comparando `ad_delivery_start_time` com `ad_delivery_stop_time` (ou a ausência deste, indicando anúncio ainda ativo), o app calcula há quantos dias cada anúncio está sendo veiculado — o principal proxy público de performance disponível na Ads Library;
3. **Análise de padrões**: o app agrega dados de centenas de anúncios coletados para identificar CTAs mais frequentes, comprimento médio de copy, uso de emoji, hashtags predominantes e formatos de criativo mais comuns no nicho monitorado;
4. **Monitoramento contínuo**: coletas periódicas automáticas (a cada 3 horas) detectam novos anúncios de concorrentes e atualizam o status dos anúncios já conhecidos (ativo → inativo).

### Experiência do usuário (ponta a ponta)
1. Usuário configura um nicho com palavras-chave (ex.: "OpusClip", "Descript", "ai video editor");
2. Clica em "Coletar agora" ou aguarda a próxima coleta automática;
3. O app chama `/ads_archive` com `ads_read` e exibe os resultados na aba "Busca";
4. Anúncios com 30+ dias de veiculação contínua são destacados como "Top Performers";
5. A aba "Análise" exibe um resumo: CTAs mais usados, comprimento médio de copy, % de anúncios com emoji;
6. Anúncios específicos podem ser salvos em favoritos para referência futura.

### Chamadas de API de teste realizadas
```
GET /ads_archive?search_terms=OpusClip&ad_reached_countries=US&ad_active_status=ALL
  &fields=id,page_name,ad_creative_bodies,ad_creative_link_titles,
          ad_delivery_start_time,ad_delivery_stop_time,platforms,ad_snapshot_url
  &limit=50

GET /ads_archive?search_page_ids=107169124782693&ad_reached_countries=US
  &fields=id,ad_creative_bodies,ad_delivery_start_time,ad_delivery_stop_time
  &limit=100
```

### Você concorda que está em conformidade com o uso permitido?
✅ **Sim.** O app acessa exclusivamente dados públicos da Meta Ads Library — informações que qualquer pessoa pode ver manualmente em facebook.com/ads/library. Nenhum dado privado de campanhas de terceiros é acessado. O acesso é feito via token do próprio usuário autenticado, que consente explicitamente ao conectar sua conta. Os dados coletados são armazenados no banco de dados privado do usuário e nunca compartilhados com terceiros.

---

### 🎬 Script do Screencast — `ads_read`

> **Duração alvo:** 2–3 minutos
> **Este vídeo é diferente do anterior:** enquanto o vídeo de `business_management` foca no fluxo de autenticação e na chamada à API, este deve focar nos **dados retornados e em como o usuário os utiliza** para análise competitiva.
> **Pré-requisito para gravação:** Tenha pelo menos 10–20 anúncios já coletados no nicho de demonstração para que os dados apareçam imediatamente.

---

#### CENA 1 — Contextualização rápida do app (0:00–0:15)

**O que mostrar na tela:**
- App aberto em `https://metads.app` já logado
- O painel com a lista de nichos visível

**Narração:**
> "MetaAds Intelligence uses the `ads_read` permission to read ad content from Meta's public Ad Library. I'll demonstrate how the collected ad data is displayed and used by the user."

---

#### CENA 2 — Entrar no nicho e mostrar aba de busca com anúncios coletados (0:15–0:50)

**O que mostrar na tela:**
1. Clique em um nicho existente (ex.: `"AI Video Editors"`)
2. A aba **"Search"** (ou "Busca") é exibida com uma lista de anúncios coletados
3. Role devagar a lista — o revisor precisa ver:
   - **Nome do anunciante** (page_name) em cada card
   - **Texto do anúncio** (ad_creative_bodies) — copy real do anúncio
   - **Data de início** (ad_delivery_start_time) — mostrando há quantos dias está ativo
   - **Plataformas** onde o anúncio veicula (Instagram, Facebook etc.)
4. Pause em 2–3 cards individuais para que o revisor leia o conteúdo

**Narração:**
> "Here we can see ads collected from the Meta Ads Library for this niche. Each card shows the advertiser's page name, the ad copy text, when it started running, and which platforms it's active on. All of this comes from the public `ads_archive` endpoint, using the `ads_read` permission."

---

#### CENA 3 — Mostrar um anúncio individual em detalhe (0:50–1:20)

**O que mostrar na tela:**
1. Clique em um anúncio específico para abrir o painel de detalhe
2. Mostre claramente os campos:
   - **Headline / título** do anúncio
   - **Corpo do texto** (copy completo)
   - **CTA detectado** (ex.: "Learn More", "Sign Up")
   - **Dias ativo** calculado pelo app (ex.: "47 days running")
   - **Link para o snapshot** na Ads Library original
3. Se houver botão "Ver na Ads Library", clique nele — isso abre `facebook.com/ads/library` com o anúncio original, **provando que o dado é público**

**Narração:**
> "Clicking on an individual ad shows full details: the ad copy, detected call-to-action, how many days it has been running, and a direct link back to Meta's own Ad Library page for this ad. This confirms all data is publicly available — `ads_read` simply enables the app to retrieve it programmatically."

**⚠️ Esta cena é crucial:** abrir o snapshot original na Ads Library do Facebook demonstra ao revisor que os dados são públicos, não privados.

---

#### CENA 4 — Filtros de busca (1:20–1:45)

**O que mostrar na tela:**
1. De volta à lista de anúncios, use os filtros disponíveis:
   - Filtre por **status: Ativo**
   - Filtre ou ordene por **"Mais longevos primeiro"** (anúncios rodando há mais dias)
2. A lista se atualiza mostrando apenas anúncios ativos, ordenados por dias de veiculação
3. Aponte para o anúncio no topo: "X dias ativo" — esse é o valor de inteligência central do app

**Narração:**
> "The user can filter by active ads and sort by longevity — how many days each ad has been running. Ads that run for 30+ days are a strong signal of performance. This insight is only possible because `ads_read` provides access to the start and stop dates for each ad."

---

#### CENA 5 — Salvar um anúncio em favoritos (1:45–2:00)

**O que mostrar na tela:**
1. Clique no botão de salvar/favoritar em um anúncio de destaque
2. Navegue para a aba **"Saved"** (ou "Salvos")
3. O anúncio aparece na lista de salvos

**Narração:**
> "Users can save specific ads for future reference — building a personal swipe file of high-performing competitor ads to use as creative inspiration."

---

#### CENA 6 — Histórico de coletas (2:00–2:20)

**O que mostrar na tela:**
1. Navegue para a aba **"History"** (ou "Histórico") dentro do nicho
2. Mostre a lista de coletas passadas com: data/hora, número de anúncios encontrados, status (sucesso/falha)
3. Aponte para uma coleta recente — mostra que o sistema coleta automaticamente a cada 3 horas

**Narração:**
> "The History tab shows all past collection runs. The app collects automatically every 3 hours, keeping the competitor ad database up to date. Each run uses `ads_read` to fetch the latest ads from the Meta Ads Archive."

---

#### CENA 7 — Comparação com facebook.com/ads/library (2:20–2:45)

**O que mostrar na tela:**
1. Abra uma nova aba do browser em `https://www.facebook.com/ads/library`
2. Digite o mesmo termo de busca usado no app (ex.: "OpusClip")
3. Os mesmos anúncios aparecem na Ads Library oficial do Facebook
4. Volte para o MetaAds e mostre o mesmo anúncio lado a lado (ou em sequência rápida)

**Narração:**
> "To make it clear: here is Meta's own Ad Library at facebook.com/ads/library. Searching for the same keyword shows the same ads. MetaAds Intelligence uses `ads_read` to access this exact same public data programmatically — providing marketers with a structured, searchable database instead of manual browsing."

**⚠️ Esta cena é o argumento mais forte para o revisor.** Ela prova que o app não acessa nada que não seja já público.

---

#### Checklist antes de gravar
- [ ] Nicho com 15–30 anúncios já coletados (para que a lista apareça cheia desde o início)
- [ ] Pelo menos um anúncio com 30+ dias de veiculação visível
- [ ] Snapshot de anúncio abre corretamente no `facebook.com/ads/library` ao clicar
- [ ] Aba "Saved" com ao menos 1 anúncio salvo previamente
- [ ] Aba "History" com ao menos 2–3 coletas registradas
- [ ] `facebook.com/ads/library` funcionando no browser para a cena de comparação
- [ ] Narração em inglês, clara e sem ruído
- [ ] MP4 (H.264), máximo 100 MB

---

#### Dica geral para os dois vídeos

Os revisores da Meta verificam principalmente:
1. **O app existe de verdade** e tem UI funcional (não é só um script de API)
2. **O usuário consente explicitamente** no fluxo OAuth
3. **Os dados são usados para o propósito declarado** (análise competitiva de dados públicos)
4. **Nenhum dado privado de terceiros** é exposto ou armazenado

Gravar os dois vídeos separados (um para cada escopo) é obrigatório quando a Meta pede individualmente — não tente reutilizar o mesmo vídeo para os dois.

---

## 3. `public_profile`

### Análise da política
`public_profile` é uma permissão padrão que fornece acesso às informações básicas do perfil público do usuário (nome, foto de perfil, ID). É concedida automaticamente a todos os apps e exigida para qualquer fluxo de autenticação OAuth com o Facebook.

### Como o app usa essa permissão
O MetaAds Intelligence usa `public_profile` exclusivamente para:

1. **Autenticação e identificação do usuário**: confirmar que o login OAuth foi bem-sucedido e exibir o nome do usuário no cabeçalho do painel;
2. **Unicidade de conta**: associar o ID público do Facebook ao perfil de usuário no sistema de autenticação (Clerk), garantindo que um mesmo usuário não crie múltiplas contas acidentalmente;
3. **Exibição contextual**: mostrar "Conectado como [Nome]" na tela de configurações de conta, permitindo que o usuário confirme qual conta Facebook está vinculada.

### Você concorda que está em conformidade com o uso permitido?
✅ **Sim.** `public_profile` é usado exclusivamente para autenticação e exibição básica de identidade na interface. Nenhum dado de perfil é armazenado além do ID e nome de exibição, e esses dados nunca são compartilhados com terceiros nem usados para fins comerciais.

---

## Resumo

| Escopo | Função no app | Dados acessados | Ação automática? |
|---|---|---|---|
| `business_management` | Desbloqueia `/ads_archive` + valida token | Ads Library pública + token do usuário | ❌ Nunca |
| `ads_read` | Lê campos dos anúncios coletados | Ads Library pública (dados públicos) | ❌ Nunca |
| `public_profile` | Login OAuth + exibição de nome | Perfil público do usuário | ❌ Nunca |

**Por que apenas esses 3 escopos?**
O MetaAds Intelligence é, em sua versão atual, uma ferramenta de **leitura e análise de dados públicos**. Não cria anúncios, não gerencia campanhas, não acessa leads e não modifica nenhum ativo do usuário. Os 3 escopos acima cobrem exatamente o que o produto faz hoje, sem solicitar permissões além do necessário.

**Compromisso de privacidade:** Todos os dados da Meta acessados são armazenados exclusivamente para benefício do usuário autenticado que os originou. O app não vende, compartilha nem monetiza dados de usuários. Política de Privacidade: https://metads.app/privacy

---

*Documento gerado para submissão no Meta App Review — metads.app*
