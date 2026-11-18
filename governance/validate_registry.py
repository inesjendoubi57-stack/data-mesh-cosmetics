
import json
import re
import sys
from pathlib import Path
import yaml

# ============================================================
#              GOVERNANCE REGISTRY VALIDATOR
# ============================================================

# Repository root
ROOT_DIR = Path(__file__).resolve().parent.parent

# Registry file
REGISTRY_PATH = ROOT_DIR / "governance" / "registry.json"


def validate_registry():

    errors = []

    print("=" * 65)
    print("             GOVERNANCE REGISTRY VALIDATOR")
    print("=" * 65)

    # 1. Check registry file
    if not REGISTRY_PATH.exists():
        print("ERROR: registry.json not found.")
        return False

    # 2. Load JSON
    try:
        with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
            registry = json.load(file)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON: {e}")
        return False

    # 3. Check root structure
    if not isinstance(registry, dict):
        print("ERROR: Registry must be a JSON object.")
        return False

    required_root_fields = ["registry_version", "path_convention", "contracts"]

    for field in required_root_fields:
        if field not in registry:
            errors.append(f"Missing root field: {field}")

    if errors:
        return print_errors(errors)

    if registry["path_convention"] != "repository_root":
        errors.append("Unsupported path convention.")

    # 4. Validate contracts
    contracts = registry["contracts"]

    if not isinstance(contracts, list):
        errors.append("'contracts' must be a list.")
        return print_errors(errors)

    contract_names = set()

    for contract in contracts:

        if not isinstance(contract, dict):
            errors.append("Each contract must be a JSON object.")
            continue

        required_fields = [
            "name",
            "domain",
            "owner",
            "description",
            "current_version",
            "compatibility",
            "versions"
        ]

        for field in required_fields:
            if field not in contract:
                errors.append(
                    f"Contract is missing required field: {field}"
                )

        if any(field not in contract for field in required_fields):
            continue

        name = contract["name"]

        # 5. Check duplicate names
        if not isinstance(name, str) or not name.strip():
            errors.append("Contract name must be a non-empty string.")
            continue

        if name in contract_names:
            errors.append(f"Duplicate contract name: {name}")
        contract_names.add(name)

        # 6. Check Semantic Versioning
        current_version = contract["current_version"]

        if not isinstance(current_version, str) or not re.fullmatch(
            r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)",
            current_version
        ):
            errors.append(
                f"Invalid current_version for contract {name}: "
                f"{current_version}"
            )

        # 7. Check versions list
        versions = contract["versions"]

        if not isinstance(versions, list) or not versions:
            errors.append(f"Contract {name} must have a non-empty versions list.")
            continue

        version_names = set()
        active_versions = []

        for version_info in versions:

            if not isinstance(version_info, dict):
                errors.append(f"Invalid version entry in contract {name}.")
                continue

            for field in ["version", "file_path", "status"]:
                if field not in version_info:
                    errors.append(
                        f"Missing {field} in version entry of {name}."
                    )

            if any(field not in version_info for field in [
                "version", "file_path", "status"
            ]):
                continue

            version = version_info["version"]
            file_path = version_info["file_path"]
            status = version_info["status"]

            if not isinstance(version, str) or not re.fullmatch(
                r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)",
                version
            ):
                errors.append(f"Invalid version in {name}: {version}")
                continue

            if version in version_names:
                errors.append(f"Duplicate version {version} in {name}.")
            version_names.add(version)

            if status not in ["active", "deprecated", "retired"]:
                errors.append(f"Invalid status in {name}: {status}")

            if status == "active":
                active_versions.append(version)

            # Check contract file path
            if not isinstance(file_path, str) or not file_path.strip():
                errors.append(f"Invalid file_path in {name}.")
                continue

            resolved_path = (ROOT_DIR / file_path).resolve()

            if not resolved_path.is_relative_to(ROOT_DIR.resolve()):
                errors.append(f"Path escapes repository root in {name}: {file_path}")
            elif not resolved_path.is_file():
                errors.append(f"Contract file not found: {file_path}")

            else:
                # Cross-check Registry metadata with YAML contract
                try:
                    with open(resolved_path, "r", encoding="utf-8") as yaml_file:
                        yaml_contract = yaml.safe_load(yaml_file)

                    if not isinstance(yaml_contract, dict):
                        errors.append(
                            f"Invalid YAML structure in {file_path}."
                        )
                        continue

                    comparisons = {
                        "name": name,
                        "version": version,
                        "owner": contract["owner"],
                        "description": contract["description"],
                        "compatibility": contract["compatibility"]
                    }

                    for field, registry_value in comparisons.items():
                        yaml_value = yaml_contract.get(field)

                        if yaml_value != registry_value:
                            errors.append(
                                f"Mismatch in {name}: "
                                f"{field} differs between Registry "
                                f"and YAML ({registry_value} != {yaml_value})."
                            )

                except yaml.YAMLError as e:
                    errors.append(
                        f"Invalid YAML file {file_path}: {e}"
                    )
                except OSError as e:
                    errors.append(
                        f"Cannot read contract file {file_path}: {e}"
                    )


        # 8. Check current version
        if current_version not in version_names:
            errors.append(
                f"Current version {current_version} not found in versions of {name}."
            )

        if active_versions != [current_version]:
            errors.append(
                f"Contract {name} must have exactly one active version "
                f"matching current_version."
            )

    if errors:
        return print_errors(errors)

    print("\nSUCCESS: Registry validation passed!")
    print(f"Contracts validated: {len(contracts)}")
    print("=" * 65)

    return True


def print_errors(errors):

    print("\nREGISTRY VALIDATION FAILED")

    for error in errors:
        print(f"- {error}")

    print(f"\nTotal errors: {len(errors)}")
    print("=" * 65)

    return False


if __name__ == "__main__":
    sys.exit(0 if validate_registry() else 1)
