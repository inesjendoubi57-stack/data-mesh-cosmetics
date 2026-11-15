from copy import deepcopy
from pathlib import Path
import json
import yaml


# ==========================================
# FILE PATHS
# ==========================================

CURRENT_DIR = Path(__file__).resolve().parent

CONTRACT_PATH = (
    CURRENT_DIR.parent.parent
    / "contracts"
    / "merchandising-products.yaml"
)

OUTPUT_PATH = CURRENT_DIR / "compatibility_scenarios.json"


# ==========================================
# LOAD BASE CONTRACT
# ==========================================

def load_contract():
    with open(CONTRACT_PATH, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def make_pair(base_contract, new_version="2.0.0"):
    """Create two independent copies: V1 and V2."""

    old_contract = deepcopy(base_contract)
    new_contract = deepcopy(base_contract)

    old_contract["version"] = str(
        base_contract.get("version", "1.0.0")
    )

    new_contract["version"] = new_version

    return old_contract, new_contract


def get_field(contract, field_name):
    """Find a field in the contract schema."""

    for field in contract["schema"]:
        if field.get("name") == field_name:
            return field

    raise ValueError(
        f"Field '{field_name}' does not exist in the contract."
    )


def get_unique_field_name(contract, preferred_name):
    """Avoid adding a field that already exists."""

    existing_names = {
        field["name"] for field in contract["schema"]
    }

    name = preferred_name
    counter = 1

    while name in existing_names:
        name = f"{preferred_name}_{counter}"
        counter += 1

    return name


# ==========================================
# SCENARIO 1: REMOVE AN EXISTING REQUIRED FIELD
# Expected: INCOMPATIBLE
# ==========================================

def scenario_01():
    old, new = make_pair(base_contract)

    get_field(old, "price")

    new["schema"] = [
        field for field in new["schema"]
        if field["name"] != "price"
    ]

    return {
        "id": 1,
        "title": "Remove an existing required field",
        "category": "Structural change",
        "expected_result": "INCOMPATIBLE",
        "description": "Remove the required field 'price'.",
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 2: RENAME AN EXISTING FIELD
# Expected: INCOMPATIBLE
# ==========================================

def scenario_02():
    old, new = make_pair(base_contract)

    field = get_field(new, "updated_at")
    field["name"] = "last_updated"

    return {
        "id": 2,
        "title": "Rename an existing field",
        "category": "Structural change",
        "expected_result": "INCOMPATIBLE",
        "description": "Rename 'updated_at' to 'last_updated'.",
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 3: CHANGE FIELD DATA TYPE
# Expected: INCOMPATIBLE
# ==========================================

def scenario_03():
    old, new = make_pair(base_contract)

    field = get_field(new, "price")
    field["type"] = "string"

    return {
        "id": 3,
        "title": "Change an existing field data type",
        "category": "Structural change",
        "expected_result": "INCOMPATIBLE",
        "description": "Change the type of 'price' from float to string.",
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 4: ADD A NEW REQUIRED FIELD
# Expected: INCOMPATIBLE
# ==========================================

def scenario_04():
    old, new = make_pair(base_contract)

    field_name = get_unique_field_name(
        new, "supplier_code"
    )

    new["schema"].append({
        "name": field_name,
        "type": "string",
        "required": True
    })

    return {
        "id": 4,
        "title": "Add a new required field",
        "category": "Structural change",
        "expected_result": "INCOMPATIBLE",
        "description": f"Add the required field '{field_name}'.",
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 5: CHANGE OPTIONAL FIELD TO REQUIRED
# Expected: INCOMPATIBLE
# ==========================================

def scenario_05():
    old, new = make_pair(base_contract)

    optional_fields = [
        field for field in old["schema"]
        if field.get("required", False) is False
    ]

    # If no optional field exists, create one in both versions.
    if optional_fields:
        field_name = optional_fields[0]["name"]
    else:
        field_name = get_unique_field_name(
            old, "optional_test_field"
        )

        test_field = {
            "name": field_name,
            "type": "string",
            "required": False
        }

        old["schema"].append(deepcopy(test_field))
        new["schema"].append(deepcopy(test_field))

    get_field(old, field_name)
    get_field(new, field_name)["required"] = True

    return {
        "id": 5,
        "title": "Change optional field to required",
        "category": "Structural change",
        "expected_result": "INCOMPATIBLE",
        "description": f"Change '{field_name}' from optional to required.",
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 6: ADD A NEW OPTIONAL FIELD
# Expected: REVIEW_REQUIRED
# ==========================================

def scenario_06():
    old, new = make_pair(base_contract, "1.1.0")

    field_name = get_unique_field_name(
        new, "product_color"
    )

    new["schema"].append({
        "name": field_name,
        "type": "string",
        "required": False
    })

    return {
        "id": 6,
        "title": "Add a new optional field",
        "category": "Conditional change",
        "expected_result": "REVIEW_REQUIRED",
        "description": (
            f"Add the optional field '{field_name}'. "
            "Compatibility depends on whether consumers accept extra fields."
        ),
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 7: TIGHTEN A NUMERIC CONSTRAINT
# Expected: INCOMPATIBLE
# ==========================================

def scenario_07():
    old, new = make_pair(base_contract)

    old_invariants = old.get("invariants", [])

    index = next(
        (
            i for i, rule in enumerate(old_invariants)
            if rule.replace(" ", "") == "stock_qty>=0"
        ),
        None
    )

    if index is None:
        raise ValueError(
            "Expected invariant 'stock_qty >= 0' was not found."
        )

    new["invariants"][index] = "stock_qty > 0"

    return {
        "id": 7,
        "title": "Tighten a numeric business constraint",
        "category": "Business invariant",
        "expected_result": "INCOMPATIBLE",
        "description": "Change stock_qty >= 0 to stock_qty > 0.",
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 8: REMOVE AN ALLOWED ENUM VALUE
# Expected: INCOMPATIBLE
# ==========================================

def scenario_08():
    old, new = make_pair(base_contract)

    field_name = get_unique_field_name(
        old, "contract_test_status"
    )

    test_field = {
        "name": field_name,
        "type": "string",
        "required": False
    }

    old["schema"].append(deepcopy(test_field))
    new["schema"].append(deepcopy(test_field))

    get_field(old, field_name)["allowed_values"] = [
        "active",
        "inactive",
        "discontinued"
    ]

    get_field(new, field_name)["allowed_values"] = [
        "active",
        "inactive"
    ]

    return {
        "id": 8,
        "title": "Remove an allowed enum value",
        "category": "Business invariant",
        "expected_result": "INCOMPATIBLE",
        "description": "Remove 'discontinued' from the allowed values.",
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 9: ADD A NEW ALLOWED ENUM VALUE
# Expected: REVIEW_REQUIRED
# ==========================================

def scenario_09():
    old, new = make_pair(base_contract, "1.1.0")

    field_name = get_unique_field_name(
        old, "contract_test_region"
    )

    test_field = {
        "name": field_name,
        "type": "string",
        "required": False
    }

    old["schema"].append(deepcopy(test_field))
    new["schema"].append(deepcopy(test_field))

    get_field(old, field_name)["allowed_values"] = [
        "north",
        "south"
    ]

    get_field(new, field_name)["allowed_values"] = [
        "north",
        "south",
        "east"
    ]

    return {
        "id": 9,
        "title": "Add a new allowed enum value",
        "category": "Conditional change",
        "expected_result": "REVIEW_REQUIRED",
        "description": (
            "Add 'east' to the allowed values. "
            "Consumers must tolerate unknown values."
        ),
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# SCENARIO 10: TIGHTEN FRESHNESS SLA
# Expected: REVIEW_REQUIRED
# ==========================================

def scenario_10():
    old, new = make_pair(base_contract, "1.1.0")

    old_limit = old["sla"]["freshness_max_minutes"]

    new_limit = max(1, old_limit // 2)

    if new_limit >= old_limit:
        raise ValueError(
            "Could not create a stricter freshness SLA."
        )

    new["sla"]["freshness_max_minutes"] = new_limit

    return {
        "id": 10,
        "title": "Tighten freshness SLA",
        "category": "SLA change",
        "expected_result": "REVIEW_REQUIRED",
        "description": (
            f"Reduce freshness limit from {old_limit} "
            f"to {new_limit} minutes."
        ),
        "old_contract": old,
        "new_contract": new
    }


# ==========================================
# GENERATE ALL 10 SCENARIOS
# ==========================================

def generate_scenarios():

    global base_contract

    base_contract = load_contract()

    scenarios = [
        scenario_01(),
        scenario_02(),
        scenario_03(),
        scenario_04(),
        scenario_05(),
        scenario_06(),
        scenario_07(),
        scenario_08(),
        scenario_09(),
        scenario_10()
    ]

    return scenarios


# ==========================================
# SAVE SCENARIOS TO JSON
# ==========================================

def main():

    scenarios = generate_scenarios()

    report = {
        "source_contract": base_contract.get("name"),
        "total_scenarios": len(scenarios),
        "scenarios": scenarios
    }

    with open(OUTPUT_PATH, "w", encoding="utf-8") as file:
        json.dump(
            report,
            file,
            indent=4,
            ensure_ascii=False
        )

    print("=" * 55)
    print("COMPATIBILITY SCENARIOS")
    print("=" * 55)

    for scenario in scenarios:
        print(
            f"Scenario {scenario['id']:02d}: "
            f"{scenario['title']} "
            f"--> {scenario['expected_result']}"
        )

    print("=" * 55)
    print(f"Total scenarios: {len(scenarios)}")
    print(f"JSON file generated: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()