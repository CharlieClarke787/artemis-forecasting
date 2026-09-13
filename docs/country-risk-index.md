# Composite country risk index

`country_risk_index.py` creates a deterministic, PRS/ICRG-style **risk** score
from open indicators. It is a screening aid for Artemis forecasts, not a
forecast and not a replacement for a country briefing. The repository currently
contains no qualitative country-briefing files, so the initial scope is the
four countries named in the existing sanctions example (`import_ofac_api.py`).
Each output row says this explicitly in `qualitative_cross_check`.

## Method

The score runs from 0 (lower observed institutional/macroeconomic risk) to 100
(higher risk). Component weights are 50% governance, 25% macroeconomics and
25% civic freedom. If an indicator is missing, the available component weights
are renormalised; the output lists missing indicators. A row with no usable
component is rejected.

| Component | Indicators and transformation | Weight |
| --- | --- | --- |
| Governance | World Bank Worldwide Governance Indicators: Government Effectiveness, Political Stability/Absence of Violence, Rule of Law, and Control of Corruption. Each estimate on roughly -2.5 to +2.5 is mapped to 100 (lowest) through 0 (highest). | 50% |
| Macroeconomics | IMF DataMapper: real GDP growth (`NGDP_RPCH`) is mapped from +10% = 0 risk to -10% = 100 risk; general government gross debt (`GGXWDG_NGDP`) is mapped from 0% = 0 risk to 150% = 100 risk. Values are clamped at the endpoints. | 25% |
| Civic freedom | Freedom House *Freedom in the World* aggregate total (0–100 freedom) is reversed to risk (`100 - total`). The workbook edition one year after `--target-year` is treated as the calendar-year observation. | 25% |

The default target year is 2024. Each source uses the latest available
observation at or before that year; this means source years can differ and are
shown only through the component provenance in the rerun process. No missing
observation is imputed.

## Sources and rerun

- World Bank API: <https://data.worldbank.org/products/wdi>
- IMF DataMapper API: <https://www.imf.org/external/datamapper/api/v1>
- Freedom House workbook mirror (the workbook is published by Freedom House):
  <https://freedomhouse.org/reports/freedom-world>

Run:

```text
python country_risk_index.py --target-year 2024 --output-dir data\country-risk
```

The command downloads the open sources and writes `country_risk_index.csv`,
`country_risk_index.json`, and `source_manifest.json`. Generated outputs are
committed here as a dated, inspectable snapshot; rerunning the command may
change values when providers revise historical data.
The checked-in snapshot records any unavailable or out-of-range source values
in `source_manifest.json` and leaves the affected component blank rather than
substituting a fabricated observation.

## Limitations and qualitative cross-check

The index is not ICRG/PRS data and does not model conflict exposure, sanctions,
external financing, commodity concentration, exchange-rate stress, or analyst
judgment. The fixed min/max mappings and weights are policy choices, not
empirically calibrated probabilities. Freedom House and WGI are perceptions
and expert-coded measures with their own coverage and revision practices.
Use the score to test or challenge a qualitative briefing, then record why the
briefing agrees or differs; never infer a forecast from the band alone.
