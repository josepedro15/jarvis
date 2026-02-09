
-- Enable extensions
create extension if not exists pg_cron;
create extension if not exists pg_net;

-- Verify if extensions are enabled
select * from pg_extension where extname in ('pg_cron', 'pg_net');

-- Define the project URL and secret
-- NOTE: You must replace 'YOUR_PROJECT_URL' and 'YOUR_CRON_SECRET' with actual values
-- Or better, we can use a simpler approach if we don't have variables in SQL:
-- Just strictly defining the jobs.

-- Job 1: Jules Session Monitor (Every 1 minute)
-- URL: https://your-project.vercel.app/api/cron/jules
SELECT cron.schedule(
  'jules-monitor',
  '* * * * *',
  $$
  select
    net.http_get(
        url:='https://jarvis-command-center.vercel.app/api/cron/jules',
        headers:='{"Authorization": "Bearer ' || current_setting('app.cron_secret', true) || '"}'::jsonb
    ) as request_id;
  $$
);

-- Note: The above uses a custom setting 'app.cron_secret'. 
-- Alternatively, hardcode the secret or pass it as a query param.
-- Given Supabase SQL Editor limitations with variables, let's provide a template.

-- =====================================================================
-- IMPORTANT: Replace configuration values below before running!
-- =====================================================================

-- 1. Enable Extensions
create extension if not exists pg_cron;
create extension if not exists pg_net;

-- 2. Schedule Jobs

-- Clean up existing jobs (optional, to avoid duplicates)


-- Jules Monitor (Every minute)
SELECT cron.schedule(
  'jules-monitor',
  '* * * * *', -- Every minute
  $$
  select
    net.http_get(
        url:='https://jarvis-1192.vercel.app/api/cron/jules',
        headers:=jsonb_build_object('Authorization', 'Bearer ZDnLEMbFT6R00AyLILlwlo5wMohiVMyWxzlN1SdDpAY')
    ) as request_id;
  $$
);

-- N8N Sync (Every 5 minutes)
SELECT cron.schedule(
  'n8n-sync',
  '*/5 * * * *', -- Every 5 minutes
  $$
  select
    net.http_get(
        url:='https://jarvis-1192.vercel.app/api/cron/n8n',
        headers:=jsonb_build_object('Authorization', 'Bearer ZDnLEMbFT6R00AyLILlwlo5wMohiVMyWxzlN1SdDpAY')
    ) as request_id;
  $$
);

-- Metrics Aggregator (Every hour)
SELECT cron.schedule(
  'metrics-aggregator',
  '0 * * * *', -- Hourly
  $$
  select
    net.http_get(
        url:='https://jarvis-1192.vercel.app/api/cron/metrics',
        headers:=jsonb_build_object('Authorization', 'Bearer ZDnLEMbFT6R00AyLILlwlo5wMohiVMyWxzlN1SdDpAY')
    ) as request_id;
  $$
);
