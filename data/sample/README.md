# Milestone 1 real-data sample

This sample uses cadastral data from Instituto Geográfico Agustín Codazzi
(IGAC) for Pasto, Colombia (municipality code `52001`). The source is the
August 31, 2026 release, saved locally in run
`20261109T062536Z-9fp_q80e`.

- `land.json` contains three parcels from `U_TERRENO` (layer 7).
- `buildings.json` contains all six saved building features that match those
  parcels, from `U_CONSTRUCCION` (layer 3).

Match each building's `TERRENO_CODIGO` to the land `CODIGO`. Keep both
codes as text. The three parcels were selected to show one, two, and three
building matches. The files preserve the original attributes, geometry,
field definitions, and spatial reference.

The reuse terms for these exact layers still need confirmation. IGAC's
release metadata lists CC BY-SA 4.0, while Colombia's national open-data
listing shows CC BY 4.0. Credit IGAC and confirm which terms apply before
sharing the sample publicly. Keep private job, worker, and equipment
records separate from this sample.

[IGAC service directory](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer)
· [Project data dictionary](../../docs/data_dictionary.md)
