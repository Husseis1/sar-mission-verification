# Mission Verification Report: Baltic Maritime Awareness, option A (baseline)

- Customer: Example Coastal Authority (fictional)
- Analysis window: 2027-05-01 00:00 UTC + 7 days, step 10 s
- Constellation: 6 satellites in 2 planes
- Tasking: min 20 s between acquisitions
- Generated: 2026-11-15 11:49 UTC by sarverify 0.1.0

**Acceptance status: FAIL**

## 1. Requirements verification matrix

| ID | Requirement | Method | Criterion | Worst case | Scope | Margin | Status |
|---|---|---|---|---|---|---|---|
| MR-COV-001 | Maximum revisit over each area of interest | Analysis | Maximum revisit gap <= 12 h | 18.64 | Archipelago Sea | -55.4% | FAIL |
| MR-COV-002 | Mean revisit over each area of interest | Analysis | Mean revisit gap <= 7 h | 7.13 | Archipelago Sea | -1.8% | FAIL |
| MR-COV-003 | Imaging opportunities per area of interest | Analysis | Imaging opportunities per day >= 3.5 1/day | 3.43 | Archipelago Sea | -2.0% | FAIL |
| MR-LAT-001 | Acquisition-to-delivery latency (P90) | Analysis | 90th percentile delivery latency <= 120 min | 110.37 | Bothnian Bay | +8.0% | MARGINAL |
| MR-GND-001 | Downlink capacity per satellite | Analysis | Ground contact time per day >= 60 min | 189.36 | SSO-B-3 | +215.6% | PASS |

Margins below 10% are reported as MARGINAL.

## 2. Coverage by area of interest

| AOI | Opportunities/day | Lost to conflicts | Mean revisit (h) | Max revisit (h) | P90 latency (min) | Delivered | Incidence (deg) |
|---|---|---|---|---|---|---|---|
| Gulf of Finland | 4.86 | 8 | 4.97 | 9.07 | 109.1 | 100% | 15.4 - 30.4 |
| Aland Sea | 4.29 | 26 | 5.65 | 10.12 | 108.9 | 100% | 19.4 - 42.5 |
| Gotland Basin | 4.00 | 0 | 6.07 | 9.62 | 108.3 | 100% | 33.4 - 36.3 |
| Gulf of Riga | 4.00 | 0 | 6.07 | 9.61 | 108.4 | 100% | 31.6 - 35.1 |
| Bothnian Bay | 8.29 | 0 | 2.90 | 9.55 | 110.4 | 100% | 15.0 - 45.0 |
| Archipelago Sea | 3.43 | 12 | 7.13 | 18.64 | 109.1 | 100% | 31.1 - 44.8 |

## 3. Ground segment contacts

| Satellite | Contacts/day | Contact time (min/day) |
|---|---|---|
| SSO-A-1 | 22.0 | 189.8 |
| SSO-A-2 | 22.0 | 189.4 |
| SSO-A-3 | 23.0 | 192.8 |
| SSO-B-1 | 23.0 | 192.7 |
| SSO-B-2 | 22.0 | 190.0 |
| SSO-B-3 | 22.0 | 189.4 |

## 4. Single-satellite loss analysis

Each row re-runs the verification with one satellite removed, to show which requirements depend on full constellation availability.

| Lost satellite | Status | Failed requirements | Marginal requirements |
|---|---|---|---|
| SSO-A-1 | FAIL | MR-COV-001, MR-COV-002, MR-COV-003 | MR-LAT-001 |
| SSO-A-2 | FAIL | MR-COV-001, MR-COV-002, MR-COV-003 | MR-LAT-001 |
| SSO-A-3 | FAIL | MR-COV-001, MR-COV-002, MR-COV-003 | MR-LAT-001 |
| SSO-B-1 | FAIL | MR-COV-001, MR-COV-002, MR-COV-003 | MR-LAT-001 |
| SSO-B-2 | FAIL | MR-COV-001, MR-COV-002, MR-COV-003 | MR-LAT-001 |
| SSO-B-3 | FAIL | MR-COV-001, MR-COV-002, MR-COV-003 | MR-LAT-001 |

## 5. Detailed results

### MR-COV-001: Maximum revisit over each area of interest

Rationale: Vessel tracks older than half a day lose operational value for the customer.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 9.07 | <= 12 h | +24.5% | PASS |
| Aland Sea | 10.12 | <= 12 h | +15.7% | PASS |
| Gotland Basin | 9.62 | <= 12 h | +19.9% | PASS |
| Gulf of Riga | 9.61 | <= 12 h | +19.9% | PASS |
| Bothnian Bay | 9.55 | <= 12 h | +20.4% | PASS |
| Archipelago Sea | 18.64 | <= 12 h | -55.4% | FAIL |

### MR-COV-002: Mean revisit over each area of interest

Rationale: Supports a three-to-four-times-daily maritime picture.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 4.97 | <= 7 h | +29.0% | PASS |
| Aland Sea | 5.65 | <= 7 h | +19.2% | PASS |
| Gotland Basin | 6.07 | <= 7 h | +13.2% | PASS |
| Gulf of Riga | 6.07 | <= 7 h | +13.2% | PASS |
| Bothnian Bay | 2.90 | <= 7 h | +58.6% | PASS |
| Archipelago Sea | 7.13 | <= 7 h | -1.8% | FAIL |

### MR-COV-003: Imaging opportunities per area of interest

Rationale: Tasking flexibility to absorb conflicts between customers and areas.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 4.86 | >= 3.5 1/day | +38.8% | PASS |
| Aland Sea | 4.29 | >= 3.5 1/day | +22.4% | PASS |
| Gotland Basin | 4.00 | >= 3.5 1/day | +14.3% | PASS |
| Gulf of Riga | 4.00 | >= 3.5 1/day | +14.3% | PASS |
| Bothnian Bay | 8.29 | >= 3.5 1/day | +136.7% | PASS |
| Archipelago Sea | 3.43 | >= 3.5 1/day | -2.0% | FAIL |

### MR-LAT-001: Acquisition-to-delivery latency (P90)

Rationale: Near-real-time products for maritime surveillance.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| Gulf of Finland | 109.05 | <= 120 min | +9.1% | MARGINAL |
| Aland Sea | 108.95 | <= 120 min | +9.2% | MARGINAL |
| Gotland Basin | 108.34 | <= 120 min | +9.7% | MARGINAL |
| Gulf of Riga | 108.43 | <= 120 min | +9.6% | MARGINAL |
| Bothnian Bay | 110.37 | <= 120 min | +8.0% | MARGINAL |
| Archipelago Sea | 109.12 | <= 120 min | +9.1% | MARGINAL |

### MR-GND-001: Downlink capacity per satellite

Rationale: Daily data volume must be downlinked without onboard backlog.

| Scope | Measured | Threshold | Margin | Status |
|---|---|---|---|---|
| SSO-A-1 | 189.81 | >= 60 min | +216.3% | PASS |
| SSO-A-2 | 189.40 | >= 60 min | +215.7% | PASS |
| SSO-A-3 | 192.81 | >= 60 min | +221.3% | PASS |
| SSO-B-1 | 192.69 | >= 60 min | +221.2% | PASS |
| SSO-B-2 | 189.95 | >= 60 min | +216.6% | PASS |
| SSO-B-3 | 189.36 | >= 60 min | +215.6% | PASS |

## 6. Assumptions and limitations

- Circular orbits propagated analytically with secular J2 effects (RAAN precession and argument-of-latitude drift); drag and higher-order harmonics are neglected.
- An imaging opportunity is the zero-Doppler (broadside) crossing of a target, accepted when the incidence angle and look side are inside the sensor envelope.
- Revisit statistics use gaps between consecutive opportunities inside the analysis window; edge gaps at the window boundaries are excluded.
- Delivery latency assumes the acquisition is downlinked in the first contact of the same satellite that can fit the full downlink, followed by fixed ground processing time.
- Tasking conflicts are resolved per satellite by a greedy earliest-first scheduler with a minimum separation between acquisitions and an optional per-orbit acquisition budget; customer priorities and power or thermal limits beyond that budget are not modelled.
