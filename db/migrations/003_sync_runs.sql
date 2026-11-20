-- Apply once as the setup role, after Milestone 2 schema and roles.
-- This migration does not recreate or alter the three source tables.
begin;
create table igac.sync_runs (
    run_id uuid primary key,
    status text not null check (status in ('running', 'success', 'failed')),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    trigger_type text not null check (trigger_type in ('local', 'manual', 'scheduled')),
    github_run_id text,
    github_run_attempt integer check (github_run_attempt > 0),
    source_release date not null,
    snapshot_id bigint references igac.cadastral_snapshots(snapshot_id),
    content_sha256 text check (content_sha256 ~ '^[0-9a-f]{64}$'),
    records_fetched integer not null default 0 check (records_fetched >= 0),
    records_inserted integer not null default 0 check (records_inserted >= 0),
    records_updated integer not null default 0 check (records_updated >= 0),
    records_unchanged integer not null default 0 check (records_unchanged >= 0),
    snapshot_created boolean not null default false,
    error_category text check (error_category in ('fetch', 'validation', 'database')),
    first_seen_at timestamptz not null default now(),
    last_updated_at timestamptz not null default now(),
    check (finished_at is null or finished_at >= started_at),
    check (
        (status = 'running' and finished_at is null and error_category is null)
        or (status = 'success' and finished_at is not null and error_category is null
            and snapshot_id is not null and content_sha256 is not null
            and records_fetched = records_inserted + records_updated + records_unchanged)
        or (status = 'failed' and finished_at is not null and error_category is not null)
    )
);
create index sync_runs_started_idx on igac.sync_runs(started_at desc);
revoke all on igac.sync_runs from public, anon, authenticated;
grant select on igac.sync_runs to app_reader;
grant select, insert on igac.sync_runs to igac_loader;
grant update (status, finished_at, snapshot_id, content_sha256,
    records_fetched, records_inserted, records_updated, records_unchanged,
    snapshot_created, error_category, last_updated_at)
    on igac.sync_runs to igac_loader;
commit;
-- UUIDs are supplied by the sync; no sequence permission is required.
