# diagnostics/analyzer.py
# Runs all diagnostic rules on monitoring results.
# Produces a full diagnosis report for each device.

import sys
import time
from pathlib import Path

# Add parent directory to path so imports work when run directly
sys.path.insert(0, str(Path(__file__).parent.parent))

from logger_setup import get_logger
from diagnostics.rules import ALL_RULES, SEVERITY_OK, SEVERITY_WARNING, SEVERITY_CRITICAL

logger = get_logger(__name__)


def analyze_result(report: dict) -> dict:
    """
    Run every diagnostic rule against one monitoring result.

    Args:
        report: a connectivity result dict from Phase 2/3

    Returns:
        A full diagnosis with all rule results and overall verdict
    """

    host      = report.get("host", "unknown")
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

    # Run every rule and collect individual diagnoses
    rule_results = []
    for rule_fn in ALL_RULES:
        diagnosis = rule_fn(report)
        rule_results.append(diagnosis)

    # Overall severity = worst severity across all rules
    # ok < warning < critical
    severity_rank = {SEVERITY_OK: 0, SEVERITY_WARNING: 1, SEVERITY_CRITICAL: 2}

    worst_severity = SEVERITY_OK
    for d in rule_results:
        if severity_rank.get(d["severity"], 0) > severity_rank.get(worst_severity, 0):
            worst_severity = d["severity"]

    # Collect all active issues (non-ok results)
    active_issues = [
        d for d in rule_results
        if d["severity"] != SEVERITY_OK
    ]

    # Collect all recommendations
    recommendations = [
        d["recommendation"]
        for d in rule_results
        if d.get("recommendation")
    ]

    # Get health score from rule results
    health_score = next(
        (d.get("score") for d in rule_results if d["rule"] == "health_score"),
        None
    )

    full_diagnosis = {
        "host"            : host,
        "timestamp"       : timestamp,
        "overall_severity": worst_severity,
        "health_score"    : health_score,
        "active_issues"   : active_issues,
        "recommendations" : recommendations,
        "rule_results"    : rule_results,
        "raw_report"      : report
    }

    # Log based on severity
    if worst_severity == SEVERITY_CRITICAL:
        logger.error(
            f"CRITICAL | {host} | score={health_score} | "
            f"issues={[i['issue_type'] for i in active_issues]}"
        )
    elif worst_severity == SEVERITY_WARNING:
        logger.warning(
            f"WARNING | {host} | score={health_score} | "
            f"issues={[i['issue_type'] for i in active_issues]}"
        )
    else:
        logger.info(
            f"OK | {host} | score={health_score} | no issues"
        )

    return full_diagnosis


def analyze_all(reports: list) -> list:
    """
    Run diagnostics on a list of monitoring results.

    Args:
        reports: list of connectivity result dicts

    Returns:
        List of full diagnosis dicts
    """

    diagnoses = []
    for report in reports:
        diagnosis = analyze_result(report)
        diagnoses.append(diagnosis)

    return diagnoses


def print_diagnosis_report(diagnoses: list):
    """Print a clean diagnostic summary to the terminal."""

    print("\n" + "=" * 65)
    print("  AUTOMATED DIAGNOSTIC REPORT")
    print("=" * 65)

    for d in diagnoses:
        severity = d["overall_severity"].upper()
        score    = d["health_score"]
        host     = d["host"]

        # Visual severity indicator
        icon = {"OK": "✓", "WARNING": "~", "CRITICAL": "✗"}.get(severity, "?")

        print(f"\n  {icon} {host}")
        print(f"    Severity    : {severity}")
        print(f"    Health score: {score}/100")

        if d["active_issues"]:
            print(f"    Issues found:")
            for issue in d["active_issues"]:
                print(f"      • [{issue['severity'].upper()}] "
                      f"{issue['detail']}")

        if d["recommendations"]:
            print(f"    Recommendations:")
            for rec in d["recommendations"]:
                print(f"      → {rec}")

        if not d["active_issues"]:
            print(f"    No issues detected")

    # Summary counts
    total    = len(diagnoses)
    ok       = sum(1 for d in diagnoses if d["overall_severity"] == SEVERITY_OK)
    warnings = sum(1 for d in diagnoses if d["overall_severity"] == SEVERITY_WARNING)
    critical = sum(1 for d in diagnoses if d["overall_severity"] == SEVERITY_CRITICAL)

    print("\n" + "=" * 65)
    print(f"  Summary: {total} devices | "
          f"OK={ok} | WARNING={warnings} | CRITICAL={critical}")
    print("=" * 65)
