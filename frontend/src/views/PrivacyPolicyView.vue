<template>
  <div class="privacy-page">
    <div class="privacy-container">
      <header class="privacy-header">
        <router-link to="/sign-in" class="back-link">← Back to MetAds</router-link>
        <h1>Privacy Policy</h1>
        <p class="effective-date">Effective date: March 12, 2026</p>
      </header>

      <section>
        <h2>1. Overview</h2>
        <p>
          MetAds ("we", "us", or "our") operates <strong>metads.app</strong>, a software-as-a-service
          platform that provides competitive intelligence for digital marketers by analyzing publicly
          available advertising data from the Meta Ad Library. This Privacy Policy explains what
          information we collect, how we use it, and the choices you have.
        </p>
        <p>
          By using MetAds, you agree to the practices described in this policy. If you do not agree,
          please discontinue use of the service.
        </p>
      </section>

      <section>
        <h2>2. Information We Collect</h2>

        <h3>2.1 Account Information</h3>
        <p>
          When you register for an account, we collect your email address and, optionally, your name.
          Authentication is handled by <a href="https://clerk.com" target="_blank" rel="noopener">Clerk</a>,
          a third-party identity provider. We do not store your password.
        </p>

        <h3>2.2 Meta Ad Library Data</h3>
        <p>
          MetAds uses the <strong>Meta Ad Library API</strong> to retrieve publicly available
          advertising data, including:
        </p>
        <ul>
          <li>Ad creative text (headlines, body copy, descriptions)</li>
          <li>Advertiser page names and page IDs (public information)</li>
          <li>Ad delivery dates and active status</li>
          <li>Publisher platforms (Facebook, Instagram, etc.)</li>
          <li>Ad snapshot URLs</li>
        </ul>
        <p>
          <strong>This data is entirely public.</strong> The Meta Ad Library was created by Meta
          for transparency purposes and does not include any personal information about individual
          users who saw or interacted with the ads. We do not access any Meta user's personal
          data, private messages, or non-public profile information.
        </p>

        <h3>2.3 Usage Data</h3>
        <p>
          We collect standard server logs and usage analytics to operate and improve the service,
          including pages visited, features used, and error events. This data is associated with
          your account but is not sold to third parties.
        </p>
      </section>

      <section>
        <h2>3. How We Use Your Information</h2>
        <ul>
          <li><strong>Providing the service:</strong> Storing your niches, search preferences, and
            collected ad data so your workspace persists across sessions.</li>
          <li><strong>Authentication:</strong> Verifying your identity and securing your account.</li>
          <li><strong>Improving the product:</strong> Understanding which features are used most to
            prioritize development.</li>
          <li><strong>Communications:</strong> Sending service-related notices (e.g., billing, security
            alerts). We will not send marketing emails without your explicit consent.</li>
        </ul>
      </section>

      <section>
        <h2>4. Meta Platform Data — Specific Disclosures</h2>
        <p>
          MetAds accesses Meta's Ad Library API solely to retrieve <strong>publicly available</strong>
          advertising data for competitive intelligence purposes. We comply with Meta's
          <a href="https://developers.facebook.com/terms/" target="_blank" rel="noopener">Platform Terms</a>
          and
          <a href="https://developers.facebook.com/devpolicy/" target="_blank" rel="noopener">Developer Policies</a>.
          Specifically:
        </p>
        <ul>
          <li>We do <strong>not</strong> use Meta Platform Data to target advertising to users.</li>
          <li>We do <strong>not</strong> sell, license, or transfer Meta Platform Data to any
            third party.</li>
          <li>We do <strong>not</strong> use Meta Platform Data to build user profiles beyond
            what is necessary to operate the MetAds service.</li>
          <li>We do <strong>not</strong> request or store any Meta user credentials or access
            tokens belonging to end users.</li>
          <li>Data retrieved from the Meta Ad Library API is used exclusively to display
            competitive intelligence insights within the MetAds platform.</li>
        </ul>
      </section>

      <section>
        <h2>5. Data Storage and Retention</h2>
        <p>
          Your account data and collected ad data are stored in AWS infrastructure located in the
          United States (us-east-1). We retain your account data for as long as your account is
          active. Ad Library data collected via API is retained for up to 12 months to enable
          historical trend analysis, after which older records may be automatically purged.
        </p>
        <p>
          You may request deletion of your account and all associated data at any time by
          contacting us (see Section 9).
        </p>
      </section>

      <section>
        <h2>6. Data Sharing and Third Parties</h2>
        <p>We share your information only in the following limited circumstances:</p>
        <ul>
          <li>
            <strong>Service providers:</strong> We use AWS (cloud infrastructure), Clerk
            (authentication), and standard analytics tools to operate the service. These
            providers are contractually bound to protect your data and may not use it for
            their own purposes.
          </li>
          <li>
            <strong>Legal requirements:</strong> We may disclose data if required to do so by
            law, court order, or to protect the rights and safety of MetAds, our users, or the
            public.
          </li>
          <li>
            <strong>Business transfers:</strong> In the event of a merger, acquisition, or sale
            of assets, your data may be transferred. We will notify you before your data becomes
            subject to a different privacy policy.
          </li>
        </ul>
        <p>We do <strong>not</strong> sell your personal information to third parties.</p>
      </section>

      <section>
        <h2>7. Cookies and Tracking</h2>
        <p>
          MetAds uses essential cookies and browser storage to keep you logged in and preserve
          your session. We do not use third-party advertising cookies or cross-site tracking.
          Authentication cookies are managed by Clerk and are strictly necessary for the service
          to function.
        </p>
      </section>

      <section>
        <h2>8. Your Rights</h2>
        <p>
          Depending on your location, you may have the following rights regarding your personal data:
        </p>
        <ul>
          <li><strong>Access:</strong> Request a copy of the personal data we hold about you.</li>
          <li><strong>Correction:</strong> Request that we correct inaccurate or incomplete data.</li>
          <li><strong>Deletion:</strong> Request deletion of your account and personal data.</li>
          <li><strong>Portability:</strong> Request your data in a machine-readable format.</li>
          <li><strong>Objection / Restriction:</strong> Object to or restrict certain processing
            activities.</li>
          <li><strong>Withdraw consent:</strong> Where processing is based on consent, you may
            withdraw it at any time without affecting prior lawful processing.</li>
        </ul>
        <p>
          Users in the European Economic Area (EEA) have rights under the GDPR. California
          residents have rights under the CCPA/CPRA. To exercise any right, contact us using the
          details in Section 9.
        </p>
      </section>

      <section>
        <h2>9. Contact Us</h2>
        <p>
          For privacy-related requests, questions, or complaints, please contact us at:
        </p>
        <address>
          <strong>MetAds</strong><br />
          Email: <a href="mailto:contact@metads.app">contact@metads.app</a>
        </address>
        <p>
          We will respond to all requests within 30 days.
        </p>
      </section>

      <section>
        <h2>10. Changes to This Policy</h2>
        <p>
          We may update this Privacy Policy from time to time. Material changes will be
          communicated via email or a prominent notice within the app at least 7 days before
          taking effect. Continued use of MetAds after the effective date constitutes acceptance
          of the updated policy.
        </p>
      </section>

      <footer class="privacy-footer">
        <router-link to="/sign-in">← Back to MetAds</router-link>
      </footer>
    </div>
  </div>
</template>

<script setup>
// No dynamic data needed — static page
</script>

<style lang="scss" scoped>
.privacy-page {
  min-height: 100vh;
  background: var(--color-bg-secondary, #f9fafb);
  padding: var(--spacing-8, 2rem) var(--spacing-4, 1rem);
}

.privacy-container {
  max-width: 760px;
  margin: 0 auto;
  background: white;
  border-radius: var(--radius-xl, 0.75rem);
  box-shadow: var(--shadow-md, 0 4px 6px -1px rgb(0 0 0 / 0.1));
  padding: var(--spacing-8, 2rem) var(--spacing-10, 2.5rem);

  @media (max-width: 600px) {
    padding: var(--spacing-6, 1.5rem) var(--spacing-4, 1rem);
  }
}

.privacy-header {
  border-bottom: 1px solid var(--color-border, #e5e7eb);
  margin-bottom: var(--spacing-8, 2rem);
  padding-bottom: var(--spacing-6, 1.5rem);

  h1 {
    font-size: var(--font-size-3xl, 1.875rem);
    font-weight: 700;
    color: var(--color-gray-900, #111827);
    margin: var(--spacing-3, 0.75rem) 0 var(--spacing-2, 0.5rem);
  }
}

.back-link {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-primary-600, #2563eb);
  text-decoration: none;

  &:hover {
    text-decoration: underline;
  }
}

.effective-date {
  font-size: var(--font-size-sm, 0.875rem);
  color: var(--color-text-muted, #6b7280);
}

section {
  margin-bottom: var(--spacing-8, 2rem);

  h2 {
    font-size: var(--font-size-xl, 1.25rem);
    font-weight: 600;
    color: var(--color-gray-900, #111827);
    margin-bottom: var(--spacing-3, 0.75rem);
    padding-bottom: var(--spacing-2, 0.5rem);
    border-bottom: 1px solid var(--color-border, #e5e7eb);
  }

  h3 {
    font-size: var(--font-size-base, 1rem);
    font-weight: 600;
    color: var(--color-gray-800, #1f2937);
    margin: var(--spacing-4, 1rem) 0 var(--spacing-2, 0.5rem);
  }

  p {
    color: var(--color-text-secondary, #374151);
    line-height: 1.7;
    margin-bottom: var(--spacing-3, 0.75rem);
  }

  ul {
    color: var(--color-text-secondary, #374151);
    line-height: 1.7;
    padding-left: var(--spacing-6, 1.5rem);
    margin-bottom: var(--spacing-3, 0.75rem);

    li {
      margin-bottom: var(--spacing-2, 0.5rem);
    }
  }

  a {
    color: var(--color-primary-600, #2563eb);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }

  address {
    font-style: normal;
    background: var(--color-bg-secondary, #f9fafb);
    border: 1px solid var(--color-border, #e5e7eb);
    border-radius: var(--radius-md, 0.5rem);
    padding: var(--spacing-4, 1rem);
    margin: var(--spacing-3, 0.75rem) 0;
    line-height: 1.8;

    a {
      color: var(--color-primary-600, #2563eb);
    }
  }
}

.privacy-footer {
  border-top: 1px solid var(--color-border, #e5e7eb);
  padding-top: var(--spacing-6, 1.5rem);
  margin-top: var(--spacing-4, 1rem);
  font-size: var(--font-size-sm, 0.875rem);

  a {
    color: var(--color-primary-600, #2563eb);
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}
</style>
