-- Milestone 3 Part E: IGAC Pasto quality checks. Execute as app_reader.
-- Every result includes a UTC measurement timestamp from one consistent snapshot.
-- No source writes, temporary tables, functions, extensions, or migrations.
-- Empty tables produce zero count results but no field-rate rows (no denominator).
-- Historical versions are intentional: source duplicates are checked WITHIN snapshots.
-- Counts below are measurements to run, not findings already established.

begin transaction isolation level repeatable read read only;
set local statement_timeout = '30s';
set local extra_float_digits = 3;

-- 1. Physical row counts. Parcels/buildings include all historical versions.
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       'cadastral_snapshots' as table_name, count(*) as row_count
from igac.cadastral_snapshots
union all
select timezone('UTC', transaction_timestamp()), 'parcels', count(*) from igac.parcels
union all
select timezone('UTC', transaction_timestamp()), 'buildings', count(*) from igac.buildings
union all
select timezone('UTC', transaction_timestamp()), 'sync_runs', count(*) from igac.sync_runs;

-- 2. Per-snapshot scope. Fetch time is not the source release date or last sync check.
-- Separate counts avoid multiplying parcels by their associated buildings.
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       s.snapshot_id, s.source_run_id, s.release_date, s.fetched_at,
       s.municipality_code, s.geometry_srid,
       (select count(*) from igac.parcels p where p.snapshot_id = s.snapshot_id) as parcels,
       (select count(*) from igac.buildings b where b.snapshot_id = s.snapshot_id) as buildings
from igac.cadastral_snapshots s
order by s.snapshot_id;

-- 3. Null and blank rates for all stored fields (including important source fields).
-- Database NULL cannot distinguish an absent API field from explicit JSON null.
-- Some sync fields are intentionally nullable; interpret using run status.
with records as (
    select 'parcels' as table_name, p.snapshot_id::text as scope, to_jsonb(p) as attributes
    from igac.parcels p
    union all
    select 'buildings', b.snapshot_id::text, to_jsonb(b) from igac.buildings b
    union all
    select 'cadastral_snapshots', s.snapshot_id::text, to_jsonb(s)
    from igac.cadastral_snapshots s
    union all
    select 'sync_runs', 'status=' || r.status, to_jsonb(r) from igac.sync_runs r
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       table_name, scope, f.key as field, count(*) as denominator,
       count(*) filter (where f.value = 'null'::jsonb) as null_count,
       round(100.0 * count(*) filter (where f.value = 'null'::jsonb)
             / nullif(count(*), 0), 2) as null_percent,
       count(*) filter (where jsonb_typeof(f.value) = 'string'
                         and btrim(f.value #>> '{}') = '') as blank_count,
       round(100.0 * count(*) filter (where jsonb_typeof(f.value) = 'string'
                                     and btrim(f.value #>> '{}') = '')
             / nullif(count(*), 0), 2) as blank_percent
from records
cross join lateral jsonb_each(attributes) f
group by table_name, scope, f.key
order by table_name, scope, field;

-- 4. Source/natural IDs. Report zeros as well as positive duplicate counts.
-- OBJECTID stability across releases is unverified. Building CODIGO is NOT unique.
-- sync run_id is an operational primary key, not an IGAC natural ID.
with keys as (
    select 'parcels' as table_name, snapshot_id::text as scope,
           'OBJECTID' as key_name, object_id::text as key_value from igac.parcels
    union all
    select 'parcels', snapshot_id::text, 'CODIGO', codigo from igac.parcels
    union all
    select 'buildings', snapshot_id::text, 'OBJECTID', object_id::text from igac.buildings
    union all
    select 'cadastral_snapshots', 'all snapshots', 'source_run_id', source_run_id
    from igac.cadastral_snapshots
    union all
    select 'sync_runs', 'all runs', 'run_id', run_id::text from igac.sync_runs
), grouped as (
    select table_name, scope, key_name, key_value, count(*) as n
    from keys
    group by table_name, scope, key_name, key_value
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       table_name, scope, key_name,
       sum(n) as row_count,
       count(*) filter (where n > 1) as duplicate_groups,
       coalesce(sum(n - 1) filter (where n > 1), 0) as excess_rows
from grouped
group by table_name, scope, key_name
order by table_name, scope, key_name;

-- 5. Expected repeated building codes: preserve distinct OBJECTIDs.
with grouped as (
    select snapshot_id, codigo, count(*) as n, count(distinct object_id) as distinct_ids
    from igac.buildings
    group by snapshot_id, codigo
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       s.snapshot_id,
       count(g.codigo) as distinct_building_codes,
       count(*) filter (where g.distinct_ids > 1) as codes_with_multiple_source_ids,
       coalesce(sum(g.n - 1) filter (where g.n > 1), 0) as rows_lost_if_codes_were_deduplicated
from igac.cadastral_snapshots s
left join grouped g on g.snapshot_id = s.snapshot_id
group by s.snapshot_id
order by s.snapshot_id;

-- 6. Different-ID duplicate candidates: exact equality of STORED source payload.
-- Excludes internal IDs, OBJECTID, snapshot linkage, and audit timestamps.
-- Same codes alone are insufficient. Unstored API attributes can distinguish rows.
-- Geometry representation must match exactly; no fuzzy/spatial duplicate claim.
with records as (
    select 'parcels' as table_name, snapshot_id,
           to_jsonb(p) - array['parcel_id', 'snapshot_id', 'object_id',
                              'first_seen_at', 'last_updated_at'] as payload
    from igac.parcels p
    union all
    select 'buildings', snapshot_id,
           to_jsonb(b) - array['building_id', 'snapshot_id', 'object_id',
                              'first_seen_at', 'last_updated_at']
    from igac.buildings b
), candidates as (
    select table_name, snapshot_id, count(*) as n
    from records
    group by table_name, snapshot_id, payload
    having count(*) > 1
), scopes as (
    select s.snapshot_id, t.table_name
    from igac.cadastral_snapshots s
    cross join (values ('parcels'), ('buildings')) t(table_name)
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       s.table_name, s.snapshot_id, count(c.n) as candidate_groups,
       coalesce(sum(c.n - 1), 0) as candidate_excess_rows
from scopes s
left join candidates c on c.table_name = s.table_name and c.snapshot_id = s.snapshot_id
group by s.table_name, s.snapshot_id
order by s.table_name, s.snapshot_id;

-- 7. Source identifiers and basic geometry structure. No PostGIS assumed.
-- Geometry checks do NOT prove topology, correct location, or survey accuracy.
with records as (
    select 'parcels' as table_name, snapshot_id, object_id, codigo,
           null::text as terreno_codigo, null::text as construction_type, geometry
    from igac.parcels
    union all
    select 'buildings', snapshot_id, object_id, codigo,
           terreno_codigo, construction_type, geometry from igac.buildings
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       table_name, snapshot_id, count(*) as denominator,
       count(*) filter (where object_id is null or object_id <= 0) as invalid_object_ids,
       count(*) filter (where codigo is null or codigo !~ '^[0-9]{30}$') as invalid_codes,
       count(*) filter (where table_name = 'buildings'
                         and (terreno_codigo is null or terreno_codigo !~ '^[0-9]{30}$')) as invalid_parent_codes,
       count(*) filter (where table_name = 'buildings'
                         and (construction_type is null or btrim(construction_type) = '')) as missing_categories,
       count(*) filter (where geometry is null or geometry = 'null'::jsonb) as missing_geometry,
       count(*) filter (where geometry is not null and geometry <> 'null'::jsonb and
           case when jsonb_typeof(geometry) = 'object'
                     and jsonb_typeof(geometry -> 'rings') = 'array'
                then jsonb_array_length(geometry -> 'rings') = 0
                else true end) as malformed_or_empty_ring_containers
from records
group by table_name, snapshot_id
order by table_name, snapshot_id;

-- 8. Nonfinite/nonpositive measurements and observed finite ranges.
-- No invented maximum size threshold; units and ground accuracy remain unverified.
-- NaN/Infinity are handled explicitly, not treated as ordinary outliers.
with measurements as (
    select 'parcels' as table_name, snapshot_id, shape_area, shape_length from igac.parcels
    union all
    select 'buildings', snapshot_id, shape_area, shape_length from igac.buildings
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       table_name, snapshot_id, v.field, count(*) as denominator,
       count(*) filter (where v.value is null) as missing_values,
       count(*) filter (where v.value in ('NaN'::double precision,
           'Infinity'::double precision, '-Infinity'::double precision)) as nonfinite_values,
       count(*) filter (where v.value <= 0 and v.value > '-Infinity'::double precision) as nonpositive_finite_values,
       min(v.value) filter (where v.value > '-Infinity'::double precision
                             and v.value < 'Infinity'::double precision) as minimum_finite,
       max(v.value) filter (where v.value > '-Infinity'::double precision
                             and v.value < 'Infinity'::double precision) as maximum_finite
from measurements
cross join lateral (values ('shape_area', shape_area), ('shape_length', shape_length)) v(field, value)
group by table_name, snapshot_id, v.field
order by table_name, snapshot_id, v.field;

-- 9. Audit consistency for every table, plus snapshot release/SRID checks.
with audit as (
    select 'cadastral_snapshots' as table_name, first_seen_at, last_updated_at from igac.cadastral_snapshots
    union all
    select 'parcels', first_seen_at, last_updated_at from igac.parcels
    union all
    select 'buildings', first_seen_at, last_updated_at from igac.buildings
    union all
    select 'sync_runs', first_seen_at, last_updated_at from igac.sync_runs
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc, table_name,
       count(*) as denominator,
       count(*) filter (where first_seen_at is null or last_updated_at is null) as missing_audit_times,
       count(*) filter (where last_updated_at < first_seen_at) as reversed_audit_times,
       count(*) filter (where first_seen_at > transaction_timestamp()
                         or last_updated_at > transaction_timestamp()) as future_audit_times
from audit
group by table_name
order by table_name;

select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       count(*) as denominator,
       count(*) filter (where geometry_srid <> 3857 or geometry_srid is null) as invalid_srid,
       count(*) filter (where municipality_code is null
                         or municipality_code !~ '^[0-9]{5}$') as malformed_municipality,
       count(*) filter (where release_date > timezone('UTC', transaction_timestamp())::date) as future_release_dates,
       count(*) filter (where fetched_at > transaction_timestamp()) as future_fetch_times,
       count(*) filter (where release_date > timezone('UTC', fetched_at)::date) as release_after_fetch
from igac.cadastral_snapshots;

-- 10. Orphans. Nullable snapshot_id on failed/running syncs is NOT an orphan.
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       'parcels_without_snapshot' as check_name, count(*) as row_count
from igac.parcels p
where not exists (select 1 from igac.cadastral_snapshots s where s.snapshot_id = p.snapshot_id)
union all
select timezone('UTC', transaction_timestamp()), 'buildings_without_matching_parcel', count(*)
from igac.buildings b
where not exists (select 1 from igac.parcels p
                  where p.snapshot_id = b.snapshot_id and p.codigo = b.terreno_codigo)
union all
select timezone('UTC', transaction_timestamp()), 'buildings_without_snapshot', count(*)
from igac.buildings b
where not exists (select 1 from igac.cadastral_snapshots s where s.snapshot_id = b.snapshot_id)
union all
select timezone('UTC', transaction_timestamp()), 'sync_runs_with_invalid_snapshot_reference', count(*)
from igac.sync_runs r
where r.snapshot_id is not null and not exists (
    select 1 from igac.cadastral_snapshots s where s.snapshot_id = r.snapshot_id
);

-- 11. Returned building matches per snapshot. No match does NOT mean vacant.
with matches as (
    select p.snapshot_id, p.parcel_id, count(b.building_id) as building_count
    from igac.parcels p
    left join igac.buildings b on b.snapshot_id = p.snapshot_id and b.terreno_codigo = p.codigo
    group by p.snapshot_id, p.parcel_id
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       s.snapshot_id, count(m.parcel_id) as parcels,
       count(*) filter (where m.building_count > 0) as parcels_with_matches,
       count(*) filter (where m.building_count = 0) as parcels_without_returned_matches,
       coalesce(sum(m.building_count), 0) as returned_buildings,
       round(100.0 * count(*) filter (where m.building_count = 0)
             / nullif(count(m.parcel_id), 0), 2) as unmatched_parcel_percent
from igac.cadastral_snapshots s
left join matches m on m.snapshot_id = s.snapshot_id
group by s.snapshot_id
order by s.snapshot_id;

-- 12. Construction categories are observed values, not an invented allowed list.
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       snapshot_id, construction_type, count(*) as building_rows,
       round(100.0 * count(*) / sum(count(*)) over (partition by snapshot_id), 2) as percent_of_snapshot
from igac.buildings
group by snapshot_id, construction_type
order by snapshot_id, construction_type;

-- 13. Geographic representation: counts and Pasto shares PER snapshot.
-- Municipality is snapshot metadata; ingestion checked record-level municipality.
-- Source rows do not independently retain codigo_municipio in these tables.
-- Do not sum versions into unique geographic coverage or infer city-wide coverage.
-- Compare measured coverage with the business location, Manizales, in the report.
with coverage as (
    select s.snapshot_id, s.municipality_code,
           (select count(*) from igac.parcels p where p.snapshot_id = s.snapshot_id) as parcel_rows,
           (select count(*) from igac.buildings b where b.snapshot_id = s.snapshot_id) as building_rows
    from igac.cadastral_snapshots s
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       snapshot_id, municipality_code,
       case when municipality_code = '52001' then 'Pasto' else 'Other municipality code' end as geography,
       parcel_rows, building_rows,
       round(100.0 * case when municipality_code = '52001' then parcel_rows else 0 end
             / nullif(parcel_rows, 0), 2) as pasto_parcel_share_percent,
       round(100.0 * case when municipality_code = '52001' then building_rows else 0 end
             / nullif(building_rows, 0), 2) as pasto_building_share_percent
from coverage
order by snapshot_id;

-- 14. Within-Pasto representation: observed block-level match and missing-code rates.
-- Selected blocks are not a random sample; differences do not prove discrimination.
-- Do not rank block accuracy or interpret missing building matches as vacancy.
with matches as (
    select p.snapshot_id, p.parcel_id, p.manzana_codigo,
           exists (select 1 from igac.buildings b where b.snapshot_id = p.snapshot_id
                   and b.terreno_codigo = p.codigo) as has_building
    from igac.parcels p
    join igac.cadastral_snapshots s on s.snapshot_id = p.snapshot_id
    where s.municipality_code = '52001'
)
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       snapshot_id, manzana_codigo,
       count(*) as selected_parcels,
       count(*) filter (where not has_building) as without_returned_building_matches,
       round(100.0 * count(*) filter (where not has_building) / nullif(count(*), 0), 2) as unmatched_percent,
       count(*) filter (where manzana_codigo is null or btrim(manzana_codigo) = '') as missing_block_codes
from matches
group by snapshot_id, manzana_codigo
order by snapshot_id, manzana_codigo nulls first;

-- 15. Operational quality, not proof that the dated source is current.
-- A failed run's zero counters do not measure partial downloads.
select timezone('UTC', transaction_timestamp()) as measured_at_utc,
       status, trigger_type, count(*) as runs,
       min(started_at) as earliest_start, max(finished_at) as latest_finish,
       count(*) filter (where finished_at < started_at) as reversed_run_times,
       count(*) filter (where status = 'success' and (
           snapshot_id is null or content_sha256 is null or finished_at is null
           or error_category is not null
           or records_fetched <> records_inserted + records_updated + records_unchanged
       )) as inconsistent_successes,
       count(*) filter (where status = 'failed' and (
           finished_at is null or error_category is null
       )) as inconsistent_failures,
       count(*) filter (where status = 'running' and (
           finished_at is not null or error_category is not null
       )) as inconsistent_running_states,
       count(*) filter (where records_fetched < 0 or records_inserted < 0
                         or records_updated < 0 or records_unchanged < 0) as negative_counter_rows
from igac.sync_runs
group by status, trigger_type
order by status, trigger_type;

rollback;
