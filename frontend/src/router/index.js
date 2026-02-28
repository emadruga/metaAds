/**
 * Vue Router Configuration
 *
 * Routes:
 * - Public: /sign-in, /sign-up
 * - Protected: /, /niches/new, /n/:nicheSlug/*
 *
 * In dev mode, auth guards are bypassed.
 */
import { createRouter, createWebHistory } from 'vue-router'
import { devMode } from '@/services/api'

const routes = [
  // Public routes
  {
    path: '/sign-in',
    name: 'SignIn',
    component: () => import('@/views/SignInView.vue'),
    meta: { requiresAuth: false }
  },
  {
    path: '/sign-up',
    name: 'SignUp',
    component: () => import('@/views/SignUpView.vue'),
    meta: { requiresAuth: false }
  },

  // Protected routes
  {
    path: '/',
    name: 'NicheSelector',
    component: () => import('@/views/NicheSelectorView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/niches/new',
    name: 'CreateNiche',
    component: () => import('@/views/CreateNicheView.vue'),
    meta: { requiresAuth: true }
  },
  {
    path: '/n/:nicheSlug',
    name: 'NicheWorkspace',
    component: () => import('@/views/NicheWorkspaceView.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'NicheSearch',
        component: () => import('@/views/SearchView.vue')
      },
      {
        path: 'saved',
        name: 'NicheSaved',
        component: () => import('@/views/SavedView.vue')
      },
      {
        path: 'settings',
        name: 'NicheSettings',
        component: () => import('@/views/NicheSettingsView.vue')
      },
      {
        path: 'history',
        name: 'NicheHistory',
        component: () => import('@/views/CollectionHistoryView.vue')
      }
    ]
  },

  // Admin routes
  {
    path: '/admin/collection-health',
    name: 'AdminCollectionHealth',
    component: () => import('@/views/AdminCollectionView.vue'),
    meta: { requiresAuth: true }
  },

  // Catch-all redirect
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes
})

// Auth navigation guard
router.beforeEach(async (to, _from, next) => {
  // In dev mode, bypass all auth checks
  if (devMode) {
    // Just redirect sign-in/sign-up to home
    if (to.name === 'SignIn' || to.name === 'SignUp') {
      next({ name: 'NicheSelector' })
    } else {
      next()
    }
    return
  }

  // Production mode: use Clerk auth
  try {
    const { useAuth } = await import('@clerk/vue')
    const { isSignedIn, isLoaded } = useAuth()

    const requiresAuth = to.meta.requiresAuth !== false

    // Wait for Clerk to load before making auth decisions
    if (!isLoaded.value) {
      // Don't block navigation - let ClerkLoading handle the UI
      // Just allow the navigation to proceed
      next()
      return
    }

    // Clerk is loaded, now check authentication
    if (requiresAuth && !isSignedIn.value) {
      // Not signed in but needs auth - redirect to sign-in
      next({
        name: 'SignIn',
        query: { redirect: to.fullPath }
      })
    } else if (
      !requiresAuth &&
      isSignedIn.value &&
      (to.name === 'SignIn' || to.name === 'SignUp')
    ) {
      // Signed in but on auth page - redirect to home
      const redirectTo = to.query.redirect || '/'
      next(redirectTo)
    } else {
      // All good - proceed
      next()
    }
  } catch (error) {
    console.warn('Auth not available, proceeding without guard', error)
    next()
  }
})

export default router
