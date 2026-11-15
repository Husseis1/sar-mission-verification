# Mission Verification Report: Baltic Maritime Awareness, option D (local station, rephased, merged western AOI)

- Customer: Example Coastal Authority (fictional)
- Analysis window: 2027-05-01 00:00 UTC + 7 days, step 10 s
- Constellation: 6 satellites in 2 planes
- Tasking: min 20 s between acquisitions
- Generated: 2026-11-15 11:49 UTC by sarverify 0.1.0

**Acceptance status: PASS**

## 1. Requirements verification matrix

| ID | Requirement | Method | Criterion | Worst case | Scope | Margin | Status |
|---|---|---|---|---|---|---|---|
| MR-COV-001 | Maximum revisit over each area of interest | Analysis | Maximum revisit gap <= 12 h | 10.28 | Gotland Basin | +14.4% | PASS |
| MR-COV-002 | Mean revisit over each area of interest | Analysis | Mean revisit gap <= 7 h | 4.84 | Gotland Basin | +30.8% | PASS |
| MR-COV-003 | Imaging opportunities per area of interest | Analysis | Imaging opportunities per day >= 3.5 1/day | 5.00 | Gotland Basin | +42.9% | PASS |
| MR-LAT-001 | Acquisition-to-delivery latency (P90) | Analysis | 90th percentile delivery latency <= 120 min | 23.00 | Gulf of Finland | +80.8% | PASS |
| MR-GND-001 | Downlink capacity per satellite | Analysis | Ground contact time per day >= 60 min | 240.52 | SSO-A-2 | +300.9% | PASS |

Margins below 10% are reported as MARGINAL.

## 2. Coverage by area of interest

| AOI | Opportunities/day | Lost to conflicts | Mean revisit (h) | Max revisit (h) | P90 latency (min) | Delivered | Incidence (deg) |
|---|---|---|---|---|---|---|---|
| Gulf of Finland | 5.86 | 7 | 4.10 | 9.20 | 23.0 | 100% | 15.4 - 38.6 |
| Gotland Basin | 5.00 | 7 | 4.84 | 10.28 | 23.0 | 100% | 20.3 - 36.0 |
| Gulf of Riga | 5.00 | 7 | 4.83 | 9.74 | 23.0 | 100% | 31.6 - 43.2 |
| Bothnian Bay | 8.43 | 0 | 2.84 | 9.68 | 23.0 | 100% | 15.0 - 44.9 |
| Aland and Archipelago Sea | 6.86 | 4 | 3.50 | 9.72 | 23.0 | 100% | 15.3 - 44.8 |

## 3. Ground segment contacts

| Satellite | Contacts/day | Contact time (min/day) |
|---|---|---|
| SSO-A-1 | 28.0 | 241.1 |
| SSO-A-2 | 28.0 | 240.5 |
| SSO-A-3 | 31.0 | 252.0 |
| SSO-B-1 | 30.0 | 248.2 |
| SSO-B-2 | 28.0 | 241.5 |
| SSO-B-3 | 29.0 | 243.8 |

## 4. Single-satellite loss analysis

Each row re-runs the verification with one satellite removed, to show which requirements depend on full constellation availability.

| Lost satellite | Status | Failed requirements | Marginal requirements |
|---|---|---|---|
| SSO-A-1 | FAIL | MR-COV-001 | - |
| SSO-A-3 | FAIL | MR-COV-001 | - |
| SSO-B-1 | FAIL | MR-COV-001 | - |
| SSO-B-2 | FAIL | MR-COV-001 | MR-COV-002 |
| SSO-B-3 | FAIL | MR-COV-001 | - |
| SSO-A-2 | PASS | - | - |

## 5. Detailed results

### MR-COV-001: Maximum revisit over each area of interest

Rationale: Vessel tracks older than half a day lose operational value for the customer.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 9.20 | <= 12 h | +23.4% | PASS |
| Gotland Basin | 10.28 | <= 12 h | +14.4% | PASS |
| Gulf of Riga | 9.74 | <= 12 h | +18.8% | PASS |
| Bothnian Bay | 9.68 | <= 12 h | +19.3% | PASS |
| Aland and Archipelago Sea | 9.72 | <= 12 h | +19.0% | PASS |

### MR-COV-002: Mean revisit over each area of interest

Rationale: Supports a three-to-four-times-daily maritime picture.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 4.10 | <= 7 h | +41.4% | PASS |
| Gotland Basin | 4.84 | <= 7 h | +30.8% | PASS |
| Gulf of Riga | 4.83 | <= 7 h | +31.1% | PASS |
| Bothnian Bay | 2.84 | <= 7 h | +59.5% | PASS |
| Aland and Archipelago Sea | 3.50 | <= 7 h | +50.0% | PASS |

### MR-COV-003: Imaging opportunities per area of interest

Rationale: Tasking flexibility to absorb conflicts between customers and areas.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 5.86 | >= 3.5 1/day | +67.3% | PASS |
| Gotland Basin | 5.00 | >= 3.5 1/day | +42.9% | PASS |
| Gulf of Riga | 5.00 | >= 3.5 1/day | +42.9% | PASS |
| Bothnian Bay | 8.43 | >= 3.5 1/day | +140.8% | PASS |
| Aland and Archipelago Sea | 6.86 | >= 3.5 1/day | +95.9% | PASS |

### MR-LAT-001: Acquisition-to-delivery latency (P90)

Rationale: Near-real-time products for maritime surveillance.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 23.00 | <= 120 min | +80.8% | PASS |
| Gotland Basin | 23.00 | <= 120 min | +80.8% | PASS |
| Gulf of Riga | 23.00 | <= 120 min | +80.8% | PASS |
| Bothnian Bay | 23.00 | <= 120 min | +80.8% | PASS |
| Aland and Archipelago Sea | 23.00 | <= 120 min | +80.8% | PASS |

### MR-GND-001: Downlink capacity per satellite

Rationale: Daily data volume must be downlinked without onboard backlog.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| SSO-A-1 | 241.14 | >= 60 min | +301.9% | PASS |
| SSO-A-2 | 240.52 | >= 60 min | +300.9% | PASS |
| SSO-A-3 | 252.02 | >= 60 min | +320.0% | PASS |
| SSO-B-1 | 248.19 | >= 60 min | +313.7% | PASS |
| SSO-B-2 | 241.48 | >= 60 min | +302.5% | PASS |
| SSO-B-3 | 243.81 | >= 60 min | +306.3% | PASS |

## 6. Assumptions and limitations

- Circular orbits propagated analytically with secular J2 effects (RAAN precession and argument-of-latitude drift); drag and higher-order harmonics are neglected.
- An imaging opportunity is the zero-Doppler (broadside) crossing of a target, accepted when the incidence angle and look side are inside the sensor envelope.
- Revisit statistics use gaps between consecutive opportunities inside the analysis window; edge gaps at the window boundaries are excluded.
- Delivery latency assumes the acquisition is downlinked in the first contact of the same satellite that can fit the full downlink, followed by fixed ground processing time.
- Tasking conflicts are resolved per satellite by a greedy earliest-first scheduler with a minimum separation between acquisitions and an optional per-orbit acquisition budget; customer priorities and power or thermal limits beyond that budget are not modelled.
