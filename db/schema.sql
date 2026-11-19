-- db/schema.sql: your database design (Week 2), extended in Weeks 3 and 6.
--
-- Design on paper first, using docs/data_dictionary.md, then build it here.
-- Required (see the Week 2 page):
--   * at least 3 related tables that match the real entities in your data
--   * a primary key on every table; keep the source's natural ID with a UNIQUE constraint
--   * foreign keys for every relationship
--   * real data types (timestamptz, integer, numeric, text), not text for everything
--   * NOT NULL and CHECK constraints that encode what you learned about the data
--   * audit columns on every table: first_seen_at and last_updated_at
--
-- Week 3 adds sync_runs. Week 6 adds agent_runs and agent_proposals.
-- Use identity columns (generated always as identity) for IDs you create yourself.
--
begin;

create schema igac;
revoke all on schema igac from public, anon, authenticated;

-- One snapshot represents one saved IGAC download.
create table igac.cadastral_snapshots (
    snapshot_id        bigint generated always as identity primary key,
    source_run_id      text not null unique check (source_run_id ~ '[^[:space:]]'),
    release_date       date not null,
    fetched_at         timestamptz not null,
    municipality_code  text not null check (municipality_code ~ '^[0-9]{5}$'),
    land_layer_url     text not null check (land_layer_url ~ '[^[:space:]]'),
    building_layer_url text not null check (building_layer_url ~ '[^[:space:]]'),
    geometry_srid      integer not null check (geometry_srid = 3857),
    first_seen_at      timestamptz not null default now(),
    last_updated_at    timestamptz not null default now()
);

create table igac.parcels (
    parcel_id       bigint generated always as identity primary key,
    snapshot_id     bigint not null references igac.cadastral_snapshots (snapshot_id),
    object_id       bigint not null check (object_id > 0),
    codigo          text not null check (codigo ~ '^[0-9]{30}$'),
    manzana_codigo  text,
    codigo_anterior text,
    department_code text,
    shape_area      double precision,
    shape_length    double precision,
    geometry        jsonb,
    first_seen_at   timestamptz not null default now(),
    last_updated_at timestamptz not null default now(),
    unique (snapshot_id, object_id),
    unique (snapshot_id, codigo)
);

create table igac.buildings (
    building_id       bigint generated always as identity primary key,
    snapshot_id       bigint not null,
    object_id         bigint not null check (object_id > 0),
    codigo            text not null check (codigo ~ '^[0-9]{30}$'),
    terreno_codigo    text not null check (terreno_codigo ~ '^[0-9]{30}$'),
    construction_type text not null check (construction_type ~ '[^[:space:]]'),
    shape_area        double precision,
    shape_length      double precision,
    geometry          jsonb,
    first_seen_at     timestamptz not null default now(),
    last_updated_at   timestamptz not null default now(),
    unique (snapshot_id, object_id),
    foreign key (snapshot_id, terreno_codigo)
        references igac.parcels (snapshot_id, codigo)
);

create index buildings_parcel_idx on igac.buildings (snapshot_id, terreno_codigo);

revoke all on all tables in schema igac from public, anon, authenticated;
revoke all on all sequences in schema igac from public, anon, authenticated;

commit;

-- Geometry stores the source ArcGIS JSON. The snapshot records its SRID.
-- On updates, the loader preserves first_seen_at and sets last_updated_at.
