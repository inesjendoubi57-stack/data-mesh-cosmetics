
from pathlib import Path
from datetime import datetime
import re
import yaml
import requests

from pydantic import (
    create_model,
    Field,
    ConfigDict,
    ValidationError
)


# ==========================================
# 1. CONFIGURATION
# ==========================================

BASE_DIR = Path(__file__).resolve().parent
CONTRACTS_DIR = BASE_DIR.parent / "contracts"

API_URLS = {
    "merchandising": "http://localhost:8001/api/products/",
    "fulfillment": "http://localhost:8002/api/deliveries/",
    "finance": "http://localhost:8003/api/payments/"
}

CONTRACT_FILES = {
    "merchandising": "merchandising-products.yaml",
    "fulfillment": "fulfillment-orders.yaml",
    "finance": "finance-invoices.yaml"
}


# ==========================================
# 2. LOAD YAML CONTRACT
# ==========================================

def load_contract(filename):

    path = CONTRACTS_DIR / filename

    with open(path, "r", encoding="utf-8") as file:
        contract = yaml.safe_load(file)

    print("Contract loaded:", contract["name"])

    return contract


# ==========================================
# 3. YAML TYPES -> PYTHON TYPES
# ==========================================

TYPE_MAPPING = {
    "string": str,
    "integer": int,
    "float": float,
    "datetime": datetime
}


# ==========================================
# 4. READ INVARIANTS
# ==========================================

def extract_constraints(contract):

    constraints = {}

    for rule in contract.get("invariants", []):

        match = re.fullmatch(
            r"\s*(\w+)\s*(>=|<=|>|<)\s*(-?\d+(?:\.\d+)?)\s*",
            rule
        )

        if match:

            field_name, operator, value = match.groups()
            value = float(value)

            constraints[field_name] = constraints.get(
                field_name, {}
            )

            if operator == ">":
                constraints[field_name]["gt"] = value

            elif operator == ">=":
                constraints[field_name]["ge"] = value

            elif operator == "<":
                constraints[field_name]["lt"] = value

            elif operator == "<=":
                constraints[field_name]["le"] = value

    return constraints


# ==========================================
# 5. BUILD DYNAMIC PYDANTIC MODEL
# ==========================================

def build_model(contract):

    fields = {}

    constraints = extract_constraints(contract)

    for field in contract["schema"]:

        field_name = field["name"]
        field_type = field["type"]

        if field_type not in TYPE_MAPPING:
            raise ValueError(
                f"Unsupported type: {field_type}"
            )

        python_type = TYPE_MAPPING[field_type]

        # Required or Optional
        if field["required"]:
            default = ...
        else:
            python_type = python_type | None
            default = None

        # Apply business constraints
        field_constraints = constraints.get(field_name, {})

        if field_constraints:
            definition = Field(
                default,
                **field_constraints
            )
        else:
            definition = default

        fields[field_name] = (
            python_type,
            definition
        )

    model_name = contract["name"].replace("-", "_")

    DynamicModel = create_model(
        model_name,
        __config__=ConfigDict(extra="forbid"),
        **fields
    )

    return DynamicModel


# ==========================================
# 6. CHECK UNIQUE FIELDS
# ==========================================

def check_unique(records, contract):

    errors = 0

    for rule in contract.get("invariants", []):

        match = re.fullmatch(
            r"\s*(\w+)\s+is unique\s*",
            rule
        )

        if match:

            field_name = match.group(1)

            values = [
                record.get(field_name)
                for record in records
                if record.get(field_name) is not None
            ]

            if len(values) != len(set(values)):

                print(
                    f"INVALID: Duplicate values in {field_name}"
                )

                errors += 1

            else:

                print(
                    f"UNIQUE CHECK: {field_name} PASSED"
                )

    return errors


# ==========================================
# 7. VALIDATE API RECORDS
# ==========================================

def validate_records(records, contract, model):

    valid_records = []
    invalid_count = 0

    print("\nNumber of records:", len(records))
    print("--------------------------------")

    for index, record in enumerate(records, start=1):

        try:

            validated_record = model(**record)

            valid_records.append(
                validated_record.model_dump()
            )

            print(f"Record {index}: VALID")

        except ValidationError as error:

            invalid_count += 1

            print(f"Record {index}: INVALID")
            print(error)

    # Check uniqueness across records
    unique_errors = check_unique(
        valid_records,
        contract
    )

    total_errors = invalid_count + unique_errors

    return total_errors


# ==========================================
# 8. VALIDATE ONE DOMAIN
# ==========================================

def validate_domain(domain):

    print("\n")
    print("=" * 50)
    print("DOMAIN:", domain.upper())
    print("=" * 50)

    # Load YAML
    contract = load_contract(
        CONTRACT_FILES[domain]
    )

    # Generate Pydantic model
    DynamicModel = build_model(contract)

    print("Dynamic Model:", DynamicModel.__name__)

    # Get API URL
    url = API_URLS[domain]

    try:

        response = requests.get(
            url,
            timeout=10
        )

        response.raise_for_status()

        data = response.json()

        # Accept a list of records or one record
        if isinstance(data, dict):
            data = [data]

        if not isinstance(data, list):
            print("INVALID API RESPONSE: Expected a list or object")
            return False

        print("\nData received from API!")
        print("--------------------------------")

        # Validate all records
        errors = validate_records(
            data,
            contract,
            DynamicModel
        )

        if errors == 0:

            print("\nRESULT: ALL RECORDS VALID")
            return True

        else:

            print("\nRESULT: VALIDATION FAILED")
            print("Total errors:", errors)
            return False

    except requests.RequestException as error:

        print("API CONNECTION ERROR:", error)
        return False

    except (ValueError, KeyError, TypeError) as error:

        print("CONTRACT OR DATA ERROR:", error)
        return False


# ==========================================
# 9. MAIN VALIDATION
# ==========================================

def main():

    results = {}

    for domain in CONTRACT_FILES:

        results[domain] = validate_domain(domain)

    print("\n")
    print("=" * 50)
    print("FINAL VALIDATION REPORT")
    print("=" * 50)

    for domain, result in results.items():

        status = "VALID" if result else "INVALID"

        print(domain.upper(), ":", status)

    successful = sum(results.values())

    print("--------------------------------")
    print(
        f"{successful}/{len(results)} domains validated successfully"
    )


if __name__ == "__main__":
    main()
