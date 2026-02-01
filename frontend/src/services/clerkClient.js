/**
 * Clerk Auth Module
 *
 * Provides access to the Clerk auth instance outside of Vue components.
 * The auth instance is set by App.vue once Clerk is loaded.
 *
 * The useAuth() composable returns:
 * - isLoaded: Ref<boolean> - whether Clerk has initialized
 * - isSignedIn: Ref<boolean> - whether user is signed in
 * - userId: Ref<string | null> - current user ID
 * - sessionId: Ref<string | null> - current session ID
 * - getToken: Ref<Function> - function to get session token
 * - signOut: Ref<Function> - function to sign out
 */

let authInstance = null

/**
 * Set the auth instance (called from App.vue)
 */
export function setAuthInstance(auth) {
  authInstance = auth
  console.log('[ClerkClient] Auth instance set, isSignedIn:', auth?.isSignedIn?.value)
}

/**
 * Get the auth instance
 * @returns {Object|null} Auth instance or null if not initialized
 */
export function getAuthInstance() {
  return authInstance
}

/**
 * Get the current session token
 * @returns {Promise<string|null>} Session token or null if not authenticated
 */
export async function getSessionToken() {
  if (!authInstance) {
    console.warn('[ClerkClient] Auth instance not set')
    return null
  }

  // Check if signed in first
  if (!authInstance.isSignedIn?.value) {
    console.warn('[ClerkClient] User not signed in')
    return null
  }

  try {
    // getToken is a ref containing a function, so we call .value()
    const token = await authInstance.getToken.value()
    console.log('[ClerkClient] Token retrieved:', token ? 'success' : 'null')
    return token
  } catch (error) {
    console.error('[ClerkClient] Error getting token:', error)
    return null
  }
}

/**
 * Check if user is signed in
 * @returns {boolean} True if user is signed in
 */
export function isSignedIn() {
  if (!authInstance) {
    return false
  }
  return !!authInstance.isSignedIn?.value
}

/**
 * Check if Clerk is loaded
 * @returns {boolean} True if Clerk has initialized
 */
export function isLoaded() {
  if (!authInstance) {
    return false
  }
  return !!authInstance.isLoaded?.value
}

/**
 * Get current user ID
 * @returns {string|null} Current user ID or null if not authenticated
 */
export function getCurrentUserId() {
  if (!authInstance) {
    return null
  }
  return authInstance.userId?.value
}
