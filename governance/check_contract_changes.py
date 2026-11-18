import os
import subprocess
import sys
from pathlib import Path

import yaml

from check import compare_contracts

# Compares each contract with the same file on the base branch.

ROOT_DIR = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = ROOT_DIR / "contracts"

DEFAULT_BASE_REF = "origin/main"


def load_base_contract(base_ref, relative_path):

    result = subprocess.run(
        ["git", "show", f"{base_ref}:{relative_path}"],
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        return None

    return yaml.safe_load(result.stdout)


def check_contract_file(path, base_ref):

    relative_path = path.relative_to(ROOT_DIR).as_posix()

    with open(path, "r", encoding="utf-8") as file:
        new_contract = yaml.safe_load(file)

    old_contract = load_base_contract(base_ref, relative_path)

    print(f"\nContract: {relative_path}")

    if old_contract is None:
        print("Result: NEW CONTRACT (nothing to compare)")
        return "COMPATIBLE"

    status, changes = compare_contracts(old_contract, new_contract)

    print(f"Result: {status}")

    for change in changes:
        print(f"  - {change}")

    if not changes:
        print("  - No change.")

    return status


def main():

    base_ref = os.environ.get("BASE_REF") or DEFAULT_BASE_REF

    print("=" * 65)
    print("              CONTRACT CHANGE GATE")
    print("=" * 65)
    print(f"Base branch: {base_ref}")

    exists = subprocess.run(
        ["git", "rev-parse", "--verify", "--quiet", base_ref],
        cwd=ROOT_DIR,
        capture_output=True,
    )

    if exists.returncode != 0:
        print(f"ERROR: base branch {base_ref} not found. Run: git fetch origin")
        return 1

    statuses = [
        check_contract_file(path, base_ref)
        for path in sorted(CONTRACTS_DIR.glob("*.yaml"))
    ]

    print("\n" + "=" * 65)

    if "INCOMPATIBLE" in statuses:
        print("FAILED: breaking change detected. Merge blocked.")
        print("=" * 65)
        return 1

    if "REVIEW_REQUIRED" in statuses:
        print("PASSED WITH WARNING: a reviewer must check these changes.")
    else:
        print("PASSED: all contracts are backward compatible.")

    print("=" * 65)

    return 0


if __name__ == "__main__":
    sys.exit(main())
