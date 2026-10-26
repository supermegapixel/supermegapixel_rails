# Fixture data

**Everything in this directory is invented.** These files exist so the API can be built and tested before real verification is wired up. They are not real claims, sources, outlets or scores, and nothing here describes a real organization, person or place.

## Rules

`FixtureStore` refuses to load any record that breaks one of these rules, and `tests/test_fixture_labeling.py` checks them too:

1. Claim IDs start with `clm_fixture_` and outlet IDs start with `out_fixture_`.
2. Claim text, outlet names, receipt source names and receipt quotes start with `[FIXTURE]`.
3. Every URL and outlet domain uses a reserved name (`.example`, `.invalid`, `.test`, `.localhost`, or `example.com/.net/.org`; RFC 2606 and RFC 6761), so a fixture can never point at a real site.
4. Every outlet index uses exposure basis `fixture`.

The API also labels each response it builds from this store: `meta.data_status` is `"fixture"` and every response carries the header `X-TrustBuilder-Data: fixture`. The app won't start on this store when `TRUSTBUILDER_ENV=production`.

## Scenarios the tests rely on

| ID | Scenario |
|---|---|
| `clm_fixture_0001` | Statistic. Provisional "unverifiable", then a deep check finds it contradicted (two receipts, one a released public record). Shows original and current verdicts that differ. |
| `clm_fixture_0002` | Quote. A single deep verdict, so the original and current verdicts are the same version. |
| `clm_fixture_0003` | Scientific. Still unverifiable after the deep pass: no score, band `insufficient_evidence`. |
| `clm_fixture_0004` | Historical event. A scheduled re-check lowers the verdict after a primary record turns up. |
| `out_fixture_01` | Six weekly scored snapshots; the index drifts down from 70 to 64. |
| `out_fixture_02` | One snapshot with too few claims checked (2 of a minimum 3): status `insufficient_evidence`, no index. |
| `out_fixture_03` | Three snapshots; the index falls from the `mixed` band into `leaning_faltering`. |

`outlets.json` holds weekly snapshots with 90-day rolling windows. If you add or change a scenario, update this table and the tests that use it.
