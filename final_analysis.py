import os
import pandas as pd
import matplotlib
import xml.etree.ElementTree as ET

matplotlib.use("Agg")
import matplotlib.pyplot as plt

os.makedirs("results", exist_ok=True)

CASE_COL = "case:concept:name"
TIME_COL = "time:timestamp"
ACTIVITY_COL = "concept:name"


def normalize_df(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out[TIME_COL] = pd.to_datetime(out[TIME_COL], utc=True, errors="coerce")
    out = out.dropna(subset=[TIME_COL, CASE_COL, ACTIVITY_COL])
    return out


def classify_case_outcome(activities: list[str], is_international: bool) -> str:
    declaration_events = [a for a in activities if "Declaration" in a]
    scope = declaration_events if declaration_events else activities

    last_submitted_idx = max((i for i, a in enumerate(scope) if "SUBMITTED" in a), default=-1)
    last_final_approved_idx = max((i for i, a in enumerate(scope) if "FINAL_APPROVED" in a), default=-1)
    last_rejected_idx = max((i for i, a in enumerate(scope) if "REJECTED" in a), default=-1)

    if last_final_approved_idx > last_rejected_idx and last_final_approved_idx >= last_submitted_idx:
        return "approved"
    if last_rejected_idx > last_final_approved_idx and last_rejected_idx >= last_submitted_idx:
        return "rejected"
    if is_international and any("Start trip" in a for a in activities):
        return "open"
    if last_submitted_idx != -1:
        return "open"
    return "unknown"


def detect_rework(activities: list[str]) -> list[dict]:
    rows = []
    seen = {}
    for idx, act in enumerate(activities):
        seen.setdefault(act, []).append(idx)

    for act, positions in seen.items():
        if len(positions) <= 1:
            continue
        has_loop = any((b - a) > 1 for a, b in zip(positions, positions[1:]))
        rows.append({
            "activity": act,
            "repeat_count": len(positions),
            "rework_type": "major" if len(positions) >= 3 else "minor",
            "is_loop_rework": has_loop,
        })
    return rows


def conformance_violations(activities: list[str], is_international: bool) -> list[str]:
    violations = []

    def first_idx(token: str) -> int:
        for i, a in enumerate(activities):
            if token in a:
                return i
        return -1

    start_trip_idx = first_idx("Start trip")
    end_trip_idx = first_idx("End trip")
    permit_final_idx = max((i for i, a in enumerate(activities) if "Permit FINAL_APPROVED" in a), default=-1)
    decl_final_idx = max((i for i, a in enumerate(activities) if "Declaration FINAL_APPROVED" in a), default=-1)
    req_payment_idx = first_idx("Request Payment")
    pay_handled_idx = first_idx("Payment Handled")

    if is_international:
        if start_trip_idx != -1 and (permit_final_idx == -1 or permit_final_idx > start_trip_idx):
            violations.append("trip_started_without_permit_final_approval")
        if end_trip_idx != -1 and (start_trip_idx == -1 or start_trip_idx > end_trip_idx):
            violations.append("trip_ended_without_valid_start")

    if req_payment_idx != -1 and (decl_final_idx == -1 or decl_final_idx > req_payment_idx):
        violations.append("payment_requested_before_declaration_final_approval")

    if req_payment_idx != -1 and pay_handled_idx == -1:
        violations.append("payment_requested_but_not_handled")

    return violations


def stage_waiting_rows(df_sorted: pd.DataFrame) -> pd.DataFrame:
    waiting_rows = []
    for case_id, group in df_sorted.groupby(CASE_COL):
        group = group.reset_index(drop=True)
        for i in range(len(group) - 1):
            waiting_rows.append({
                "case_id": case_id,
                "from": group.loc[i, ACTIVITY_COL],
                "to": group.loc[i + 1, ACTIVITY_COL],
                "waiting_days": (group.loc[i + 1, TIME_COL] - group.loc[i, TIME_COL]).total_seconds() / 86400,
            })

    return pd.DataFrame(waiting_rows)


def analyze_log(df: pd.DataFrame, variants: dict, name: str) -> dict:
    is_international = name.lower() == "international"
    df = normalize_df(df)

    activity_freq = df[ACTIVITY_COL].value_counts().reset_index()
    activity_freq.columns = ["activity", "frequency"]
    activity_freq.to_csv(f"results/{name}_activity_frequency.csv", index=False)

    plt.figure(figsize=(10, 6))
    df[ACTIVITY_COL].value_counts().head(10).plot(kind="bar")
    plt.title(f"Top 10 Activities - {name.capitalize()}")
    plt.xlabel("Activity")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(f"results/{name}_top_activities.png")
    plt.close()

    case_times = df.groupby(CASE_COL)[TIME_COL].agg(["min", "max"])
    case_times["duration_days"] = (case_times["max"] - case_times["min"]).dt.total_seconds() / 86400
    case_times.to_csv(f"results/{name}_case_durations.csv")

    plt.figure(figsize=(10, 6))
    case_times["duration_days"].plot(kind="hist", bins=50)
    plt.title(f"Case Duration Distribution - {name.capitalize()}")
    plt.xlabel("Duration in days")
    plt.ylabel("Number of cases")
    plt.tight_layout()
    plt.savefig(f"results/{name}_duration_distribution.png")
    plt.close()

    df_sorted = df.sort_values(by=[CASE_COL, TIME_COL])
    waiting_df = stage_waiting_rows(df_sorted)
    if waiting_df.empty:
        waiting_summary = pd.DataFrame(columns=["from", "to", "count", "mean", "median", "p90", "max"])
    else:
        waiting_summary = waiting_df.groupby(["from", "to"]) ["waiting_days"].agg(
            count="count",
            mean="mean",
            median="median",
            p90=lambda x: x.quantile(0.9),
            max="max",
        ).sort_values("p90", ascending=False)
    waiting_summary.to_csv(f"results/{name}_waiting_time_summary.csv")

    case_rows = []
    rework_rows = []
    violation_rows = []

    for case_id, group in df_sorted.groupby(CASE_COL):
        activities = list(group[ACTIVITY_COL])
        outcome = classify_case_outcome(activities, is_international)
        case_rows.append({"case_id": case_id, "outcome": outcome})

        for rw in detect_rework(activities):
            rework_rows.append({"case_id": case_id, **rw})

        violations = conformance_violations(activities, is_international)
        for v in violations:
            violation_rows.append({"case_id": case_id, "violation_type": v})

    case_status_df = pd.DataFrame(case_rows)
    case_status_df.to_csv(f"results/{name}_case_outcomes.csv", index=False)

    rework_df = pd.DataFrame(rework_rows)
    rework_df.to_csv(f"results/{name}_rework_cases.csv", index=False)

    violations_df = pd.DataFrame(violation_rows)
    violations_df.to_csv(f"results/{name}_conformance_violations.csv", index=False)

    missing_rows = []
    for case_id, group in df_sorted.groupby(CASE_COL):
        activities = list(group[ACTIVITY_COL])
        if is_international and "Start trip" in activities and not any("Permit" in a and "FINAL_APPROVED" in a for a in activities):
            missing_rows.append({"case_id": case_id, "issue": "Trip without permit final approval"})
        if any("SUBMITTED" in a and "Declaration" in a for a in activities) and not any("Declaration FINAL_APPROVED" in a for a in activities):
            missing_rows.append({"case_id": case_id, "issue": "Declaration submitted without final approval"})
        if "Request Payment" in activities and "Payment Handled" not in activities:
            missing_rows.append({"case_id": case_id, "issue": "Payment requested but not handled"})

    missing_df = pd.DataFrame(missing_rows)
    missing_df.to_csv(f"results/{name}_missing_step_cases.csv", index=False)

    variant_rows = [{"variant": " -> ".join(variant), "frequency": frequency} for variant, frequency in variants.items()]
    pd.DataFrame(variant_rows).sort_values("frequency", ascending=False).to_csv(f"results/{name}_variants.csv", index=False)

    total_cases = df[CASE_COL].nunique()
    approved_cases = (case_status_df["outcome"] == "approved").sum()
    rejected_cases = (case_status_df["outcome"] == "rejected").sum()
    open_cases = (case_status_df["outcome"] == "open").sum()
    payment_cases = df[df[ACTIVITY_COL].eq("Payment Handled")][CASE_COL].nunique()

    cases_with_rework = rework_df["case_id"].nunique() if not rework_df.empty else 0
    cases_with_violations = violations_df["case_id"].nunique() if not violations_df.empty else 0

    return {
        "process": name,
        "total_cases": total_cases,
        "total_events": len(df),
        "unique_activities": df[ACTIVITY_COL].nunique(),
        "median_duration_days": round(case_times["duration_days"].median(), 2),
        "p90_duration_days": round(case_times["duration_days"].quantile(0.9), 2),
        "max_duration_days": round(case_times["duration_days"].max(), 2),
        "approved_cases": int(approved_cases),
        "approval_rate_percent": round(approved_cases / total_cases * 100, 2),
        "rejected_cases": int(rejected_cases),
        "rejection_rate_percent": round(rejected_cases / total_cases * 100, 2),
        "open_cases": int(open_cases),
        "open_case_rate_percent": round(open_cases / total_cases * 100, 2),
        "payment_handled_cases": int(payment_cases),
        "payment_completion_rate_percent": round(payment_cases / total_cases * 100, 2),
        "number_of_variants": len(variants),
        "cases_with_rework": int(cases_with_rework),
        "rework_case_rate_percent": round(cases_with_rework / total_cases * 100, 2),
        "cases_with_conformance_violations": int(cases_with_violations),
        "conformance_violation_rate_percent": round(cases_with_violations / total_cases * 100, 2),
        "cases_with_missing_step_issue": int(missing_df["case_id"].nunique() if not missing_df.empty else 0),
    }


def compute_variants_from_df(df_sorted: pd.DataFrame) -> dict[tuple[str, ...], int]:
    variants: dict[tuple[str, ...], int] = {}
    for _, group in df_sorted.groupby(CASE_COL):
        key = tuple(group[ACTIVITY_COL].tolist())
        variants[key] = variants.get(key, 0) + 1
    return variants


def read_xes_to_df(file_path: str) -> pd.DataFrame:
    rows = []
    current_case = None

    for event, elem in ET.iterparse(file_path, events=("start", "end")):
        tag = elem.tag.split("}")[-1]

        if event == "start" and tag == "trace":
            current_case = None

        elif event == "end" and tag == "string" and current_case is None:
            key = elem.attrib.get("key")
            if key in {"concept:name", "id"}:
                current_case = elem.attrib.get("value")

        elif event == "end" and tag == "event":
            activity = None
            timestamp = None
            for child in elem:
                ctag = child.tag.split("}")[-1]
                key = child.attrib.get("key")
                value = child.attrib.get("value")
                if ctag == "string" and key == ACTIVITY_COL:
                    activity = value
                elif ctag == "date" and key == TIME_COL:
                    timestamp = value

            if current_case and activity and timestamp:
                rows.append({CASE_COL: current_case, ACTIVITY_COL: activity, TIME_COL: timestamp})
            elem.clear()

    return pd.DataFrame(rows)


def run_analysis() -> None:
    domestic_df = read_xes_to_df("data/DomesticDeclarations.xes")
    international_df = read_xes_to_df("data/InternationalDeclarations.xes")

    domestic_df = normalize_df(domestic_df)
    international_df = normalize_df(international_df)

    domestic_variants = compute_variants_from_df(domestic_df.sort_values([CASE_COL, TIME_COL]))
    international_variants = compute_variants_from_df(international_df.sort_values([CASE_COL, TIME_COL]))

    domestic_kpis = analyze_log(domestic_df, domestic_variants, "domestic")
    international_kpis = analyze_log(international_df, international_variants, "international")

    pd.DataFrame([domestic_kpis, international_kpis]).to_csv("results/kpi_summary.csv", index=False)

    print("Final analysis completed.")
    print("All results saved in the results folder.")


if __name__ == "__main__":
    run_analysis()
