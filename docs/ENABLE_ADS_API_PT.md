# Como Habilitar a API de Anúncios - Passo a Passo

## ✅ Você está no lugar certo!

Você encontrou a página correta: **Configurações** → **API de Marketing**

## 📍 Onde você está agora

Você viu esta mensagem (em vermelho no seu screenshot):

```
┌─────────────────────────────────────────────────────────┐
│ Nível de acesso da API de anúncios: Development        │
│                                                         │
│ Requisitos para um nível de acesso mais alto:          │
│ • App must be published                                │
│ • Ads Management Standard Access must be approved      │
│   in App Review                                        │
│                                                         │
│ [Adicione o acesso padrão de gerenciamento de         │
│  anúncios à Análise do App] ← CLIQUE AQUI!            │
└─────────────────────────────────────────────────────────┘
```

## 🎯 PRÓXIMO PASSO

**Clique no link azul:**

👉 **"Adicione o acesso padrão de gerenciamento de anúncios à Análise do App"**

## 📝 O que vai acontecer

Depois de clicar, você será levado para uma página de **App Review** onde precisará:

### 1. Solicitar Permissão "Ads Management Standard Access"

Você verá um formulário pedindo:

#### A. Detalhes do App
```
Nome do app: EWD Marketing API
Tipo: Business
Plataforma: Web/API
```

#### B. Caso de Uso
**Exemplo de texto para usar:**

```
Descrição do Caso de Uso:

Estou desenvolvendo uma ferramenta de análise de inteligência competitiva
que utiliza a API da Biblioteca de Anúncios do Meta para coletar e
analisar dados públicos de anúncios.

O objetivo é ajudar empresas a:
1. Entender tendências de mercado
2. Analisar estratégias de concorrentes
3. Otimizar suas próprias campanhas publicitárias

A ferramenta coleta apenas dados públicos disponíveis na Biblioteca de
Anúncios e respeita todos os termos de uso da API.

Funcionalidades principais:
- Busca de anúncios por palavras-chave
- Análise de padrões de texto e CTAs
- Comparação de estratégias de competidores
- Geração de relatórios de insights

Volume estimado: ~200 chamadas de API por hora
Dados coletados: Texto de anúncios, CTAs, datas de veiculação,
                 páginas anunciantes
```

#### C. Screencasts ou Screenshots
**Você precisará mostrar:**
- Como o app funciona
- Onde usa a API de Anúncios
- Interface do usuário (se houver)

**O que fazer:**
```bash
# Grave um vídeo curto (2-3 minutos) mostrando:
1. Seu código rodando
2. Executando: python test_api.py
3. Mostrando a tentativa de coletar ads
4. Explicando o erro de permissão
5. Mostrando seu código fonte

Ou tire screenshots de:
- Seu código
- Terminal mostrando tentativa de uso
- Documentação do projeto
```

#### D. Documentação
**Links úteis para incluir:**
```
- Repositório GitHub (se público)
- README.md do projeto
- Documentação da API que você está construindo
```

### 2. Publicar o App

Você também precisa mudar o app de **Development** para **Live**.

**Como fazer:**

1. Na página do app, procure por **"App Mode"** ou **"Modo do App"**
2. Mude de **"Development"** para **"Live"** ou **"Ativo"**
3. Pode pedir para você aceitar termos e condições

## ⚠️ IMPORTANTE: Sobre a Biblioteca de Anúncios

A permissão que você está vendo (**Ads Management Standard Access**) é para **gerenciar** anúncios (criar, editar, deletar).

Para **LER** dados da **Biblioteca de Anúncios**, você também pode precisar de:

### Permissão Adicional: "Ad Library API Access"

Depois de solicitar o "Ads Management Standard Access", você também deve:

1. Voltar para: https://www.facebook.com/ads/library/api/
2. Procurar por **"Solicitar Acesso à API da Biblioteca de Anúncios"**
3. Selecionar **"Todos os Anúncios"**
4. Preencher outro formulário

## 🔄 Processo Completo

```
┌─────────────────────────────────────────────────────────┐
│ PASSO 1: Solicitar "Ads Management Standard Access"    │
│ ├─ Clicar no link azul na página atual                │
│ ├─ Preencher formulário de App Review                 │
│ └─ Aguardar aprovação (1-2 semanas)                   │
│                                                         │
│ PASSO 2: Publicar o App                               │
│ ├─ Mudar de "Development" para "Live"                 │
│ └─ Aceitar termos e condições                         │
│                                                         │
│ PASSO 3: Solicitar "Ad Library API Access"            │
│ ├─ Ir para facebook.com/ads/library/api/              │
│ ├─ Escolher "Todos os Anúncios"                       │
│ └─ Preencher formulário                               │
│                                                         │
│ PASSO 4: Aguardar Aprovação Final                     │
│ └─ Meta revisará em 1-2 semanas                       │
└─────────────────────────────────────────────────────────┘
```

## 📋 Checklist

Use esta lista para acompanhar seu progresso:

```
□ 1. Clicar em "Adicione o acesso padrão..."
□ 2. Preencher formulário de App Review
□ 3. Gravar screencast mostrando o app
□ 4. Escrever descrição do caso de uso
□ 5. Submeter para revisão
□ 6. Mudar app para modo "Live"
□ 7. Ir para facebook.com/ads/library/api/
□ 8. Solicitar acesso à Ad Library API
□ 9. Escolher "Todos os Anúncios"
□ 10. Preencher formulário da Ad Library
□ 11. Aguardar aprovação (1-2 semanas)
□ 12. Testar com: python test_api.py
```

## 🎬 Preparando o Screencast

**Recomendações:**

1. **Duração:** 2-3 minutos
2. **Ferramenta:** QuickTime (Mac), OBS Studio (grátis)
3. **Conteúdo a mostrar:**
   ```
   00:00 - Introdução do projeto
   00:30 - Mostrar estrutura do código
   01:00 - Executar python test_api.py
   01:30 - Mostrar erro de permissão
   02:00 - Explicar como vai usar a API
   02:30 - Mostrar documentação
   ```

4. **Narração (opcional mas recomendado):**
   ```
   "Olá, este é meu projeto de análise de anúncios.
   Ele usa a API da Biblioteca de Anúncios do Meta
   para coletar dados públicos de anúncios e gerar
   insights de inteligência competitiva.

   Como podem ver aqui [mostrar código], o app faz
   chamadas à API de forma responsável, respeitando
   os limites de taxa.

   Quando tento executar [rodar test_api.py], recebo
   um erro de permissão porque ainda não tenho acesso
   aprovado.

   Esta ferramenta será usada para [explicar uso]."
   ```

## 📧 Emails que Você Receberá

### Email 1: Confirmação de Submissão
```
Assunto: Sua solicitação de App Review foi recebida

Obrigado por submeter seu app para revisão.
Nossa equipe analisará em breve.

ID da Solicitação: #XXXXX
Status: Em Revisão
```

### Email 2: Solicitação de Informações (talvez)
```
Assunto: Informações adicionais necessárias

Precisamos de mais informações sobre seu app:
- [Pedidos específicos]

Por favor, responda em até 7 dias.
```

### Email 3: Aprovação (esperamos!)
```
Assunto: Seu app foi aprovado!

Parabéns! Seu app agora tem acesso a:
- Ads Management Standard Access

Próximos passos:
1. Configure seu app
2. Comece a usar a API
```

## 🔧 Depois da Aprovação

Quando aprovado:

1. **Testar imediatamente:**
   ```bash
   python test_api.py
   ```

2. **Verificar se funciona:**
   ```bash
   python example_usage.py 1
   ```

3. **Começar a coletar dados:**
   ```bash
   python -m src.main
   ```

## ❓ FAQ

**P: Quanto tempo demora?**
R: 1-2 semanas tipicamente. Alguns casos: 3-5 dias.

**P: E se for rejeitado?**
R: Meta explicará o motivo. Corrija e resubmeta.

**P: Posso usar enquanto espera?**
R: Não para dados reais. Use dados mock para desenvolver.

**P: Precisa ser empresa registrada?**
R: Não necessariamente, mas ajuda na aprovação.

**P: Pode usar dados pessoais?**
R: Pode tentar, mas aprovação é mais difícil.

## 📞 Suporte

Se tiver problemas:
- **Docs:** https://developers.facebook.com/docs/app-review/
- **Comunidade:** https://developers.facebook.com/community/
- **Suporte:** https://developers.facebook.com/support/bugs/

---

## ✅ Resumo

1. **AGORA:** Clique no link azul: "Adicione o acesso padrão..."
2. **Preencha:** Formulário de App Review
3. **Prepare:** Screencast de 2-3 minutos
4. **Escreva:** Descrição do caso de uso
5. **Submeta:** Para revisão
6. **Aguarde:** 1-2 semanas
7. **Teste:** python test_api.py

---

**Criado:** 2026-01-18
**Idioma:** Português (Brasil)
**Status:** Aguardando sua ação! Clique no link azul! 🚀
