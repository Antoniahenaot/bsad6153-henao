# Milestone 1 Data Dictionary

## Source and scope

**Provisional source:** Instituto Geográfico Agustín Codazzi (IGAC), Pasto, Colombia. Both the API and the pilot city are pending instructor approval.

The fetch used the August 31, 2026 release and filtered both layers to Pasto (`52001`). The land layer is `U_TERRENO` (layer 7), and the building layer is `U_CONSTRUCCION` (layer 3). These layers give the equipment management project map context for job sites. Machine hours, maintenance, and equipment assignments come from the business's own records.

The **full saved run** contained 500 distinct valid land records and 1,218 related building records. Of the 500 parcels, 422 had at least one building match and 78 had no match returned. The **field examples and sample observations** below come from inspecting six saved land records and six saved building records. The 12-record inspection does not establish how common a field value or missing value is across the full dataset.

Sources: [IGAC service directory](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer) and [official layer schemas](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer/layers).

## Fields

The tables cover 15 attributes across the two layers. “Nullable” means the published schema allows the field to have a JSON `null` value. A field can be present with a `null` value or absent from a response, so the fetch checks required identifiers before counting a record. All listed attribute keys were present in the 12 inspected records. Numeric examples are rounded for readability.

### Urban land

| Field | Type | Meaning | Saved example | Nullable? |
|---|---|---|---|---|
| `OBJECTID` | Integer ID | Identifies a row in the land layer for this release. | `3282148` | No |
| `CODIGO` | Text | Current 30-digit cadastral parcel code. | `520010103000003330005000000000` | No |
| `MANZANA_CODIGO` | Text | Code for the city block containing the parcel. | `52001010300000333` | Yes |
| `CODIGO_ANTERIOR` | Text | Previous cadastral code for the parcel. | `52001010303330005000` | Yes |
| `codigo_municipio` | Text | Municipality code. The fetch uses it to select Pasto. | `52001` | Yes |
| `CODIGO_DEPARTAMENTO` | Text | Department code. | `null` | Yes |
| `Shape__Area` | Decimal number | Area value reported for the parcel polygon. | `1392.0516` | Yes |
| `Shape__Length` | Decimal number | Boundary length reported for the parcel polygon. | `150.1138` | Yes |

### Urban buildings

| Field | Type | Meaning | Saved example | Nullable? |
|---|---|---|---|---|
| `OBJECTID` | Integer ID | Identifies a row in the building layer for this release. | `5376636` | No |
| `CODIGO` | Text | Cadastral code recorded on the building row. | `520010103000000230901901000000` | No |
| `TERRENO_CODIGO` | Text | Parcel code used to match the building to the land layer. | `520010103000000230901900000000` | Yes |
| `TIPO_CONSTRUCCION` | Text | IGAC's construction category. | `CONVENCIONAL` | No |
| `codigo_municipio` | Text | Municipality code. The fetch uses it to select Pasto. | `52001` | Yes |
| `Shape__Area` | Decimal number | Area value reported for the building footprint. | `135.6149` | Yes |
| `Shape__Length` | Decimal number | Boundary length reported for the building footprint. | `56.0482` | Yes |

The API returns `geometry` separately from the attributes. All 12 inspected records had polygon geometry, and both sample pages reported Web Mercator (EPSG:3857). The project can use the polygons to draw the parcel boundaries and building footprints. The units of the reported area and length values and the survey accuracy of the shapes have not been verified.

## Record IDs and relationships

Use `OBJECTID` to identify a row within its layer and release and to order pages during a fetch. Keep cadastral codes as text so all digits, including any leading zeros, are preserved.

Match a building's `TERRENO_CODIGO` to the land layer's `CODIGO`. One parcel can have several building rows. A building row with a missing or invalid parcel code cannot be matched by this method. Keep unmatched parcels in the land data and report the number without a building match separately.

## Verified data surprises

1. **A building can have a different code from its parcel.** In the inspected sample, building `5376636` had `CODIGO` ending in `901000000` and `TERRENO_CODIGO` ending in `900000000`. The two fields serve different purposes in the match.
2. **Two building rows can share the same cadastral codes.** In the inspected sample, buildings `5376670` and `5376714` shared both `CODIGO` and `TERRENO_CODIGO`. One was `CONVENCIONAL` and the other was `NO CONVENCIONAL`. Treating building `CODIGO` as a unique row ID would drop a record.
3. **The department field can be present but empty.** All six inspected land rows had `codigo_municipio = "52001"` and `CODIGO_DEPARTAMENTO = null`. The department field is therefore unsuitable as a required field for this sample.
4. **Some parcels had no building match.** In the full run, 78 of 500 parcels had no building match returned by the queried layer. Their vacancy status is unknown.

## Update behavior

IGAC documents monthly publication for the national open cadastral dataset. The URL used for this run is for the August 31, 2026 snapshot. We have not verified that the same URL updates in place. For a newer release, check the official catalog for its endpoint, confirm that it still covers the pilot city and provides the required fields, and save it separately with its release date and fetch date.

Compare records across releases by parcel code where the code still matches. Flag codes that appear or disappear for review, since a change in code can affect a match. `OBJECTID` identifies rows within a release, and its stability across releases has not been verified.

Sources: [IGAC release metadata](https://metadatos.icde.gov.co/geonetwork/srv/api/records/0eaaf959-4229-43f9-8e9d-970a9daf43ed?language=all) and [IGAC open geospatial data catalog](https://www.igac.gov.co/datos-abiertos/datos-abiertos-geoespaciales).

## Ethical use and attribution

Credit IGAC and record the release date when using the data. The exact license for public display of the hosted layers still needs confirmation. IGAC's detailed release metadata lists **CC BY-SA 4.0**, while Colombia's national open-data portal lists **CC BY 4.0**. Both licenses require attribution, and ShareAlike adds conditions when sharing adapted data. Confirm which terms apply to the exact layers before publishing a map or a data sample.

Use the shapes as reference information for planning. Label the source and release date so readers know the map reflects a particular snapshot. Keep worker information, private job details, and equipment assignments separate from the public map.

Sources: [IGAC's release and reuse terms](https://metadatos.icde.gov.co/geonetwork/srv/api/records/0eaaf959-4229-43f9-8e9d-970a9daf43ed?language=all), [national open-data listing](https://www.datos.gov.co/en/dataset/Base-Catastral-P-blica-del-Gestor-IGAC-08-2026/ny62-ftfh), [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), and [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).
