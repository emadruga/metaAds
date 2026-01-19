# Guia Visual: Como Solicitar Acesso à API da Biblioteca de Anúncios

## 🎯 Você está aqui: Graph API Explorer ❌

O Graph API Explorer é apenas para testar chamadas de API. Você precisa ir para um lugar diferente!

## ✅ Onde você PRECISA ir

### Caminho 1: Através do Dashboard do App

```
1. Na página atual (Graph API Explorer):
   ┌─────────────────────────────────────┐
   │ Meta                                 │
   │ [Meus apps] ← CLIQUE AQUI           │
   └─────────────────────────────────────┘

2. Você verá:
   ┌─────────────────────────────────────┐
   │ Meus apps                            │
   │                                      │
   │ ┌─────────────────────────┐         │
   │ │ EWD Marketing API       │ ← CLIQUE│
   │ │ App ID: 257668913...    │         │
   │ └─────────────────────────┘         │
   └─────────────────────────────────────┘

3. No painel do app, à esquerda:
   ┌─────────────────────────────────────┐
   │ Dashboard                            │
   │ Painel                              │
   │ Produtos                            │
   │ > Adicionar produtos  ← CLIQUE      │
   │                                      │
   │ Ou role até encontrar:              │
   │                                      │
   │ □ API da biblioteca de anúncios     │
   │   [Configurar] ← CLIQUE             │
   └─────────────────────────────────────┘
```

### Caminho 2: Link Direto (Mais Fácil!)

Abra uma nova aba e cole este link:

```
https://www.facebook.com/ads/library/api/
```

Ou este (específico para desenvolvedores):

```
https://developers.facebook.com/products/ad-library-api/
```

## 🔍 O que você vai ver

Na página correta, você verá algo como:

```
╔════════════════════════════════════════════════╗
║  API da Biblioteca de Anúncios                ║
╟────────────────────────────────────────────────╢
║                                                ║
║  Obtenha acesso a dados de anúncios           ║
║  políticos e comerciais                       ║
║                                                ║
║  ┌──────────────────────────────────────┐    ║
║  │ Tipo de Acesso:                      │    ║
║  │                                       │    ║
║  │ ○ Anúncios políticos e sociais       │    ║
║  │ ● Todos os anúncios ← ESCOLHA ESTE!  │    ║
║  │                                       │    ║
║  │ [Começar] ou [Solicitar Acesso]      │    ║
║  └──────────────────────────────────────┘    ║
║                                                ║
╚════════════════════════════════════════════════╝
```

## 📝 Formulário de Solicitação

Depois de clicar em "Começar", você verá um formulário pedindo:

### 1. Informações Pessoais
```
Nome completo: _________________
Data de nascimento: ___/___/___
CPF: ___________________
Documento de identidade: [Upload]
```

### 2. Caso de Uso
```
Por que você precisa de acesso?

Exemplo de resposta:
┌────────────────────────────────────────┐
│ Estou desenvolvendo uma ferramenta de │
│ inteligência competitiva para analisar│
│ estratégias de publicidade digital.   │
│ A ferramenta ajudará empresas a       │
│ entender tendências de mercado e      │
│ otimizar suas campanhas através da   │
│ análise de dados públicos da         │
│ Biblioteca de Anúncios do Meta.      │
└────────────────────────────────────────┘
```

### 3. Informações de Uso
```
Chamadas de API estimadas por dia: ____
Países de interesse: [Brasil, EUA]
Categorias de anúncios: [Comercial]
```

## 🚨 Se você não encontrar a opção

### Verifique 1: Status do App

Seu app precisa estar no modo **"Ativo"** (Live), não "Desenvolvimento"

```
1. Vá para: https://developers.facebook.com/apps/25766891366325694/
2. Verifique o status no topo da página
3. Se estiver em "Desenvolvimento", mude para "Ativo"
```

### Verifique 2: Conta Business Manager

Algumas vezes você precisa de uma conta Business Manager:

```
1. Vá para: https://business.facebook.com/
2. Crie uma conta Business Manager (se não tiver)
3. Associe seu app ao Business Manager
4. Tente novamente solicitar acesso
```

### Verifique 3: Localização

A API pode não estar disponível em todas as regiões ainda.

Verifique em: https://developers.facebook.com/docs/ad-library-api/

## 🎬 Links Rápidos

Tente estes links na ordem:

1. **Link principal:** https://www.facebook.com/ads/library/api/
2. **Para desenvolvedores:** https://developers.facebook.com/products/ad-library-api/
3. **Seu app:** https://developers.facebook.com/apps/25766891366325694/
4. **Business Manager:** https://business.facebook.com/

## 📞 Precisa de Ajuda?

Se ainda não encontrar:

1. **Suporte Meta:**
   https://developers.facebook.com/support/

2. **Comunidade:**
   https://developers.facebook.com/community/

3. **Pesquise por:**
   "Como solicitar acesso API biblioteca anúncios Meta"

## ✅ Como saber se deu certo

Depois de solicitar acesso:

1. Você receberá um email de confirmação
2. Status mudará para "Em análise"
3. Após aprovação (1-2 semanas), execute:

```bash
python test_api.py
```

Deve mostrar:
```
3. Testing ads_archive endpoint...
   Status: 200
   ✓ ads_archive endpoint is working!
```

## 📊 Resumo Rápido

```
┌─────────────────────────────────────────────┐
│ 1. Saia do Graph API Explorer               │
│                                              │
│ 2. Vá para:                                 │
│    https://www.facebook.com/ads/library/api/│
│                                              │
│ 3. Clique em "Solicitar Acesso"            │
│                                              │
│ 4. Escolha "Todos os anúncios"             │
│                                              │
│ 5. Preencha o formulário                   │
│                                              │
│ 6. Aguarde aprovação (1-2 semanas)         │
└─────────────────────────────────────────────┘
```

---

**Criado:** 2026-01-18
**Idioma:** Português (Brasil)
