# Expected and verified outputs

| Component | Verified result |
|---|---|
| Official analytical source | 56 rows |
| Kafka Phase B run | 57 produced = 56 official rows + 1 malformed fixture |
| Boundary validation | 56 accepted, 1 quarantined |
| Bronze Delta | 56 rows |
| Silver Delta | 56 unique business-key rows after replay |
| Delta schema proof | incompatible write rejected; proof table unchanged |
| Gold Delta | 13 regional profiles |
| RAG corpus | 445 chunks = 391 MEWA + 54 GASTAT |
| Hybrid retrieval | dense + BM25 + RRF + cross-encoder reranking |
| Grounded generation | official-document citations resolved to physical PDF pages / URLs |
| Airflow success run | 9 of 9 tasks final success |
| Controlled GX failure | negative `volume_m3` rejected and downstream Gold/RAG blocked |
| OpenLineage | real START / COMPLETE / FAIL task-stage events retained |

Representative Gold outputs:

| Region | Total water volume (m³) | Dominant source | Dominant share | Active sources |
|---|---:|---|---:|---:|
| Al-Riyadh | 1,169,478,459 | Desalinated water (SWCC) | 70.63% | 2 |
| Eastern Region | 667,705,791 | Desalinated water (SWCC) | 76.91% | 2 |
| Al-Jouf | 49,568,883 | Groundwater | 100.00% | 1 |

The source's regional sums differ from the supplied Grand Total by -1 m³ for Desalinated water and -1 m³ for Surface water. AquaLens preserves those source values and does not invent an explanation.
