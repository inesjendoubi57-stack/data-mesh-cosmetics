
from pathlib import Path
import json
import sys


# ==========================================
# FILE PATH
# ==========================================

CURRENT_DIR = Path(__file__).resolve().parent

SCENARIOS_PATH = (
    CURRENT_DIR.parent
    / "validators"
    / "compatibility_cases"
    / "compatibility_scenarios.json"
)


# ==========================================
# COMPARE CONTRACT FIELDS
# ==========================================

def compare_fields(old_contract, new_contract):

    changes = []
    status = "COMPATIBLE"

    old_fields = {
        field["name"]: field
        for field in old_contract.get("schema", [])
    }

    new_fields = {
        field["name"]: field
        for field in new_contract.get("schema", [])
    }

    old_names = set(old_fields)
    new_names = set(new_fields)

    # Fields removed
    for name in old_names - new_names:
        changes.append(f"Removed field: {name}")
        status = "INCOMPATIBLE"

    # Fields added
    for name in new_names - old_names:
        field = new_fields[name]

        if field.get("required", False):
            changes.append(f"Added required field: {name}")
            status = "INCOMPATIBLE"
        else:
            changes.append(f"Added optional field: {name}")

            if status != "INCOMPATIBLE":
                status = "REVIEW_REQUIRED"

    # Compare existing fields
    for name in old_names & new_names:

        old_field = old_fields[name]
        new_field = new_fields[name]

        # Data type change
        if old_field.get("type") != new_field.get("type"):
            changes.append(f"Type changed: {name}")
            status = "INCOMPATIBLE"

        # Optional field becomes required
        if (
            not old_field.get("required", False)
            and new_field.get("required", False)
        ):
            changes.append(f"Optional field became required: {name}")
            status = "INCOMPATIBLE"

        # Compare allowed values
        old_values = old_field.get("allowed_values")
        new_values = new_field.get("allowed_values")

        if old_values is not None and new_values is not None:

            removed_values = set(old_values) - set(new_values)
            added_values = set(new_values) - set(old_values)

            if removed_values:
                changes.append(
                    f"Removed allowed values from {name}: "
                    f"{sorted(removed_values)}"
                )
                status = "INCOMPATIBLE"

            if added_values:
                changes.append(
                    f"Added allowed values to {name}: "
                    f"{sorted(added_values)}"
                )

                if status != "INCOMPATIBLE":
                    status = "REVIEW_REQUIRED"

    return status, changes


# ==========================================
# COMPARE INVARIANTS
# ==========================================

def compare_invariants(old_contract, new_contract):

    old_rules = set(old_contract.get("invariants", []))
    new_rules = set(new_contract.get("invariants", []))

    removed_rules = old_rules - new_rules
    added_rules = new_rules - old_rules

    changes = []

    if removed_rules:
        changes.append(
            f"Removed invariants: {sorted(removed_rules)}"
        )

    if added_rules:
        changes.append(
            f"Added invariants: {sorted(added_rules)}"
        )

    if added_rules:
        return "INCOMPATIBLE", changes

    if removed_rules:
        return "REVIEW_REQUIRED", changes

    return "COMPATIBLE", changes


# ==========================================
# COMPARE SLA
# ==========================================

def compare_sla(old_contract, new_contract):

    old_sla = old_contract.get("sla", {})
    new_sla = new_contract.get("sla", {})

    changes = []

    for key in set(old_sla) | set(new_sla):

        old_value = old_sla.get(key)
        new_value = new_sla.get(key)

        if old_value != new_value:
            changes.append(
                f"SLA changed: {key} ({old_value} -> {new_value})"
            )

    if changes:
        return "REVIEW_REQUIRED", changes

    return "COMPATIBLE", changes


# ==========================================
# COMPARE TWO CONTRACTS
# ==========================================

def compare_contracts(old_contract, new_contract):

    all_changes = []
    statuses = []

    status, changes = compare_fields(
        old_contract, new_contract
    )
    statuses.append(status)
    all_changes.extend(changes)

    status, changes = compare_invariants(
        old_contract, new_contract
    )
    statuses.append(status)
    all_changes.extend(changes)

    status, changes = compare_sla(
        old_contract, new_contract
    )
    statuses.append(status)
    all_changes.extend(changes)

    if "INCOMPATIBLE" in statuses:
        final_status = "INCOMPATIBLE"

    elif "REVIEW_REQUIRED" in statuses:
        final_status = "REVIEW_REQUIRED"

    else:
        final_status = "COMPATIBLE"

    return final_status, all_changes


# ==========================================
# MAIN: CHECK ALL SCENARIOS
# ==========================================
def main():

    if not SCENARIOS_PATH.exists():
        print("ERROR: Scenarios JSON file not found.")
        return 1

    with open(SCENARIOS_PATH, "r", encoding="utf-8") as file:
        data = json.load(file)

    scenarios = data.get("scenarios", [])

    print("=" * 65)
    print("       DATA CONTRACT COMPATIBILITY CHECKER")
    print("=" * 65)

    passed = 0

    for scenario in scenarios:

        scenario_id = scenario["id"]
        title = scenario["title"]

        old_contract = scenario["old_contract"]
        new_contract = scenario["new_contract"]

        expected = scenario["expected_result"]

        actual, changes = compare_contracts(
            old_contract, new_contract
        )

        result = "PASS" if actual == expected else "FAIL"

        if result == "PASS":
            passed += 1

        print(f"\nScenario {scenario_id}: {title}")
        print(f"Expected: {expected}")
        print(f"Detected: {actual}")
        print(f"Result: {result}")

        for change in changes:
            print(f"  - {change}")

        if not changes:
            print("  - No compatibility changes detected.")

    print("\n" + "=" * 65)
    print(f"TOTAL: {passed}/{len(scenarios)} scenarios passed")
    print("=" * 65)

    return 0 if passed == len(scenarios) else 1

if __name__ == "__main__":
    sys.exit(main())