import * as Sentry from '@sentry/nextjs';

Sentry.init({
  dsn: process.env.SENTRY_DSN,
  tracesSampleRate: 1.0,
  profilesSampleRate: 1.0,
  enableTracing: true,
  enableProfiling: true,
  environment: process.env.NODE_ENV,
  release: process.env.npm_package_version,
  integrations: [
    new Sentry.Integrations.HttpClient({ tracing: true }),
    new Sentry.Replay(),  // Session replay
  ],
  beforeSend(event) {
    // Scrub PII
    if (event.user) event.user.ip_address = '[scrubbed]';
    return event;
  },
  // User feedback widget
  integrations: [new Sentry.FeedbackWidget({ attachButton: true })],
});