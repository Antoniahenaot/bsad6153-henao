-- db/queries.sql: business questions answered with SQL (Week 2).
--
-- At least five queries, each answering a question from your baseline log.
-- Put the question in plain English in a comment above each query.
-- Across the five, use: two JOINs, one GROUP BY, one filter by time,
-- and one query whose answer surprised you (explain why in the comment).
--
-- Each query uses the verified saved Pasto run. Replace the run ID to review another run.

-- 1. Which municipality and release does the November 2026 download cover?
-- Baseline decision: Whether to use Pasto data for the mapping pilot.
select source_run_id, municipality_code, release_date, fetched_at
from igac.cadastral_snapshots
where source_run_id = '20261109T062536Z-9fp_q80e'
  and fetched_at >= timestamptz '2026-11-01 00:00:00+00'
  and fetched_at < timestamptz '2026-12-01 00:00:00+00';

-- 2. How many building records did IGAC return for each parcel?
-- Baseline decision: Whether the downloaded records were useful for the pilot map.
select p.codigo as parcel_code, count(b.building_id) as returned_building_count
from igac.cadastral_snapshots as s
join igac.parcels as p on p.snapshot_id = s.snapshot_id
left join igac.buildings as b
    on b.snapshot_id = p.snapshot_id and b.terreno_codigo = p.codigo
where s.source_run_id = '20261109T062536Z-9fp_q80e'
group by p.codigo
order by returned_building_count desc, parcel_code;

-- 3. How many parcels had a returned building match, and how many had none?
-- Baseline decision: Whether the download supports displaying both map layers together.
-- A missing match leaves the parcel's vacancy status unknown.
with parcel_matches as (
    select p.parcel_id, count(b.building_id) as returned_building_count
    from igac.cadastral_snapshots as s
    join igac.parcels as p on p.snapshot_id = s.snapshot_id
    left join igac.buildings as b
        on b.snapshot_id = p.snapshot_id and b.terreno_codigo = p.codigo
    where s.source_run_id = '20261109T062536Z-9fp_q80e'
    group by p.parcel_id
)
select count(*) filter (where returned_building_count > 0) as parcels_with_a_match,
       count(*) filter (where returned_building_count = 0) as parcels_without_a_match
from parcel_matches;

-- 4. How many building records would the map omit if it kept one row per building code?
-- Baseline decision: Whether the downloaded records were useful for the pilot map.
-- Surprising finding: One building code can appear on records with distinct source IDs.
with records_per_code as (
    select b.codigo, count(distinct b.object_id) as record_count
    from igac.cadastral_snapshots as s
    join igac.buildings as b on b.snapshot_id = s.snapshot_id
    where s.source_run_id = '20261109T062536Z-9fp_q80e'
    group by b.codigo
    having count(distinct b.object_id) > 1
)
select count(*) as repeated_building_codes,
       coalesce(sum(record_count - 1), 0) as building_records_omitted
from records_per_code;

-- 5. Which construction categories can the pilot display for matched Pasto parcels?
-- Baseline decision: Whether the Pasto data could help by providing map context.
-- Categories describe the saved records. Current site conditions remain unknown.
select b.construction_type, count(*) as building_records
from igac.cadastral_snapshots as s
join igac.parcels as p on p.snapshot_id = s.snapshot_id
join igac.buildings as b
    on b.snapshot_id = p.snapshot_id and b.terreno_codigo = p.codigo
where s.source_run_id = '20261109T062536Z-9fp_q80e'
group by b.construction_type
order by building_records desc, b.construction_type;
