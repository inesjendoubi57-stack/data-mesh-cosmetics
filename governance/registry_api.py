import json
import re
import sys
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, ValidationError

from check import compare_contracts


ROOT_DIR = Path(__file__).resolve().parent.parent
REGISTRY_PATH = ROOT_DIR / "governance" / "registry.json"
PROPOSALS_DIR = ROOT_DIR / "governance" / "proposals"

sys.path.insert(0, str(ROOT_DIR / "validators"))
from validate import build_model  # noqa: E402

app = FastAPI(
    title="Governance Registry",
    description="Registered data contracts, payload validation and compatibility checks",
    version="1.0.0",
)


def load_registry():
    with open(REGISTRY_PATH, "r", encoding="utf-8") as file:
        return json.load(file)["contracts"]


def load_yaml(path):
    with open(path, "r", encoding="utf-8") as file:
        return yaml.safe_load(file)


def find_entry(name):
    for entry in load_registry():
        if entry["name"] == name:
            return entry
    raise HTTPException(status_code=404, detail="Contract not registered")


def load_version(entry, version=None):
    version = version or entry["current_version"]

    for version_info in entry["versions"]:
        if version_info["version"] == version:
            return load_yaml(ROOT_DIR / version_info["file_path"])

    raise HTTPException(status_code=404, detail="Version not registered")


@app.get("/")
def home():
    return {"message": "Governance Registry is running"}


@app.get("/contracts")
def list_contracts():
    return load_registry()


@app.get("/contracts/{name}")
def get_contract(name: str, version: str | None = None):
    return load_version(find_entry(name), version)


class Payload(BaseModel):
    contract_name: str
    records: list[dict]


@app.post("/validate")
def validate_payload(payload: Payload):

    contract = load_version(find_entry(payload.contract_name))
    model = build_model(contract)
    errors = []

    for index, record in enumerate(payload.records, start=1):
        try:
            model(**record)
        except ValidationError as error:
            for detail in error.errors():
                field = ".".join(str(part) for part in detail["loc"])
                errors.append(f"Record {index}, {field}: {detail['msg']}")

    for rule in contract.get("invariants", []):
        match = re.fullmatch(r"\s*(\w+)\s+is unique\s*", rule)
        if match:
            field = match.group(1)
            values = [record.get(field) for record in payload.records]
            if len(values) != len(set(values)):
                errors.append(f"Duplicate values in {field}")

    return {
        "contract_name": payload.contract_name,
        "version": contract["version"],
        "records": len(payload.records),
        "valid": not errors,
        "errors": errors,
    }


@app.get("/proposals/{name}")
def list_proposals(name: str):
    find_entry(name)
    return sorted(path.name for path in PROPOSALS_DIR.glob(f"{name}-*.yaml"))


@app.get("/compatibility/{name}")
def check_compatibility(name: str, proposal: str):
    old_contract = load_version(find_entry(name))
    proposal_path = PROPOSALS_DIR / proposal

    if proposal_path.parent != PROPOSALS_DIR or not proposal_path.is_file():
        raise HTTPException(status_code=404, detail="Proposal not found")

    new_contract = load_yaml(proposal_path)
    status, changes = compare_contracts(old_contract, new_contract)

    return {
        "contract_name": name,
        "old_version": old_contract["version"],
        "new_version": new_contract["version"],
        "status": status,
        "accepted": status != "INCOMPATIBLE",
        "changes": changes,
    }
