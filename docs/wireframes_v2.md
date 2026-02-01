# MetAds UI/UX Wireframes v2

## Table of Contents

1. [Authentication Screens](#1-authentication-screens-new)
2. [Niche Selector](#2-niche-selector-landing-page---authenticated)
3. [Desktop Layout](#3-desktop-layout-1024px)
4. [Tablet Layout](#4-tablet-layout-768px---1024px)
5. [Mobile Layout](#5-mobile-layout---iphone-768px)
6. [Interaction Patterns](#6-interaction-patterns)
7. [Visual Hierarchy](#7-visual-hierarchy)
8. [Component Specifications](#8-component-specifications)
9. [Related Ads / Variants Feature](#9-related-ads--variants-feature)
10. [User Flow Diagram](#10-user-flow-diagram-updated-with-auth)
11. [Key Differences from BigSpy](#11-key-differences-from-bigspy)
12. [Next Steps](#12-next-steps)

---

## Changelog from v1
- **Added Authentication Screens**: Sign In, Sign Up, Password Reset
- **Added User Menu**: Avatar dropdown with sign out, account settings
- **Added Protected Route Handling**: Loading states, redirect flows
- **Updated Headers**: Added user avatar/menu to all layouts
- **Added Onboarding Flow**: First-time user experience

---

## Design Philosophy

**Core Principle:** Clean, focused, progressive disclosure - the opposite of BigSpy's information overload.

**Authentication Principle:** Seamless auth experience using Clerk - minimal friction, multiple sign-in options, secure by default.

**Key Concept: Niches** - Users organize their research into separate "niches" (analysis projects), each containing its own collection of ads, saved items, and insights. This provides clear context and data isolation for different research areas.

**Key Metrics to Highlight:**
- Days Active (proxy for ad performance)
- Related Ads / Variants (shows active A/B testing)
- Creative Preview (visual-first approach)
- Page/Advertiser Name
- Platform Distribution
- CTA Type

---

## 1. AUTHENTICATION SCREENS (NEW)

### 1A. Sign In Page (Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                          ┌────────────────────────────────┐                          │
│                          │                                │                          │
│                          │           MetAds               │                          │
│                          │   Competitive Intelligence     │                          │
│                          │      for Meta Ads              │                          │
│                          │                                │                          │
│                          │  ────────────────────────────  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ Continue with Google   G │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ Continue with GitHub   ⬡ │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │          ─── or ───            │                          │
│                          │                                │                          │
│                          │  Email                         │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ you@example.com          │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  Password                      │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ ••••••••••••             │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │        Sign In           │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  Forgot password?              │                          │
│                          │                                │                          │
│                          │  ────────────────────────────  │                          │
│                          │                                │                          │
│                          │  Don't have an account?        │                          │
│                          │  Sign up →                     │                          │
│                          │                                │                          │
│                          └────────────────────────────────┘                          │
│                                                                                      │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘

Background: Gradient from primary color to secondary
Card: White with shadow, centered, max-width 400px
```

### 1B. Sign In Page (Mobile)

```
┌─────────────────────────────────┐
│                                 │
│                                 │
│           MetAds                │
│   Competitive Intelligence      │
│      for Meta Ads               │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Continue with Google    G │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ Continue with GitHub    ⬡ │  │
│  └───────────────────────────┘  │
│                                 │
│          ─── or ───             │
│                                 │
│  Email                          │
│  ┌───────────────────────────┐  │
│  │ you@example.com           │  │
│  └───────────────────────────┘  │
│                                 │
│  Password                       │
│  ┌───────────────────────────┐  │
│  │ ••••••••••••              │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │         Sign In           │  │
│  └───────────────────────────┘  │
│                                 │
│  Forgot password?               │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  Don't have an account?         │
│  Sign up →                      │
│                                 │
└─────────────────────────────────┘

Full-screen on mobile, no card container
Padding: 24px on sides
```

### 1C. Sign Up Page (Desktop)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                          ┌────────────────────────────────┐                          │
│                          │                                │                          │
│                          │           MetAds               │                          │
│                          │   Create your account          │                          │
│                          │                                │                          │
│                          │  ────────────────────────────  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ Continue with Google   G │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ Continue with GitHub   ⬡ │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │          ─── or ───            │                          │
│                          │                                │                          │
│                          │  First name                    │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ John                     │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  Last name                     │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ Doe                      │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  Email                         │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ john@example.com         │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  Password                      │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ ••••••••••••             │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │  Min 8 characters              │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │       Create Account     │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  By signing up, you agree to   │                          │
│                          │  our Terms and Privacy Policy  │                          │
│                          │                                │                          │
│                          │  ────────────────────────────  │                          │
│                          │                                │                          │
│                          │  Already have an account?      │                          │
│                          │  Sign in →                     │                          │
│                          │                                │                          │
│                          └────────────────────────────────┘                          │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 1D. Email Verification Screen

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                          ┌────────────────────────────────┐                          │
│                          │                                │                          │
│                          │           ✉️                    │                          │
│                          │                                │                          │
│                          │     Check your email           │                          │
│                          │                                │                          │
│                          │  We sent a verification link   │                          │
│                          │  to john@example.com           │                          │
│                          │                                │                          │
│                          │  Click the link in your email  │                          │
│                          │  to verify your account.       │                          │
│                          │                                │                          │
│                          │  ────────────────────────────  │                          │
│                          │                                │                          │
│                          │  Didn't receive the email?     │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │     Resend email         │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │   Use different email    │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          └────────────────────────────────┘                          │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 1E. Forgot Password Screen

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                          ┌────────────────────────────────┐                          │
│                          │                                │                          │
│                          │  ← Back to sign in             │                          │
│                          │                                │                          │
│                          │     Reset your password        │                          │
│                          │                                │                          │
│                          │  Enter your email and we'll    │                          │
│                          │  send you a reset link.        │                          │
│                          │                                │                          │
│                          │  Email                         │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ you@example.com          │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │    Send reset link       │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          └────────────────────────────────┘                          │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 1F. Loading / Auth Check Screen

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                                     MetAds                                           │
│                                                                                      │
│                                   ◠ ◡ ◠                                              │
│                                  (loading)                                           │
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                                                                                      │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘

Shown briefly while Clerk checks authentication status
Spinner animates
```

### 1G. Auth Component Specifications

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  AUTH SCREEN SPECIFICATIONS                           │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Card container:                                      │
│  - Width: 400px (desktop), 100% (mobile)              │
│  - Padding: 32px                                      │
│  - Border-radius: 16px                                │
│  - Shadow: 0 25px 50px rgba(0,0,0,0.15)              │
│  - Background: white                                  │
│                                                       │
│  Background:                                          │
│  - Gradient: linear-gradient(135deg, #667eea, #764ba2)│
│  - Or: Subtle pattern with brand colors               │
│                                                       │
│  Logo:                                                │
│  - Size: 48px icon + 24px text                        │
│  - Centered at top of card                            │
│                                                       │
│  OAuth buttons:                                       │
│  - Height: 48px                                       │
│  - Border: 1px solid #e5e7eb                          │
│  - Icon: 20px, left aligned                           │
│  - Hover: background #f9fafb                          │
│                                                       │
│  Form inputs:                                         │
│  - Height: 48px                                       │
│  - Border: 1px solid #d1d5db                          │
│  - Focus: border-color primary, ring                  │
│  - Border-radius: 8px                                 │
│                                                       │
│  Primary button:                                      │
│  - Height: 48px                                       │
│  - Background: primary color                          │
│  - Color: white                                       │
│  - Font-weight: 600                                   │
│                                                       │
│  Links:                                               │
│  - Color: primary                                     │
│  - Hover: underline                                   │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 2. NICHE SELECTOR (Landing Page - Authenticated)

The Niche Selector is the entry point to the application after authentication. Users must select or create a niche before accessing the search workspace.

### 2A. Desktop: Niche Selector (with User Menu)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  HEADER                                       MetAds          [+ New]    [Avatar ▼]  │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│  Welcome back, John!                                                                 │
│                                                                                      │
│  YOUR NICHES                                                                         │
│  ─────────────────────────────────────────────────────────────────────────────────   │
│                                                                                      │
│  ┌────────────────────────┐  ┌────────────────────────┐  ┌────────────────────────┐ │
│  │ 🎬                     │  │ 📊                     │  │ 🗳️                     │ │
│  │                        │  │                        │  │                        │ │
│  │ Video Editing Apps     │  │ CRMs                   │  │ Election 2026          │ │
│  │                        │  │                        │  │                        │ │
│  │ ─────────────────────  │  │ ─────────────────────  │  │ ─────────────────────  │ │
│  │                        │  │                        │  │                        │ │
│  │ 342 ads · 24 saved     │  │ 187 ads · 12 saved     │  │ 89 ads · 8 saved       │ │
│  │ Last collected: 2h ago │  │ Last collected: 1d ago │  │ Last collected: 3d ago │ │
│  │                        │  │                        │  │                        │ │
│  └────────────────────────┘  └────────────────────────┘  └────────────────────────┘ │
│         (purple accent)            (green accent)              (blue accent)         │
│                                                                                      │
│  ┌────────────────────────┐                                                         │
│  │                        │                                                         │
│  │          +             │                                                         │
│  │                        │                                                         │
│  │    Create New Niche    │                                                         │
│  │                        │                                                         │
│  └────────────────────────┘                                                         │
│       (dashed border)                                                               │
│                                                                                      │
├──────────────────────────────────────────────────────────────────────────────────────┤
│  FOOTER                                                              © 2026 MetAds   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### 2B. User Menu Dropdown (NEW)

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  USER MENU DROPDOWN                                   │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Triggered by clicking avatar in header               │
│                                                       │
│  ┌─────────────────────────────┐                      │
│  │ ┌─────┐                     │                      │
│  │ │     │  John Doe           │                      │
│  │ │ JD  │  john@example.com   │                      │
│  │ └─────┘                     │                      │
│  │ ─────────────────────────── │                      │
│  │                             │                      │
│  │  ⚙️  Account Settings       │ → Opens Clerk modal  │
│  │                             │                      │
│  │  📧  Manage Email          │ → Opens Clerk modal  │
│  │                             │                      │
│  │  🔒  Security              │ → Opens Clerk modal  │
│  │                             │                      │
│  │ ─────────────────────────── │                      │
│  │                             │                      │
│  │  🚪  Sign Out              │                      │
│  │                             │                      │
│  └─────────────────────────────┘                      │
│                                                       │
│  Specifications:                                      │
│  - Width: 240px                                       │
│  - Position: aligned to right edge of avatar         │
│  - Shadow: medium                                     │
│  - Border-radius: 8px                                 │
│  - Avatar: 40px circle with initials or image        │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 2C. Mobile: Niche Selector (with User Menu)

```
┌─────────────────────────────────┐
│  ≡  MetAds        [+]  [Avatar] │
├─────────────────────────────────┤
│                                 │
│  Welcome back, John!            │
│                                 │
│  YOUR NICHES                    │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🎬 Video Editing Apps     │  │
│  │ ─────────────────────────  │  │
│  │ 342 ads · 24 saved        │  │
│  │ Last collected: 2h ago    │  │
│  └───────────────────────────┘  │
│       (purple left border)      │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 📊 CRMs                   │  │
│  │ ─────────────────────────  │  │
│  │ 187 ads · 12 saved        │  │
│  │ Last collected: 1d ago    │  │
│  └───────────────────────────┘  │
│       (green left border)       │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🗳️ Election 2026          │  │
│  │ ─────────────────────────  │  │
│  │ 89 ads · 8 saved          │  │
│  │ Last collected: 3d ago    │  │
│  └───────────────────────────┘  │
│       (blue left border)        │
│                                 │
│  ┌───────────────────────────┐  │
│  │           +               │  │
│  │    Create New Niche       │  │
│  └───────────────────────────┘  │
│                                 │
└─────────────────────────────────┘
```

### 2D. First-Time User: Onboarding (NEW)

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  HEADER                                       MetAds                     [Avatar ▼]  │
├──────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                      │
│                                                                                      │
│                              🎉 Welcome to MetAds!                                   │
│                                                                                      │
│                  You're all set up. Let's create your first niche.                  │
│                                                                                      │
│                                                                                      │
│                          ┌────────────────────────────────┐                          │
│                          │                                │                          │
│                          │  What would you like to        │                          │
│                          │  research?                     │                          │
│                          │                                │                          │
│                          │  Name *                        │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ e.g., Video Editing Apps │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  Keywords (for collection)     │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │ video editing ai, opus   │  │                          │
│                          │  │ clip, descript           │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │  ┌──────────────────────────┐  │                          │
│                          │  │   Create & Start         │  │                          │
│                          │  │   Collecting             │  │                          │
│                          │  └──────────────────────────┘  │                          │
│                          │                                │                          │
│                          │                                │                          │
│                          │  Or choose a template:         │                          │
│                          │                                │                          │
│                          │  [SaaS Tools] [E-commerce]     │                          │
│                          │  [Finance] [Health & Fitness]  │                          │
│                          │                                │                          │
│                          └────────────────────────────────┘                          │
│                                                                                      │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘

Shown only on first sign-in when user has 0 niches
```

### 2E. Empty State: No Niches (Returning User)

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                       📁                            │
│                                                     │
│           No niches yet                             │
│                                                     │
│     Create your first niche to start               │
│     collecting and analyzing ads.                   │
│                                                     │
│     A niche is a research project focused           │
│     on a specific market or topic.                  │
│                                                     │
│         ┌─────────────────────────┐                │
│         │   Create Your First     │                │
│         │        Niche            │                │
│         └─────────────────────────┘                │
│                                                     │
│     Examples:                                       │
│     • "Video Editing Apps"                          │
│     • "E-commerce Fashion Brands"                   │
│     • "SaaS Productivity Tools"                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 2F. Create Niche Modal

```
┌─────────────────────────────────────────────────────┐
│  CREATE NEW NICHE                              [×]  │
├─────────────────────────────────────────────────────┤
│                                                     │
│  Name *                                             │
│  ┌─────────────────────────────────────────────┐   │
│  │ e.g., Video Editing Apps                    │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Description                                        │
│  ┌─────────────────────────────────────────────┐   │
│  │ e.g., AI-powered video editing tools and    │   │
│  │ competitor analysis                         │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Icon                                               │
│  ┌─────────────────────────────────────────────┐   │
│  │ [🎬] [📊] [🗳️] [💰] [🏠] [🎮] [📱] [more ▼] │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Color                                              │
│  ┌─────────────────────────────────────────────┐   │
│  │ [●] [●] [●] [●] [●] [●] [●] [●]             │   │
│  │ purple green blue orange pink teal red gray │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Keywords (for data collection)                     │
│  ┌─────────────────────────────────────────────┐   │
│  │ video editing ai, opus clip, descript       │   │
│  │ (comma separated)                           │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  Default Countries                                  │
│  ┌─────────────────────────────────────────────┐   │
│  │ [US ×] [BR ×] [+ Add]                       │   │
│  └─────────────────────────────────────────────┘   │
│                                                     │
│  ─────────────────────────────────────────────────  │
│                                                     │
│                      [Cancel]  [Create Niche]       │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## 3. DESKTOP LAYOUT (>1024px)

Three-column layout with persistent views, **scoped to the selected niche**, with user menu in header.

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│  [← Niches]  🎬 Video Editing Apps                    [⚙️]  [🔄 Collect]  [Avatar ▼] │
├────────────────────┬───────────────────────────────┬─────────────────────────────────┤
│                    │                               │                                 │
│  SEARCH PANEL      │  RESULTS LIST                 │  AD DETAIL                      │
│  ────────────────  │  ────────────────────────     │  ────────────────────────────   │
│                    │                               │                                 │
│  ┌──────────────┐  │  Found: 247 ads               │  ┌─────────────────────────┐   │
│  │ Search...    │  │  Sorted by: Days Active ▼     │  │                         │   │
│  └──────────────┘  │                               │  │                         │   │
│                    │  ┌─────────────────────────┐  │  │    CREATIVE PREVIEW     │   │
│  FILTERS           │  │┌───┐                    │  │  │                         │   │
│  ────────────────  │  ││ ◻ │ OpusClip        ⭐ │  │  │    (Large image/video   │   │
│                    │  │└───┘ Turn long videos...│  │  │     preview area)       │   │
│  Platform          │  │      IG FB · 67 days    │  │  │                         │   │
│  ○ All             │  │      [Learn More]       │  │  │                         │   │
│  ○ Instagram       │  └─────────────────────────┘  │  └─────────────────────────┘   │
│  ○ Facebook        │                               │                                 │
│  ○ Messenger       │  ┌─────────────────────────┐  │  PAGE                           │
│                    │  │┌───┐                    │  │  ─────────────────────────────  │
│  Country           │  ││ ◻ │ Descript           │  │  OpusClip                       │
│  [US, BR      ▼]   │  │└───┘ Edit videos as...  │  │  @opusclip · Verified           │
│                    │  │      IG · 45 days       │  │  [★ Mark as Competitor]         │
│  Status            │  │      [Try Free]         │  │                                 │
│  ○ All             │  └─────────────────────────┘  │  METRICS                        │
│  ● Active          │                               │  ─────────────────────────────  │
│  ○ Inactive        │  ┌─────────────────────────┐  │  Started: Dec 1, 2025           │
│                    │  │┌───┐                    │  │  Days Active: 67                │
│  Days Active       │  ││ ◻ │ Captions.ai        │  │  Platforms: IG, FB              │
│  Min: [7   ]       │  │└───┘ Auto-generate...   │  │  Status: ● Active               │
│  Max: [    ]       │  │      IG FB · 34 days    │  │  Related Ads: [4 variants →]    │
│                    │  │      [Get Started]      │  │                                 │
│  Date Range        │  └─────────────────────────┘  │  AD COPY                        │
│  [Last 30 days ▼]  │                               │  ─────────────────────────────  │
│                    │  ┌─────────────────────────┐  │  Headline:                      │
│                    │  │┌───┐                    │  │  "Turn long videos into         │
│  ┌──────────────┐  │  ││ ◻ │ Kapwing            │  │   viral clips in one click"     │
│  │   SEARCH     │  │  │└───┘ Create content...  │  │                                 │
│  └──────────────┘  │  │      IG · 28 days       │  │  Body:                          │
│                    │  │      [Sign Up]          │  │  "Stop spending hours editing.  │
│                    │  └─────────────────────────┘  │   OpusClip uses AI to find the  │
│                    │                               │   best moments in your long     │
│                    │  ─────────────────────────    │   videos..."                    │
│                    │  Load more results...         │                                 │
│                    │                               │  CTA: Learn More                │
│                    │                               │  Link: opus.pro/get-started     │
│                    │                               │                                 │
│                    │                               │  ─────────────────────────────  │
│                    │                               │                                 │
│                    │                               │  [View on Meta]  [Save]  [Copy] │
│                    │                               │                                 │
├────────────────────┴───────────────────────────────┴─────────────────────────────────┤
│  FOOTER                                                              © 2026 MetAds   │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Desktop Header (Workspace) - Updated

```
┌──────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                      │
│  WORKSPACE HEADER SPECIFICATIONS                                                     │
│  ──────────────────────────────────────────────────────────────────────────────────  │
│                                                                                      │
│  [← Niches]           Back navigation to Niche Selector                              │
│                                                                                      │
│  🎬 Video Editing Apps   Niche icon + name (with niche color accent underline)       │
│                                                                                      │
│  [⚙️]                  Niche Settings (edit name, keywords, colors)                  │
│                                                                                      │
│  [🔄 Collect]          Trigger data collection for this niche                        │
│                        - Shows spinner while collecting                              │
│                        - Shows "Collecting... 23 new" during progress                │
│                        - Shows "Last: 2h ago" when idle                              │
│                                                                                      │
│  [Avatar ▼]            User menu (NEW)                                               │
│                        - Shows user avatar or initials                               │
│                        - Dropdown with account options                               │
│                        - Sign out button                                             │
│                                                                                      │
└──────────────────────────────────────────────────────────────────────────────────────┘
```

### Desktop Column Widths
- Search Panel: ~250px (fixed)
- Results List: ~350px (fixed)
- Ad Detail: remaining space (flexible, min 400px)

---

## 4. TABLET LAYOUT (768px - 1024px)

Two-column layout with collapsible search, **scoped to the selected niche**, with user menu.

```
┌────────────────────────────────────────────────────────────────────┐
│  [← Niches]  🎬 Video Editing Apps           [⚙️] [Collect] [Avtr] │
├────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────┐    │
│  │ 🔍 video editing ai                          [Filters ▼]   │    │
│  └────────────────────────────────────────────────────────────┘    │
├─────────────────────────────┬──────────────────────────────────────┤
│                             │                                      │
│  RESULTS LIST               │  AD DETAIL                           │
│  ─────────────────────────  │  ──────────────────────────────────  │
│                             │                                      │
│  247 ads · Active · US, BR  │  ┌──────────────────────────────┐   │
│                             │  │                              │   │
│  ┌───────────────────────┐  │  │                              │   │
│  │┌───┐                  │  │  │      CREATIVE PREVIEW        │   │
│  ││   │ OpusClip      ⭐ │  │  │                              │   │
│  ││ ◻ │ Turn long vid... │  │  │                              │   │
│  │└───┘ IG FB · 67 days  │  │  │                              │   │
│  └───────────────────────┘  │  └──────────────────────────────┘   │
│                             │                                      │
│  ┌───────────────────────┐  │  OpusClip · @opusclip                │
│  │┌───┐                  │  │  [★ Mark as Competitor]              │
│  ││   │ Descript         │  │  ────────────────────────────────   │
│  ││ ◻ │ Edit videos...   │  │                                      │
│  │└───┘ IG · 45 days     │  │  ● Active · 67 days · IG, FB         │
│  └───────────────────────┘  │  Started: Dec 1, 2025                │
│                             │  Related Ads: [4 variants →]         │
│  ┌───────────────────────┐  │                                      │
│  │┌───┐                  │  │  HEADLINE                            │
│  ││   │ Captions.ai      │  │  "Turn long videos into viral        │
│  ││ ◻ │ Auto-generate... │  │   clips in one click"                │
│  │└───┘ IG FB · 34 days  │  │                                      │
│  └───────────────────────┘  │  BODY                                │
│                             │  "Stop spending hours editing..."    │
│  ┌───────────────────────┐  │                                      │
│  │┌───┐                  │  │  CTA: [Learn More]                   │
│  ││   │ Kapwing          │  │  Link: opus.pro/get-started          │
│  ││ ◻ │ Create content..│  │                                      │
│  │└───┘ IG · 28 days     │  │  ──────────────────────────────────  │
│  └───────────────────────┘  │  [View on Meta]  [Save]  [Copy]      │
│                             │                                      │
│  Load more...               │                                      │
│                             │                                      │
├─────────────────────────────┴──────────────────────────────────────┤
│  FOOTER                                                            │
└────────────────────────────────────────────────────────────────────┘
```

---

## 5. MOBILE LAYOUT - iPhone (<768px)

Single column with bottom tab navigation, **scoped to the selected niche**, with user menu accessible from hamburger.

### 5A. Mobile: Search View (Tab 1)

```
┌─────────────────────────────────┐
│  ←  🎬 Video Editing   [Avatar] │
├─────────────────────────────────┤
│                                 │
│  SEARCH                         │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ 🔍 Search keywords...     │  │
│  └───────────────────────────┘  │
│                                 │
│  Platform                       │
│  ┌───────────────────────────┐  │
│  │ All platforms           ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Country                        │
│  ┌───────────────────────────┐  │
│  │ Select countries...     ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Status                         │
│  ┌───────────────────────────┐  │
│  │ Active only             ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Minimum Days Active            │
│  ┌───────────────────────────┐  │
│  │ 7 days                  ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  Date Range                     │
│  ┌───────────────────────────┐  │
│  │ Last 30 days            ▼ │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │         SEARCH            │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
│                                 │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
│     active                      │
└─────────────────────────────────┘
```

### 5B. Mobile: User Menu (Slide-in from Avatar)

```
┌─────────────────────────────────┐
│  ×                     Account  │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │  ┌─────┐                  │  │
│  │  │     │  John Doe        │  │
│  │  │ JD  │  john@example.com│  │
│  │  └─────┘                  │  │
│  └───────────────────────────┘  │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ⚙️  Account Settings           │
│                                 │
│  📧  Manage Email               │
│                                 │
│  🔒  Security                   │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  🚪  Sign Out                   │
│                                 │
│                                 │
│                                 │
│                                 │
│                                 │
│                                 │
└─────────────────────────────────┘

Slides in from right
Overlay: semi-transparent dark background
```

### 5C. Mobile: Results View (Tab 2)

```
┌─────────────────────────────────┐
│  ←  🎬 Video Editing   [Avatar] │
├─────────────────────────────────┤
│                                 │
│  "video editing ai"             │
│  247 results · Active · US, BR  │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  OpusClip      ⭐ │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Turn long videos │  │
│  │ └─────┘  into viral cli...│  │
│  │                           │  │
│  │  IG FB  67 days  4 var >  │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  Descript         │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Edit videos as   │  │
│  │ └─────┘  easily as doc... │  │
│  │                           │  │
│  │  IG       45 days    >    │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Load more ads...     │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
│                  active         │
└─────────────────────────────────┘
```

### 5D. Mobile: Ad Detail View (Full Screen Overlay)

```
┌─────────────────────────────────┐
│  ←  Ad Detail           [Save]  │
├─────────────────────────────────┤
│                                 │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │                           │  │
│  │                           │  │
│  │     CREATIVE PREVIEW      │  │
│  │                           │  │
│  │     (Full-width image     │  │
│  │      or video player)     │  │
│  │                           │  │
│  │                           │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
│  OpusClip                       │
│  @opusclip · Verified           │
│  [★ Mark as Competitor]         │
│  ─────────────────────────────  │
│                                 │
│  ┌─────────┬─────────┬───────┐  │
│  │ 67 days │  IG FB  │ Active│  │
│  │ active  │         │   ●   │  │
│  └─────────┴─────────┴───────┘  │
│                                 │
│  Started: December 1, 2025      │
│                                 │
│  RELATED ADS                    │
│  ─────────────────────────────  │
│  ┌───────────────────────────┐  │
│  │  [4 variants from this    │  │
│  │   advertiser →]           │  │
│  │   Longest: 67 days        │  │
│  │   Newest: 12 days ago     │  │
│  └───────────────────────────┘  │
│                                 │
│  HEADLINE                       │
│  ─────────────────────────────  │
│  "Turn long videos into viral   │
│   clips in one click"           │
│                                 │
│  BODY                           │
│  ─────────────────────────────  │
│  "Stop spending hours editing.  │
│   OpusClip uses AI to find the  │
│   best moments in your long     │
│   videos and turns them into    │
│   viral shorts automatically.   │
│   Try it free today!"           │
│                                 │
│  CTA                            │
│  ─────────────────────────────  │
│  [Learn More]                   │
│                                 │
│  LANDING PAGE                   │
│  ─────────────────────────────  │
│  opus.pro/get-started           │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────┐  ┌─────────────┐ │
│  │View on    │  │  Copy Ad    │ │
│  │   Meta    │  │    Text     │ │
│  └───────────┘  └─────────────┘ │
│                                 │
└─────────────────────────────────┘
```

### 5E. Mobile: Saved Ads View (Tab 3)

```
┌─────────────────────────────────┐
│  ←  🎬 Video Editing   [Avatar] │
├─────────────────────────────────┤
│                                 │
│  SAVED ADS                      │
│  in "Video Editing Apps"        │
│  12 ads saved                   │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  OpusClip         │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  Turn long videos │  │
│  │ └─────┘  Saved: Jan 28    │  │
│  │         "Great hook!"     │  │
│  │  IG FB    67 days    >    │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  Runway ML        │  │
│  │ │  ◻  │  ───────────────  │  │
│  │ │     │  AI video gen...  │  │
│  │ └─────┘  Saved: Jan 25    │  │
│  │                           │  │
│  │  IG       52 days    >    │  │
│  └───────────────────────────┘  │
│                                 │
│  (empty state if no saved)     │
│  ┌───────────────────────────┐  │
│  │                           │  │
│  │   ⭐ No saved ads yet     │  │
│  │   in "Video Editing Apps" │  │
│  │                           │  │
│  │   Tap the save icon on    │  │
│  │   any ad to bookmark it   │  │
│  │   for later.              │  │
│  │                           │  │
│  │   [Start Searching]       │  │
│  │                           │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
│                          active │
└─────────────────────────────────┘
```

### 5F. Mobile: Related Ads View (Slide-in Panel)

```
┌─────────────────────────────────┐
│  ←  Related Ads (4)     OpusClip│
├─────────────────────────────────┤
│                                 │
│  VARIANT INSIGHTS               │
│  in "Video Editing Apps"        │
│  ─────────────────────────────  │
│  Longest running: 67 days       │
│  All use same CTA: Learn More   │
│  Headlines differ (A/B test)    │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐  ★ LONGEST        │  │
│  │ │     │  ───────────────  │  │
│  │ │  ◻  │  "Turn long       │  │
│  │ │     │   videos into..." │  │
│  │ └─────┘                   │  │
│  │  67 days · IG FB          │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐                   │  │
│  │ │     │  ───────────────  │  │
│  │ │  ◻  │  "Stop wasting    │  │
│  │ │     │   hours on..."    │  │
│  │ └─────┘                   │  │
│  │  45 days · IG FB          │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │ ┌─────┐  ✦ NEWEST         │  │
│  │ │     │  ───────────────  │  │
│  │ │  ◻  │  "AI finds your   │  │
│  │ │     │   best clips..."  │  │
│  │ └─────┘                   │  │
│  │  12 days · IG             │  │
│  └───────────────────────────┘  │
│                                 │
├─────────────────────────────────┤
│  [🔍 Search]  [📋 Results]  [⭐]│
└─────────────────────────────────┘
```

### 5G. Mobile: Niche Settings View

```
┌─────────────────────────────────┐
│  ←  Niche Settings              │
├─────────────────────────────────┤
│                                 │
│  🎬 VIDEO EDITING APPS          │
│  ─────────────────────────────  │
│                                 │
│  Name                           │
│  ┌───────────────────────────┐  │
│  │ Video Editing Apps        │  │
│  └───────────────────────────┘  │
│                                 │
│  Description                    │
│  ┌───────────────────────────┐  │
│  │ AI-powered video editing  │  │
│  │ tools and competitor      │  │
│  │ analysis                  │  │
│  └───────────────────────────┘  │
│                                 │
│  Icon                           │
│  [🎬] [📊] [🗳️] [💰] [🏠] [more]│
│                                 │
│  Color                          │
│  [●] [●] [●] [●] [●] [●]       │
│   ▲ selected                    │
│                                 │
│  Keywords                       │
│  ─────────────────────────────  │
│  ┌───────────────────────────┐  │
│  │ video editing ai     [×]  │  │
│  │ opus clip            [×]  │  │
│  │ descript             [×]  │  │
│  │ [+ Add keyword]           │  │
│  └───────────────────────────┘  │
│                                 │
│  Default Countries              │
│  [US ×] [BR ×] [+ Add]         │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  COLLECTION HISTORY             │
│  ─────────────────────────────  │
│  Today 2:30 PM    +23 new ads  │
│  Yesterday        +45 new ads  │
│  Jan 28           +12 new ads  │
│                                 │
│  ─────────────────────────────  │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Save Changes         │  │
│  └───────────────────────────┘  │
│                                 │
│  ┌───────────────────────────┐  │
│  │      Delete Niche         │  │
│  └───────────────────────────┘  │
│         (red text)              │
│                                 │
└─────────────────────────────────┘
```

---

## 6. INTERACTION PATTERNS

### 6A. Result Card States

```
NORMAL STATE                    HOVER/FOCUS STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│ ┌─────┐                   │   │ ┌─────┐                   │
│ │     │  Page Name        │   │ │     │  Page Name        │
│ │  ◻  │  Headline text... │   │ │  ◻  │  Headline text... │
│ └─────┘  IG · 45 days     │   │ └─────┘  IG · 45 days     │
└───────────────────────────┘   └───────────────────────────┘
 Border: none                    Border: 2px primary color
 Background: white               Background: light highlight


SELECTED STATE                  LOADING STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│ ┌─────┐                   │   │ ┌─────┐                   │
│ │     │  Page Name        │   │ │ ░░░ │  ░░░░░░░░░░░░░░  │
│ │  ◻  │  Headline text... │   │ │ ░░░ │  ░░░░░░░░░░░░░░  │
│ └─────┘  IG · 45 days     │   │ └─────┘  ░░░░░░░░░░░░░░  │
└───────────────────────────┘   └───────────────────────────┘
 Border: 2px primary color       Skeleton loading animation
 Background: primary light
 Left bar: 4px primary color


SAVED STATE (additional indicator)
┌───────────────────────────┐
│ ┌─────┐               ⭐  │
│ │     │  Page Name        │
│ │  ◻  │  Headline text... │
│ └─────┘  IG · 45 days     │
└───────────────────────────┘
 Star icon in top-right
 Indicates ad is saved in this niche
```

### 6B. Filter Chips (Mobile/Tablet)

```
Active filters shown as dismissible chips:

┌─────────────────────────────────────────────────────────┐
│  [Active ×]  [US ×]  [BR ×]  [7+ days ×]  [+ Filters]  │
└─────────────────────────────────────────────────────────┘
```

### 6C. Empty States

```
NO RESULTS                      ERROR STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│                           │   │                           │
│         🔍                │   │         ⚠️                │
│                           │   │                           │
│   No ads found in         │   │   Something went wrong    │
│   "Video Editing Apps"    │   │                           │
│                           │   │   We couldn't load the    │
│   Try adjusting your      │   │   results. Please check   │
│   filters or search       │   │   your connection.        │
│   for different keywords  │   │                           │
│                           │   │   [Try Again]             │
│   [Clear Filters]         │   │                           │
│                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘


NO SAVED ADS IN NICHE           NOT AUTHENTICATED
┌───────────────────────────┐   ┌───────────────────────────┐
│                           │   │                           │
│         ⭐                │   │         🔒                │
│                           │   │                           │
│   No saved ads yet in     │   │   Session expired         │
│   "Video Editing Apps"    │   │                           │
│                           │   │   Please sign in again    │
│   Tap the save icon on    │   │   to continue.            │
│   any ad to bookmark it   │   │                           │
│   for later.              │   │   [Sign In]               │
│                           │   │                           │
│   [Start Searching]       │   │                           │
│                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘
```

### 6D. Collection Status Indicator

```
IDLE STATE                      COLLECTING STATE
┌───────────────────────────┐   ┌───────────────────────────┐
│                           │   │                           │
│   [🔄 Collect]            │   │   [⏳ Collecting...]      │
│                           │   │   23 new ads found        │
│   Last: 2 hours ago       │   │                           │
│                           │   │                           │
└───────────────────────────┘   └───────────────────────────┘

COMPLETED STATE (briefly shown)
┌───────────────────────────┐
│                           │
│   [✓ Done]                │
│   +45 new ads collected   │
│                           │
└───────────────────────────┘
 (reverts to idle after 3s)
```

### 6E. Sign Out Confirmation (NEW)

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  SIGN OUT CONFIRMATION MODAL                          │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │                                                 │  │
│  │              Sign out of MetAds?                │  │
│  │                                                 │  │
│  │   You'll need to sign in again to access       │  │
│  │   your niches and saved ads.                   │  │
│  │                                                 │  │
│  │   ┌───────────────┐  ┌───────────────────────┐ │  │
│  │   │    Cancel     │  │      Sign Out         │ │  │
│  │   └───────────────┘  └───────────────────────┘ │  │
│  │                                                 │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
└───────────────────────────────────────────────────────┘

Note: This is optional - Clerk handles sign out smoothly
without confirmation in most cases
```

---

## 7. VISUAL HIERARCHY

### Color Usage

```
PRIMARY ACTIONS     METRICS/BADGES       STATUS INDICATORS
┌─────────────┐    ┌──────────────┐     ┌─────────────────┐
│   Search    │    │  67 days     │     │  ● Active       │
│   Button    │    │  (prominent) │     │  (green)        │
└─────────────┘    └──────────────┘     │                 │
 Blue/Primary       Dark text on        │  ○ Inactive     │
                    light background    │  (gray)         │
                                        └─────────────────┘

NICHE COLORS (user-selectable)
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Purple: #8B5CF6   Green: #10B981   Blue: #3B82F6      │
│  Orange: #F59E0B   Pink: #EC4899    Teal: #14B8A6      │
│  Red: #EF4444      Gray: #6B7280                       │
│                                                         │
│  Used for:                                              │
│  - Niche card accent/border                             │
│  - Workspace header underline                           │
│  - Save indicator tint                                  │
│                                                         │
└─────────────────────────────────────────────────────────┘

AUTHENTICATION COLORS (NEW)
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  Auth page gradient:                                    │
│  - Start: #667eea (indigo)                              │
│  - End: #764ba2 (purple)                                │
│                                                         │
│  OAuth button borders: #e5e7eb                          │
│  OAuth button hover: #f9fafb                            │
│                                                         │
│  Error messages: #ef4444 (red)                          │
│  Success messages: #22c55e (green)                      │
│                                                         │
└─────────────────────────────────────────────────────────┘

PLATFORM ICONS              VARIANT BADGE
┌─────────────────────────┐ ┌─────────────────────────────┐
│  [IG]  [FB]  [MSG]  [AN]│ │  [4 var]                    │
│                         │ │                             │
│  Each platform gets a   │ │  Shows number of related    │
│  subtle icon or badge   │ │  ads/variants found         │
└─────────────────────────┘ └─────────────────────────────┘

SAVED INDICATOR
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ⭐ (filled star)  - Ad is saved in current niche      │
│  ☆ (empty star)    - Ad is not saved                   │
│                                                         │
│  The star uses the niche color as accent               │
│                                                         │
└─────────────────────────────────────────────────────────┘

USER AVATAR (NEW)
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────┐                                               │
│  │     │  Size: 40px (desktop), 32px (mobile)          │
│  │ JD  │  Shape: Circle                                │
│  │     │  Content: User image or initials              │
│  └─────┘  Border: 2px solid white (on dark bg)         │
│           Hover: ring-2 ring-primary                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

### Typography Scale

```
DESKTOP                          MOBILE
─────────────────────────────    ─────────────────────────────
App name (logo): 24px bold       App name (logo): 20px bold
User name:       14px medium     User name:       14px medium
Niche Name:      20px semibold   Niche Name:      18px semibold
Page Name:       16px semibold   Page Name:       15px semibold
Headline:        14px regular    Headline:        14px regular
Meta info:       12px regular    Meta info:       12px regular
Days badge:      14px bold       Days badge:      14px bold
Variant badge:   12px medium     Variant badge:   12px medium

Section headers: 13px uppercase  Section headers: 12px uppercase
Body text:       14px regular    Body text:       14px regular

AUTH PAGES (NEW)
─────────────────────────────
Logo:            24px bold
Heading:         20px semibold
Labels:          14px medium
Inputs:          16px regular
Buttons:         16px semibold
Links:           14px regular
Helper text:     12px regular
```

---

## 8. COMPONENT SPECIFICATIONS

### 8A. Ad Result Card

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  DIMENSIONS                                           │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Desktop card:   350px width, auto height             │
│  Tablet card:    100% of column, auto height          │
│  Mobile card:    100% width - 32px padding            │
│                                                       │
│  Thumbnail:      60x60px (desktop/tablet)             │
│                  80x80px (mobile - larger touch target)│
│                                                       │
│  SPACING                                              │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Card padding:   16px                                 │
│  Card margin:    8px bottom                           │
│  Card radius:    8px                                  │
│                                                       │
│  Thumb margin:   12px right                           │
│  Text spacing:   4px between lines                    │
│  Badge spacing:  8px between badges                   │
│                                                       │
│  SAVED INDICATOR                                      │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Position:       Top-right corner, 8px from edges     │
│  Size:           16px (desktop), 20px (mobile)        │
│  Color:          Niche accent color when saved        │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 8B. Detail Panel Creative Preview

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  CREATIVE PREVIEW AREA                                │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Desktop:    400px max width, 16:9 or 1:1 aspect      │
│  Tablet:     100% width, maintain aspect ratio        │
│  Mobile:     100% width, maintain aspect ratio        │
│                                                       │
│  Types supported:                                     │
│  - Static image (most common)                         │
│  - Video with play button overlay                     │
│  - Carousel with dots indicator                       │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │                                                 │  │
│  │                                                 │  │
│  │               [▶ Play]                          │  │
│  │            (video overlay)                      │  │
│  │                                                 │  │
│  │                                                 │  │
│  └─────────────────────────────────────────────────┘  │
│                    ● ○ ○ ○                            │
│               (carousel dots)                         │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 8C. Niche Card

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  NICHE CARD COMPONENT                                 │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Desktop:                                             │
│  - Width: 280px                                       │
│  - Height: 180px                                      │
│  - Background: White with subtle niche color tint     │
│  - Border: 1px solid gray-200                         │
│  - Border-radius: 12px                                │
│  - Hover: elevation shadow, slight scale (1.02)       │
│                                                       │
│  Mobile:                                              │
│  - Width: 100% - 32px margin                          │
│  - Height: 100px                                      │
│  - Left border: 4px solid niche color                 │
│  - Background: White                                  │
│                                                       │
│  Content:                                             │
│  - Icon: 32px (desktop), 24px (mobile)                │
│  - Name: 18px semibold, gray-900                      │
│  - Stats: 14px regular, gray-600                      │
│  - Last collected: 12px regular, gray-400             │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 8D. User Avatar Component (NEW)

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  USER AVATAR COMPONENT                                │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Sizes:                                               │
│  - Large: 48px (profile pages)                        │
│  - Medium: 40px (desktop header)                      │
│  - Small: 32px (mobile header, comments)              │
│                                                       │
│  States:                                              │
│  - With image: Display user's profile image           │
│  - Without image: Show initials on colored background │
│                                                       │
│  Initials background colors (based on user ID hash):  │
│  - #8B5CF6 (purple)                                   │
│  - #10B981 (green)                                    │
│  - #3B82F6 (blue)                                     │
│  - #F59E0B (orange)                                   │
│  - #EC4899 (pink)                                     │
│                                                       │
│  Hover/Focus:                                         │
│  - Ring: 2px primary color                            │
│  - Cursor: pointer                                    │
│                                                       │
│  In dropdown trigger:                                 │
│  - Chevron down icon: 12px, gray-400                  │
│  - Spacing between avatar and chevron: 4px            │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 9. RELATED ADS / VARIANTS FEATURE

### 9A. Feature Overview

The Related Ads feature helps users identify A/B testing patterns and find winning ad variations by grouping ads from the same advertiser that are likely part of the same campaign. **Variants are scoped to the current niche.**

### 9B. What This Feature Enables

| Insight | Value for Reverse Engineering |
|---------|-------------------------------|
| "This ad has 4 variants" | Shows advertiser is actively testing - serious player |
| "This is the longest-running variant" | Likely the winner - study this one closely |
| "Newest variant launched 3 days ago" | They're still iterating - angle is working |
| "All variants use same CTA" | That CTA is validated across tests |
| "Headlines differ but body is same" | They're testing hooks, not core message |

### 9C. Variant Card Component

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  VARIANT CARD (in Related Ads list)                   │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │ ┌─────┐  ★ LONGEST (or ✦ NEWEST)               │  │
│  │ │     │  ─────────────────────────────────────  │  │
│  │ │  ◻  │  "Headline text preview that may       │  │
│  │ │     │   wrap to two lines..."                │  │
│  │ └─────┘                                        │  │
│  │  45 days · IG FB · Learn More                  │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│  Badge shown only for:                                │
│  - ★ LONGEST = highest days_active in group          │
│  - ✦ NEWEST = most recent start_date in group        │
│                                                       │
└───────────────────────────────────────────────────────┘
```

### 9D. Variant Insights Summary

```
┌───────────────────────────────────────────────────────┐
│                                                       │
│  VARIANT INSIGHTS (top of Related Ads view)           │
│  in "Video Editing Apps"                              │
│  ───────────────────────────────────────────────────  │
│                                                       │
│  Displayed insights (when applicable):                │
│                                                       │
│  • "Longest running: 67 days"                         │
│  • "All use same CTA: Learn More"                     │
│  • "Headlines differ (A/B testing hooks)"             │
│  • "Same landing page across variants"                │
│  • "Testing across IG and FB"                         │
│                                                       │
│  These insights help users quickly understand         │
│  what the advertiser is testing and what's working.   │
│                                                       │
└───────────────────────────────────────────────────────┘
```

---

## 10. USER FLOW DIAGRAM (Updated with Auth)

```
                         ┌─────────────────┐
                         │   LANDING PAGE  │
                         │   (Marketing)   │
                         └────────┬────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
                    ▼             ▼             ▼
             ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
             │   SIGN IN   │ │   SIGN UP   │ │   FORGOT    │
             │             │ │             │ │   PASSWORD  │
             └──────┬──────┘ └──────┬──────┘ └─────────────┘
                    │               │
                    │    ┌──────────┘
                    │    │
                    │    ▼
                    │  ┌─────────────┐
                    │  │   VERIFY    │
                    │  │   EMAIL     │
                    │  └──────┬──────┘
                    │         │
                    └────┬────┘
                         │
                         ▼
                ┌─────────────────┐
                │  NICHE SELECTOR │
                │  (Authenticated)│
                └────────┬────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         ▼               ▼               ▼
  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
  │   Niche 1   │ │   Niche 2   │ │  + Create   │
  │  Video Ed   │ │    CRMs     │ │    New      │
  └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
         │               │               │
         └────────┬──────┘               │
                  │                      ▼
                  ▼              ┌─────────────┐
         ┌─────────────────┐     │ Create Form │
         │    WORKSPACE    │     │  - Name     │
         │  (3-col layout) │     │  - Keywords │
         └────────┬────────┘     │  - Color    │
                  │              └─────────────┘
  ┌───────────────┼───────────────┐
  │               │               │
  ▼               ▼               ▼
┌──────┐   ┌──────────┐   ┌──────────┐
│SEARCH│   │  SAVED   │   │ SETTINGS │
│(tab) │   │  (tab)   │   │ (button) │
└──┬───┘   └──────────┘   └──────────┘
   │
   ▼
┌─────────────┐
│   SEARCH    │──────────────┐
│  RESULTS    │              │
└──────┬──────┘              │
       │                     │
User taps                No results
a result                     │
       │                     ▼
       ▼              ┌─────────────┐
┌─────────────┐       │   EMPTY     │
│  AD DETAIL  │       │   STATE     │
│   (View)    │       └──────┬──────┘
└──────┬──────┘              │
       │              Adjust filters
       │                     │
┌──────┼──────────────────┐  │
│      │                  │  │
▼      ▼                  ▼  │
┌────┐ ┌────┐      ┌────────┐
│VIEW│ │SAVE│      │  COPY  │
│REL.│ │ AD │      │  TEXT  │
│ADS │ └──┬─┘      └────────┘
└─┬──┘    │
  │       ▼
  │  ┌──────────┐
  │  │  SAVED   │◄───────────┘
  │  │  ADS     │
  │  │(in niche)│
  │  └──────────┘
  │
  ▼
┌──────────┐
│ RELATED  │
│ ADS LIST │
│(in niche)│
└────┬─────┘
     │
Tap a variant
     │
     ▼
┌──────────┐
│AD DETAIL │
│(Variant) │
└──────────┘


USER MENU FLOWS (NEW)
─────────────────────

From any authenticated screen:

[Avatar ▼] click
     │
     ▼
┌──────────────┐
│  User Menu   │
│  Dropdown    │
└──────┬───────┘
       │
       ├─── Account Settings → Clerk Account Modal
       │
       ├─── Manage Email → Clerk Email Modal
       │
       ├─── Security → Clerk Security Modal
       │
       └─── Sign Out → Confirm → /sign-in
```

---

## 11. KEY DIFFERENCES FROM BIGSPY

| Aspect | BigSpy | MetAds (Our Approach) |
|--------|--------|----------------------|
| Authentication | Simple login | Modern OAuth (Google, GitHub, Magic Link) |
| User experience | Generic | Personalized with user name/avatar |
| Information density | Very high - everything visible | Progressive disclosure |
| Primary navigation | Complex menu system | Niche-first, then 3-tab mobile / 3-column desktop |
| Data organization | Single global pool | **Organized by Niches (research projects)** |
| Filters | Always expanded, many options | Collapsible, focused on key filters |
| Creative preview | Small thumbnails | Large, prominent previews |
| Key metric | Multiple metrics competing | "Days Active" as primary signal |
| Variant detection | Not prominently featured | Core feature with dedicated view |
| Mobile experience | Desktop-first, cramped on mobile | Mobile-first, native feel |
| Visual style | Data-table aesthetic | Card-based, modern UI |
| Cognitive load | High - need to scan everything | Low - clear hierarchy |
| Saved ads | Global saved list | **Per-niche saved ads with notes/tags** |

---

## 12. NEXT STEPS

1. **Implement Auth Screens** - Sign in, sign up, forgot password with Clerk
2. **Add User Menu** - Avatar dropdown in all headers
3. **Implement Niche Selector** - Create the landing page and niche management
4. **Update workspace header** - Add niche context, user menu, and navigation
5. **Validate with real data** - Mock up with actual Meta Ad Library results
6. **Test on devices** - Verify touch targets and readability on iPhone
7. **Define color palette** - Finalize niche and auth color options
8. **Create component library** - Build reusable UI components
9. **Prototype interactions** - Add transitions and micro-animations
10. **Implement variant detection** - Start with temporal + same advertiser approach
11. **Design variant insights algorithm** - Define rules for insight generation
12. **Test auth flows** - Sign in, sign out, session expiry, password reset

---

*Document Version: 2.0*
*Created: January 30, 2026*
*Updated: January 31, 2026 - Added Authentication UI screens and user menu*
*Status: Ideation Phase*
