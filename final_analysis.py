import os
import pm4py
import pandas as pd
import matplotlib.pyplot as plt

os.makedirs("results", exist_ok=True)

domestic_log = pm4py.read_xes("data/DomesticDeclarations.xes")
international_log = pm4py.read_xes("data/InternationalDeclarations.xes")

domestic_df = pm4py.convert_to_dataframe(domestic_log)
international_df = pm4py.convert_to_dataframe(international_log)


def analyze_log(df, log, name):
    case_col = "case:concept:name"
    time_col = "time:timestamp"

    df[time_col] = pd.to_datetime(df[time_col])

    # Activity frequency
    activity_freq = df["concept:name"].value_counts().reset_index()
    activity_freq.columns = ["activity", "frequency"]
    activity_freq.to_csv(f"results/{name}_activity_frequency.csv", index=False)

    plt.figure(figsize=(10, 6))
    df["concept:name"].value_counts().head(10).plot(kind="bar")
    plt.title(f"Top 10 Activities - {name.capitalize()}")
    plt.xlabel("Activity")
    plt.ylabel("Frequency")
    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(f"results/{name}_top_activities.png")
    plt.close()

    # Case durations
    case_times = df.groupby(case_col)[time_col].agg(["min", "max"])
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

    # Rejections
    rejections = df[df["concept:name"].str.contains("REJECT", case=False, na=False)]
    rejection_summary = rejections["concept:name"].value_counts().reset_index()
    rejection_summary.columns = ["rejection_activity", "frequency"]
    rejection_summary.to_csv(f"results/{name}_rejection_summary.csv", index=False)

    # Waiting times
    df_sorted = df.sort_values(by=[case_col, time_col])
    waiting_rows = []

    for case_id, group in df_sorted.groupby(case_col):
        group = group.reset_index(drop=True)

        for i in range(len(group) - 1):
            waiting_rows.append({
                "case_id": case_id,
                "from": group.loc[i, "concept:name"],
                "to": group.loc[i + 1, "concept:name"],
                "waiting_days": (
                    group.loc[i + 1, time_col] - group.loc[i, time_col]
                ).total_seconds() / 86400
            })

    waiting_df = pd.DataFrame(waiting_rows)
    waiting_summary = (
        waiting_df
        .groupby(["from", "to"])["waiting_days"]
        .agg(["count", "mean", "median", "max"])
        .sort_values("mean", ascending=False)
    )
    waiting_summary.to_csv(f"results/{name}_waiting_time_summary.csv")

    # Rework
    rework_rows = []

    for case_id, group in df.groupby(case_col):
        activities = list(group["concept:name"])

        for activity in set(activities):
            count = activities.count(activity)

            if count > 1:
                rework_rows.append({
                    "case_id": case_id,
                    "activity": activity,
                    "repeat_count": count
                })

    pd.DataFrame(rework_rows).to_csv(f"results/{name}_rework_cases.csv", index=False)

    # Missing steps
    missing_rows = []

    for case_id, group in df.groupby(case_col):
        activities = list(group["concept:name"])

        if "Start trip" in activities and not any("Permit" in a for a in activities):
            missing_rows.append({"case_id": case_id, "issue": "Trip without permit"})

        if any("SUBMITTED" in a for a in activities) and not any("FINAL_APPROVED" in a for a in activities):
            missing_rows.append({"case_id": case_id, "issue": "Submission without final approval"})

        if "Request Payment" in activities and "Payment Handled" not in activities:
            missing_rows.append({"case_id": case_id, "issue": "Payment requested but not handled"})

    pd.DataFrame(missing_rows).to_csv(f"results/{name}_missing_step_cases.csv", index=False)

    # Variants
    variants = pm4py.get_variants(log)
    variant_rows = []

    for variant, frequency in variants.items():
        variant_rows.append({
            "variant": " -> ".join(variant),
            "frequency": frequency
        })

    variant_df = pd.DataFrame(variant_rows).sort_values("frequency", ascending=False)
    variant_df.to_csv(f"results/{name}_variants.csv", index=False)

    # KPIs
    total_cases = df[case_col].nunique()
    total_events = len(df)
    unique_activities = df["concept:name"].nunique()
    rejected_cases = rejections[case_col].nunique()
    approved_cases = df[df["concept:name"].str.contains("FINAL_APPROVED", case=False, na=False)][case_col].nunique()
    payment_cases = df[df["concept:name"].eq("Payment Handled")][case_col].nunique()

    return {
        "process": name,
        "total_cases": total_cases,
        "total_events": total_events,
        "unique_activities": unique_activities,
        "average_duration_days": round(case_times["duration_days"].mean(), 2),
        "median_duration_days": round(case_times["duration_days"].median(), 2),
        "max_duration_days": round(case_times["duration_days"].max(), 2),
        "rejected_cases": rejected_cases,
        "rejection_rate_percent": round(rejected_cases / total_cases * 100, 2),
        "final_approved_cases": approved_cases,
        "final_approval_rate_percent": round(approved_cases / total_cases * 100, 2),
        "payment_handled_cases": payment_cases,
        "payment_completion_rate_percent": round(payment_cases / total_cases * 100, 2),
        "number_of_variants": len(variants),
        "cases_with_rework": pd.DataFrame(rework_rows)["case_id"].nunique() if rework_rows else 0,
        "cases_with_missing_step_issue": pd.DataFrame(missing_rows)["case_id"].nunique() if missing_rows else 0
    }


domestic_kpis = analyze_log(domestic_df, domestic_log, "domestic")
international_kpis = analyze_log(international_df, international_log, "international")

kpi_df = pd.DataFrame([domestic_kpis, international_kpis])
kpi_df.to_csv("results/kpi_summary.csv", index=False)

print("Final analysis completed.")
print("All results saved in the results folder.")