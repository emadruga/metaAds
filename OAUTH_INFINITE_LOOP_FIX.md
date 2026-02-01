# OAuth Infinite Loop Fix

## Problem Description

After OAuth authentication completed successfully with Clerk, the application experienced an infinite redirect loop causing the entire page to flicker constantly.

## Root Cause Analysis

The infinite loop was caused by issues in the router navigation guard logic in `frontend/src/router/index.js`:

### Issue 1: Unnecessary Route Re-render
In `App.vue`, the `RouterView` component had a `:key="$route.fullPath"` prop that forced a complete component re-render on every route change, which could trigger additional navigation events.

### Issue 2: Complex Redirect Loop Prevention
The router guard had complex logic to prevent redirect loops using an `isRedirecting` flag and `afterEach` hook with timeouts. This added unnecessary complexity and timing issues.

### Issue 3: Blocking Navigation While Clerk Loads
The most critical issue: When Clerk's authentication state wasn't loaded (`isLoaded.value === false`), the guard was attempting to redirect or block navigation, which would trigger the guard again before Clerk finished loading, creating an infinite loop.

```javascript
// BEFORE (Problematic):
if (!isLoaded.value) {
  if (requiresAuth && from.name !== 'SignIn') {
    isRedirecting = true
    next({ name: 'SignIn', query: { redirect: to.fullPath }})
  } else {
    next()
  }
  return
}
```

## Solution Implemented

### 1. Removed Forced Re-render Key
**File:** `frontend/src/App.vue`

```diff
  <ClerkLoaded>
-   <RouterView :key="$route.fullPath" />
+   <RouterView />
  </ClerkLoaded>
```

**Why:** The router view doesn't need to be forced to re-render on every route change. Vue Router handles component updates automatically.

### 2. Simplified Router Guard Logic
**File:** `frontend/src/router/index.js`

Removed all the complex redirect loop prevention logic (`isRedirecting` flag, `afterEach` hook with timeouts).

### 3. Fixed Clerk Loading State Handling
The key fix: When Clerk is not loaded, **always allow navigation to proceed** and let the `ClerkLoading`/`ClerkLoaded` wrapper components in `App.vue` handle the UI state.

```javascript
// AFTER (Fixed):
if (!isLoaded.value) {
  // Don't block navigation - let ClerkLoading handle the UI
  // Just allow the navigation to proceed
  next()
  return
}
```

**Why this works:**
1. The navigation guard no longer blocks or redirects when Clerk is loading
2. The `ClerkLoading` component in `App.vue` displays a loading spinner while Clerk initializes
3. Once Clerk loads, the `ClerkLoaded` component renders the actual route
4. The navigation guard only enforces auth rules **after** Clerk has fully loaded
5. No more redirect loops because we're not trying to make navigation decisions before the auth state is known

### 4. Simplified Auth Logic After Load

```javascript
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
```

## Files Modified

1. **frontend/src/App.vue**
   - Removed `:key="$route.fullPath"` from RouterView

2. **frontend/src/router/index.js**
   - Removed `isRedirecting` flag and tracking logic
   - Removed `router.afterEach` hook
   - Simplified `beforeEach` guard to always allow navigation when Clerk is loading
   - Streamlined auth checks after Clerk loads

## Testing Instructions

1. **Start the application:**
   ```bash
   # Terminal 1 - Backend
   cd backend
   source ../venv/bin/activate
   python run.py

   # Terminal 2 - Frontend
   cd frontend
   npm run dev
   ```

2. **Test OAuth flow:**
   - Navigate to http://localhost:5173
   - Click sign in
   - Complete OAuth authentication
   - Verify: Page should load smoothly without flickering
   - Verify: You should be redirected to the niche selector page

3. **Test protected routes:**
   - Sign out
   - Try to access http://localhost:5173/niches/new directly
   - Verify: Should redirect to sign-in page
   - Sign in
   - Verify: Should redirect back to /niches/new

4. **Test public routes:**
   - While signed in, try to access /sign-in
   - Verify: Should redirect to home page (/)

## How the Auth Flow Works Now

1. **Initial Load:**
   - App loads → `ClerkLoading` shows spinner
   - Router guard allows navigation (doesn't block while loading)
   - Clerk SDK initializes in background

2. **After Clerk Loads:**
   - `ClerkLoaded` renders the actual route component
   - Router guard now has `isLoaded === true`
   - Auth checks are enforced for protected routes

3. **OAuth Redirect:**
   - User completes OAuth → Clerk redirects to configured URL
   - Router guard checks `isLoaded` (should be true now)
   - Checks `isSignedIn` (should be true after OAuth)
   - Allows navigation to proceed (user is authenticated)
   - No loops because we only check auth state when it's ready

## Key Principles Applied

1. **Separation of Concerns:**
   - UI loading state: Handled by `ClerkLoading`/`ClerkLoaded` components
   - Route protection: Handled by router guard **only after** auth state is known

2. **Avoid Premature Decisions:**
   - Never redirect based on incomplete information
   - Wait for `isLoaded` before enforcing auth rules

3. **Simplicity:**
   - Remove complex loop prevention mechanisms
   - Trust Vue Router's built-in navigation handling
   - Let Clerk's components do what they're designed to do

## Future Considerations

If you experience any auth-related issues in the future, check:

1. ✅ Is the router guard waiting for `isLoaded` before making auth decisions?
2. ✅ Are you using Clerk's `ClerkLoading`/`ClerkLoaded` components correctly?
3. ✅ Are there any unnecessary forced re-renders (`:key` props on router views)?
4. ✅ Is the Clerk publishable key correctly set in `.env`?

## Related Documentation

- [Clerk Vue Documentation](https://clerk.com/docs/references/vue/overview)
- [Vue Router Navigation Guards](https://router.vuejs.org/guide/advanced/navigation-guards.html)
- [Clerk OAuth Flow](https://clerk.com/docs/authentication/social-connections/oauth)
