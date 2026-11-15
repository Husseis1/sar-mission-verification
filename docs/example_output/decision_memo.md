# Option comparison

| Option | Mission | Satellites | Ground stations | Status | FAIL | MARGINAL | Loss cases that fail | Smallest margin |
|---|---|---|---|---|---|---|---|---|
| A | Baltic Maritime Awareness, option A (baseline) | 6 | 2 | FAIL | 3 | 1 | 6/6 | -55.4% |
| B | Baltic Maritime Awareness, option B (local station) | 6 | 3 | FAIL | 3 | 0 | 6/6 | -55.4% |
| C | Baltic Maritime Awareness, option C (local station, rephased) | 6 | 3 | FAIL | 1 | 0 | 6/6 | -22.0% |
| D | Baltic Maritime Awareness, option D (local station, rephased, merged western AOI) | 6 | 3 | PASS | 0 | 0 | 5/6 | +14.4% |

## Requirement by requirement

| Requirement | Criterion | A | B | C | D |
|---|---|---|---|---|---|
| MR-COV-001 | Maximum revisit gap <= 12 h | 18.64 (-55.4%, FAIL) | 18.64 (-55.4%, FAIL) | 14.65 (-22.0%, FAIL) | 10.28 (+14.4%, PASS) |
| MR-COV-002 | Mean revisit gap <= 7 h | 7.13 (-1.8%, FAIL) | 7.13 (-1.8%, FAIL) | 5.86 (+16.3%, PASS) | 4.84 (+30.8%, PASS) |
| MR-COV-003 | Imaging opportunities per day >= 3.5 1/day | 3.43 (-2.0%, FAIL) | 3.43 (-2.0%, FAIL) | 4.14 (+18.4%, PASS) | 5.00 (+42.9%, PASS) |
| MR-LAT-001 | 90th percentile delivery latency <= 120 min | 110.37 (+8.0%, MARGINAL) | 23.00 (+80.8%, PASS) | 23.00 (+80.8%, PASS) | 23.00 (+80.8%, PASS) |
| MR-GND-001 | Ground contact time per day >= 60 min | 189.36 (+215.6%, PASS) | 240.43 (+300.7%, PASS) | 240.52 (+300.9%, PASS) | 240.52 (+300.9%, PASS) |

## Recommendation

Option D (Baltic Maritime Awareness, option D (local station, rephased, merged western AOI)) ranks first: fewest failed requirements, then fewest marginal ones, then best resilience to losing a satellite, then the largest smallest margin.

Residual risk: losing any one of 5 satellites still breaks at least one requirement in option D; track spare capacity or replacement lead time in the program risk register.
