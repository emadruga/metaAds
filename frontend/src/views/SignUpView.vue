<template>
  <div class="auth-page">
    <div class="auth-container">
      <div class="auth-header">
        <h1 class="auth-logo">MetAds</h1>
        <p class="auth-tagline">Create your account</p>
      </div>

      <SignUp
        :routing="'path'"
        :path="'/sign-up'"
        :signInUrl="'/sign-in'"
        :afterSignUpUrl="'/'"
      />
    </div>
  </div>
</template>

<script setup>
import { SignUp } from '@clerk/vue'
</script>

<style lang="scss" scoped>
.auth-page {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: var(--spacing-4);
}

.auth-container {
  background: white;
  padding: var(--spacing-8);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-xl);
  max-width: 420px;
  width: 100%;
}

.auth-header {
  text-align: center;
  margin-bottom: var(--spacing-6);
}

.auth-logo {
  font-size: var(--font-size-3xl);
  font-weight: 700;
  color: var(--color-gray-900);
  margin-bottom: var(--spacing-2);
}

.auth-tagline {
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
