-- Fresh setup after db/schema.sql. Both role names must be unused.
-- Stop and review existing permissions if either role already exists.
-- Set passwords separately using a private client password prompt.
-- Keep passwords and connection strings out of this file.
begin;
create role igac_loader login noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
create role app_reader login noinherit nosuperuser nocreatedb nocreaterole noreplication nobypassrls;
grant usage on schema igac to igac_loader, app_reader;
grant select, insert on igac.cadastral_snapshots, igac.parcels, igac.buildings to igac_loader;
grant update (release_date, fetched_at, municipality_code, land_layer_url,
    building_layer_url, geometry_srid, last_updated_at)
    on igac.cadastral_snapshots to igac_loader;
grant update (codigo, manzana_codigo, codigo_anterior, department_code,
    shape_area, shape_length, geometry, last_updated_at)
    on igac.parcels to igac_loader;
grant update (codigo, terreno_codigo, construction_type, shape_area,
    shape_length, geometry, last_updated_at)
    on igac.buildings to igac_loader;
grant select on igac.cadastral_snapshots, igac.parcels, igac.buildings to app_reader;
commit;
-- Identity inserts require no direct sequence grants.
-- Our verified PUBLIC grants allow CONNECT and TEMPORARY, but no permanent
-- schema or table creation. Recheck shared privileges in a fresh database.
