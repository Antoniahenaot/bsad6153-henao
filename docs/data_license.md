# IGAC Data License and Attribution

**Verified:** November 25, 2026. Codex researched public publisher metadata with Antonia's approval; no live project database was accessed. Antonia approved using **CC BY-SA 4.0** for IGAC source data and project data-derived presentations/adaptations. This document does not authorize deployment.

## Exact source and project scope

The ingestion configuration in `ingest/fetch.py` uses release `2026-08-31`, Pasto municipality `52001`, and service `CATASTRO_PUBLICO_31082026`. The app selects original run `20261109T062536Z-9fp_q80e`. The existing snapshot's counts were verified separately, not remeasured for this licensing review.

| Component | Official source |
|---|---|
| Service/release | [CATASTRO_PUBLICO_31082026](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer) |
| Urban land | [U_TERRENO, layer 7](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer/7) |
| Urban buildings | [U_CONSTRUCCION, layer 3](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer/3) |
| Exact hosted item | [a55304e6ce4a47fb97f988ac321f1440 metadata](https://www.arcgis.com/sharing/rest/content/items/a55304e6ce4a47fb97f988ac321f1440?f=pjson) |
| IGAC release catalogue | [Bases Catastrales Nacionales Gestor IGAC 08-2026](https://metadatos.icde.gov.co/geonetwork/srv/api/records/0eaaf959-4229-43f9-8e9d-970a9daf43ed?language=all) |

## Evidence and reasoning

The service directory identifies the item above as its Service ItemId, credits IGAC, and describes the August 31, 2026 cutoff. The item's `url` matches the ingestion service. Its `licenseInfo` explicitly identifies **Creative Commons Attribution–ShareAlike 4.0 International** and describes conditions for derived products/services. The matching IGAC catalogue record independently lists the same license under Other constraints. The conclusion relies on explicit publisher licensing, not merely public access.

The repository previously recorded CC BY 4.0 on the [national data listing](https://www.datos.gov.co/en/dataset/Base-Catastral-P-blica-del-Gestor-IGAC-08-2026/ny62-ftfh). During this review that page/API did not expose readable license details through the research tool, so this field was not independently reconfirmed and the reason for the difference remains unknown. No claim is made that either portal was corrected or that the labels are equivalent. For this endpoint, the project follows the directly linked publisher item's explicit CC BY-SA 4.0 terms.

## Approved reuse and scope

The [official CC BY-SA 4.0 summary](https://creativecommons.org/licenses/by-sa/4.0/) permits sharing and adaptation, including commercial use, subject to its conditions. Follow the [legal terms](https://creativecommons.org/licenses/by-sa/4.0/legalcode.en), especially sections 3–4:

- Credit IGAC, link the source and license, identify changes, and retain applicable supplied copyright/license/disclaimer notices.
- Share project adaptations of licensed data under CC BY-SA 4.0; the project conservatively applies this notice to filtered tables and data-derived counts/charts/presentations.
- Do not suggest endorsement or add legal/technical restrictions that conflict with the license's reuse permissions.
- License permission does not establish accuracy or waive unrelated privacy rights.

This notice covers the IGAC material and project data adaptations/presentations. **It does not automatically license independent Python application code, documentation unrelated to the licensed material, dependencies, or private business records under Creative Commons.** No repository-wide software-license change was made. Whether every simple aggregate is legally an adaptation need not be asserted to use this conservative output policy.

The public app contains selected cadastral data, not private machine, worker, or customer records. Missing building matches do not prove vacancy. The sample is limited to Pasto and does not establish Manizales coverage, occupancy, safety, maintenance requirements, or measured business improvements.

## Attribution to display

**Data source:** Instituto Geográfico Agustín Codazzi (IGAC), *Base Catastral Pública del Gestor IGAC 08-2026*, cutoff August 31, 2026. Uses the Pasto, Colombia subset of U_TERRENO (layer 7) and U_CONSTRUCCION (layer 3). [Original service and layers](https://services2.arcgis.com/RVvWzU3lgJISqdke/ArcGIS/rest/services/CATASTRO_PUBLICO_31082026/FeatureServer). Copyright credit: IGAC.

**License:** [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/), as stated in the [exact source item's license information](https://www.arcgis.com/sharing/rest/content/items/a55304e6ce4a47fb97f988ac321f1440?f=pjson).

**Project changes:** Antonia Henao selected a limited Pasto sample, linked parcel and building records, and produced filtered tables, counts, and charts. Project adaptations of the licensed data and data-derived presentations are shared under CC BY-SA 4.0. The notice does not license independent application source code or dependencies. IGAC does not endorse this student project. Data is provided without warranties; the source cutoff does not establish current property conditions.

## Before deployment

The previous uncertainty about whether the exact source has an explicit license is addressed by the linked item evidence and approved license choice. The national-portal discrepancy remains unexplained. At the pre-deployment review, deployment and browser verification were still pending. Antonia subsequently reported a successful milestone-4 Render deployment and visible attribution/license notices in Safari on November 25, 2026; see app_verification.md. Final main-branch deployment and browser verification of later local display changes remain pending. If the project later needs different license terms, request clarification/permission from IGAC or use a separately licensed alternative; do not silently substitute CC BY-only terms. No request was sent to IGAC in this review.
