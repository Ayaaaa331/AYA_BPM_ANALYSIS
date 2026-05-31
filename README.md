# AYA BPM Analysis

Process-mining analysis for domestic and international travel declarations using `pm4py` and Python.

## Project Structure

- `final_analysis.py`: main analysis script.
- `data/`: input logs (`DomesticDeclarations.xes`, `InternationalDeclarations.xes`).
- `results/`: generated CSVs and charts.
- `tests/test_analysis_logic.py`: regression tests for KPI and conformance logic.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run Analysis

```bash
python3 final_analysis.py
```

Outputs are written to `results/`.

## Run Tests

```bash
python3 -m pytest -q
```

Note: tests cover logic functions and can run without loading XES logs.

## KPI Logic (implemented)

- `approved_cases`: case outcome is approved if the last relevant declaration state is `FINAL_APPROVED`.
- `rejected_cases`: case outcome is rejected if the last relevant declaration state is `REJECTED`.
- `open_cases`: submitted/in-progress cases without a final terminal approval/rejection.
- `approval_rate_percent`, `rejection_rate_percent`, `open_case_rate_percent`: per total cases.
- `median_duration_days`, `p90_duration_days`, `max_duration_days`: case duration metrics.
- `payment_completion_rate_percent`: share of cases with `Payment Handled`.
- `rework_case_rate_percent`: share of cases with repeated activities (minor/major rework detection).
- `conformance_violation_rate_percent`: share of cases with rule violations.

## Conformance Rules

International process:
- `Start trip` must occur after `Permit FINAL_APPROVED`.
- `End trip` must occur after `Start trip`.

Domestic and international:
- `Request Payment` must occur after `Declaration FINAL_APPROVED`.
- If `Request Payment` occurs, `Payment Handled` must exist.

## Key Result Files

- `results/kpi_summary.csv`
- `results/*_case_outcomes.csv`
- `results/*_conformance_violations.csv`
- `results/*_waiting_time_summary.csv`
- `results/*_rework_cases.csv`
- `results/*_variants.csv`
