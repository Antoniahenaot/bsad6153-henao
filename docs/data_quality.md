# Milestone 2 Data Quality Analysis

## Data checked

I checked all five land pages and 25 building pages from the saved Instituto Geográfico Agustín Codazzi (IGAC) run for Pasto, Colombia. The August 31, 2026 release included `U_TERRENO` (layer 7) and `U_CONSTRUCCION` (layer 3). The saved run (`20261109T062536Z-9fp_q80e`) contained 500 parcel records and 1,218 building records. The relationship counts below agree with `complete.json`. [Data dictionary and source details](data_dictionary.md)

## Missing values

The check counted absent fields, JSON `null` values, and blank text separately. `CODIGO_DEPARTAMENTO` was present with a `null` value in all 500 parcel records. Every other saved attribute in both layers was present and had zero `null` values or blank strings. This check covers the attributes requested by the fetch script. It does not establish that their values are accurate or current.

## Duplicate IDs and repeated cadastral codes

| Layer and field | Distinct values | Values appearing more than once |
|---|---:|---:|
| Parcel `OBJECTID` | 500 | 0 |
| Building `OBJECTID` | 1,218 | 0 |
| Parcel `CODIGO` | 500 | 0 |
| Building `CODIGO` | 422 | 325 |
| Building `TERRENO_CODIGO` | 422 | 325 |

Every `OBJECTID` was a positive integer, and every checked cadastral code was a 30-digit string. Use `OBJECTID` to identify records within each layer for this release. Do not remove building rows just because they share a cadastral code. Several building records can link to the same parcel.

## Parcel and building relationships

I matched each building's `TERRENO_CODIGO` to the parcel's `CODIGO`. All 1,218 building records matched exactly one parcel. No building had a missing or invalid join code, zero parcel matches, or multiple parcel matches.

Of the 500 parcels, 422 had at least one building match and **78 had no building match returned in the saved run**. The vacancy status of those 78 parcels is unknown. The fetch requested buildings for the selected parcels, so these counts describe the saved run. They cannot measure building coverage across all of Pasto.

## Geographic fairness check

All 500 parcel rows and all 1,218 building rows had municipality code `52001` (Pasto). The construction machinery business operates in Manizales. The saved data can demonstrate parcel and building links for Pasto, but it provides no evidence about the quality or completeness of map coverage for Manizales crews. This check did not compare cities or measure whether some neighborhoods have better coverage than others.

Treat map coverage for Manizales job sites as unverified. Use the business's hour-meter readings and service records to decide which machines need maintenance.
