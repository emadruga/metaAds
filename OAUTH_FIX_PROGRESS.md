# OAuth Authentication Fix - Progress Report

**Date:** January 31, 2026
**Project:** MetAds - Competitive Intelligence Tool for Meta Ads

---

## Previous State (Phases 1-3 Completed)

As documented in `PHASES_1_2_3_COMPLETED.md`, the application had:

✅ **Backend:** Fully functional Flask API with all CRUD operations
✅ **Frontend:** Complete Vue.js UI with all components
✅ **Dev Mode:** Working local development without authentication
✅ **Database:** SQLite with all models and relationships
✅ **Components:** NicheCard, AdCard, AdGrid, SearchFilters, AdDetailPanel
✅ **Stores:** Pinia stores for niches, ads, and auth state
✅ **22 Backend Tests:** All passing

### What Was NOT Working

After configuring Clerk for production OAuth authentication:
- ❌ **Infinite redirect loop** after successful OAuth authentication
- ❌ **Page flickering** constantly after sign-in
- ❌ **401 Unauthorized errors** from backend API
- ❌ Application unusable in production mode with Clerk

---

## The Problem: OAuth Infinite Loop

### Root Cause Analysis

The flickering and redirect loop was caused by a **race condition** between Clerk authentication loading and API requests:

1. **User completes OAuth** → Clerk redirects back to app
2. **Component mounts** → `NicheSelectorView` calls `fetchNiches()` immediately
3. **API interceptor** tries to get auth token but Clerk isn't ready yet
4. **Request sent without token** → Backend returns 401 Unauthorized
5. **401 handler** sees 401 → redirects to `/sign-in` via `window.location.href`
6. **Router guard** sees user is signed in → redirects back to `/`
7. **Loop repeats** → infinite flickering

### Contributing Factors

1. **Router Guard Issue:** When `isLoaded.value === false`, the guard was trying to make navigation decisions, triggering repeated navigation events
2. **Forced Re-renders:** `RouterView` had `:key="$route.fullPath"` causing unnecessary component re-renders
3. **Premature API Calls:** Components made API requests before authentication state was ready
4. **Naive 401 Handler:** Always redirected to sign-in without checking if it was just a timing issue

---

## The Fix: Comprehensive Auth Flow Improvements

### 1. Router Guard Simplification
**File:** `frontend/src/router/index.js`

**Before:**
```javascript
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

**After:**
```javascript
if (!isLoaded.value) {
  // Don't block navigation - let ClerkLoading handle the UI
  // Just allow the navigation to proceed
  next()
  return
}
```

**Why:** Let the `ClerkLoading`/`ClerkLoaded` wrapper components in `App.vue` handle the loading state instead of trying to redirect before auth state is known.

### 2. Remove Forced Re-renders
**File:** `frontend/src/App.vue`

**Change:**
```diff
  <ClerkLoaded>
-   <RouterView :key="$route.fullPath" />
+   <RouterView />
  </ClerkLoaded>
```

**Why:** Vue Router automatically handles component updates. Forcing re-renders on every route change was causing unnecessary component lifecycle events.

### 3. Wait for Clerk in API Interceptor
**File:** `frontend/src/services/api.js` (lines 32-44)

**Added:**
```javascript
// Wait for Clerk to load before getting token
if (!isLoaded.value) {
  // Wait up to 5 seconds for Clerk to load
  await new Promise((resolve) => {
    const timeout = setTimeout(() => resolve(), 5000)
    const checkInterval = setInterval(() => {
      if (isLoaded.value) {
        clearInterval(checkInterval)
        clearTimeout(timeout)
        resolve()
      }
    }, 50)
  })
}
```

**Why:** Ensures API requests always wait for Clerk to load before attempting to get the auth token.

### 4. Smarter 401 Error Handling
**File:** `frontend/src/services/api.js` (lines 65-92)

**Added:**
```javascript
if (error.response?.status === 401 && !isDevMode) {
  // Check if we're already on an auth page
  const currentPath = window.location.pathname
  if (currentPath === '/sign-in' || currentPath === '/sign-up') {
    return Promise.reject(error)
  }

  // Check if user is actually signed out or if it's just a timing issue
  const { isSignedIn, isLoaded } = useAuth()

  if (isLoaded.value && isSignedIn.value) {
    console.warn('Got 401 but user is signed in - may be a timing issue')
    return Promise.reject(error)
  }

  // User is actually not signed in - redirect to sign-in
  if (isLoaded.value && !isSignedIn.value) {
    window.location.href = '/sign-in'
  }
}
```

**Why:** Don't redirect on 401 if we're already on auth page or if the user is actually signed in (timing issue).

### 5. Wait for Clerk in Components
**File:** `frontend/src/views/NicheSelectorView.vue` (lines 72-94)

**Added:**
```javascript
onMounted(async () => {
  // In production mode, wait for Clerk to be ready before fetching
  if (!isDevMode) {
    const { isLoaded } = useAuth()

    // Wait for Clerk to load
    if (!isLoaded.value) {
      await new Promise((resolve) => {
        const timeout = setTimeout(() => resolve(), 5000)
        const checkInterval = setInterval(() => {
          if (isLoaded.value) {
            clearInterval(checkInterval)
            clearTimeout(timeout)
            resolve()
          }
        }, 50)
      })
    }
  }

  // Now fetch niches (auth token will be available)
  nichesStore.fetchNiches()
})
```

**Why:** Components wait for Clerk to be ready before making API calls, ensuring auth tokens are available.

---

## Current State: Partially Fixed

### ✅ What's Working Now

1. **No more infinite redirect loop** - App doesn't continuously redirect between pages
2. **No more page flickering** - UI is stable after OAuth completion
3. **Router navigation works** - Can navigate between routes without loops
4. **Clerk integration stable** - Auth state loads properly
5. **Loading states display correctly** - ClerkLoading spinner shows while auth initializes

### ⚠️ What's Still Not Working

1. **401 Errors Still Occurring** - Backend is returning 401 Unauthorized for API requests
2. **Data Not Loading** - Niches and other data fail to fetch due to auth errors

**Current Error:**
```
127.0.0.1 - - [31/Jan/2026 19:25:10] "GET /api/niches HTTP/1.1" 401 -
```

This indicates that even though Clerk is loaded and the user is authenticated on the frontend, the **auth token is not being properly sent to or validated by the backend**.

---

## Next Steps: Remaining Issues to Fix

### 1. Debug Auth Token Flow ⚠️ PRIORITY

**Issue:** Backend is receiving requests without valid auth tokens

**Investigation needed:**
- [ ] Verify Clerk access token is actually being retrieved in API interceptor
- [ ] Check if token is being added to Authorization header
- [ ] Confirm backend JWT validation is working
- [ ] Ensure Clerk JWT secrets are properly configured in backend

**Debug steps:**
```javascript
// Add to frontend/src/services/api.js request interceptor
const token = await getToken()
console.log('🔑 Auth token:', token ? 'PRESENT' : 'MISSING')
console.log('🔑 Token preview:', token?.substring(0, 20) + '...')

// Add to backend/app/middleware/auth.py
print(f"🔐 Authorization header: {request.headers.get('Authorization', 'MISSING')}")
```

### 2. Backend Auth Configuration

**Check these backend files:**

**`backend/.env`:**
```env
CLERK_SECRET_KEY=sk_test_...  # Must be set
CLERK_PUBLISHABLE_KEY=pk_test_...  # Should match frontend
```

**`backend/app/middleware/auth.py`:**
- Verify JWT validation logic
- Check if Clerk webhook endpoint is configured
- Confirm DEV_AUTH_BYPASS is OFF in production

**`backend/app/config.py`:**
- Ensure Clerk credentials are loaded from environment
- Verify JWT validation settings

### 3. Frontend Token Retrieval

**Verify `getToken()` is working:**

**Test in browser console:**
```javascript
// While on the app
const { useAuth } = await import('@clerk/vue')
const { getToken, isSignedIn, isLoaded } = useAuth()
console.log('Loaded:', isLoaded.value)
console.log('Signed in:', isSignedIn.value)
const token = await getToken()
console.log('Token:', token)
```

### 4. Clerk Configuration Check

**Verify in Clerk Dashboard:**
- [ ] JWT Template is configured (if using custom claims)
- [ ] Allowed origins include `http://localhost:5173`
- [ ] OAuth redirects include your callback URLs
- [ ] API keys match between frontend and backend

### 5. Possible Solutions

#### Option A: Token Not Being Retrieved
If `getToken()` returns null even when signed in:

**Fix:** Check Clerk session configuration
```javascript
// Try with template parameter
const token = await getToken({ template: 'your-template-name' })
```

#### Option B: Token Not Being Sent
If token exists but not in request headers:

**Fix:** Verify interceptor is running
```javascript
// Add debugging
api.interceptors.request.use(async (config) => {
  console.log('🚀 Request interceptor running')
  // ... rest of code
})
```

#### Option C: Backend Not Validating Correctly
If token is sent but backend rejects it:

**Fix:** Update backend JWT validation
```python
# backend/app/middleware/auth.py
# Ensure using correct Clerk public key for verification
```

#### Option D: Use Clerk Backend SDK
For more reliable backend validation:

```bash
# In backend
pip install clerk-backend-sdk
```

```python
# backend/app/middleware/auth.py
from clerk_backend_api import Clerk

clerk = Clerk(bearer_auth=os.environ['CLERK_SECRET_KEY'])

def verify_clerk_token(token):
    try:
        session = clerk.sessions.verify_token(token)
        return session.user_id
    except Exception as e:
        return None
```

---

## Testing Checklist

Once auth token flow is fixed, verify:

- [ ] Sign in via OAuth redirects correctly
- [ ] No flickering or loops
- [ ] No 401 errors in console
- [ ] Niches load successfully after sign-in
- [ ] Can create new niche
- [ ] Can navigate to niche workspace
- [ ] Search and saved ads work
- [ ] Sign out works correctly
- [ ] Refresh page maintains auth state
- [ ] Direct URL access to protected routes works

---

## Files Modified in This Fix

### Frontend Changes
1. `frontend/src/App.vue` - Removed forced RouterView re-render key
2. `frontend/src/router/index.js` - Simplified navigation guard
3. `frontend/src/services/api.js` - Added Clerk loading wait + smarter 401 handling
4. `frontend/src/views/NicheSelectorView.vue` - Wait for Clerk before fetching data

### Documentation Created
1. `OAUTH_INFINITE_LOOP_FIX.md` - Detailed explanation of the loop fix
2. `OAUTH_FIX_PROGRESS.md` - This document

---

## Summary

### Progress Made ✅
- Fixed infinite redirect loop after OAuth
- Eliminated page flickering
- Stabilized router navigation
- Improved auth loading state handling
- Made UI usable again

### Remaining Work ⚠️
- **Critical:** Fix 401 errors - auth tokens not reaching/validating on backend
- Debug token retrieval and transmission
- Verify backend JWT validation configuration
- Test complete auth flow end-to-end

### Time Estimate
- **Auth token debugging:** 30-60 minutes
- **Backend configuration fixes:** 30 minutes
- **End-to-end testing:** 30 minutes
- **Total remaining:** ~2 hours

---

## Key Learnings

1. **Don't make navigation decisions before auth state is ready** - Let loading components handle UI while waiting
2. **Wait for auth in API interceptors** - Never send requests before tokens are available
3. **Smarter 401 handling** - Distinguish between real unauthorized access and timing issues
4. **Component lifecycle timing matters** - Don't fetch data in `onMounted` before checking auth state
5. **Separate concerns** - Router guards handle navigation, Clerk components handle loading UI, interceptors handle tokens

---

## Next Session Action Items

**Immediate priorities:**
1. Add debug logging to track auth token flow
2. Verify Clerk configuration in dashboard
3. Check backend JWT validation
4. Test token retrieval in browser console
5. Fix 401 errors
6. Verify complete auth flow works

**Once auth is working:**
- Proceed to Phase 4: Meta Ad Library API Integration
- Implement actual ad collection from Meta
- Add analytics and insights features
