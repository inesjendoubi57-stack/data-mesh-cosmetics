import json
import os
import re
from datetime import datetime, timezone

import requests
import yaml
from django.conf import settings
from pydantic import ValidationError

from validate import build_model


def load_registry():
    with open(settings.REGISTRY_PATH, "r", encoding="utf-8") as file:
        registry = json.load(file)

    products = []

    for entry in registry["contracts"]:
        active = next(v for v in entry["versions"] if v["status"] == "active")

        with open(settings.ROOT_DIR / active["file_path"], "r", encoding="utf-8") as file:
            contract = yaml.safe_load(file)

        products.append({**entry, "contract": contract})

    return products


def find_product(name):
    for product in load_registry():
        if product["name"] == name:
            return product
    return None


def load_proposals(name):
    proposals = []

    for path in sorted(settings.PROPOSALS_DIR.glob(f"{name}-*.yaml")):
        with open(path, "r", encoding="utf-8") as file:
            proposals.append({"file": path.name, "contract": yaml.safe_load(file)})

    return proposals


def endpoint_url(product):
    # Docker : MERCHANDISING_HOST, FULFILLMENT_HOST, FINANCE_HOST
    host = os.environ.get(f"{product['domain'].upper()}_HOST")
    if host:
        return product["endpoint"].replace("localhost", host)
    return product["endpoint"]


def fetch_records(product):
    response = requests.get(endpoint_url(product), timeout=5)
    response.raise_for_status()
    return response.json()


def unique_fields(contract):
    fields = []
    for rule in contract.get("invariants", []):
        match = re.fullmatch(r"\s*(\w+)\s+is unique\s*", rule)
        if match:
            fields.append(match.group(1))
    return fields


def check_status(product):
    contract = product["contract"]
    status = {
        "reachable": False,
        "valid": False,
        "errors": [],
        "age_minutes": None,
        "sla_respected": False,
        "records": [],
    }

    try:
        records = fetch_records(product)
    except (requests.RequestException, ValueError):
        return status

    status["reachable"] = True
    status["records"] = records

    model = build_model(contract)

    for index, record in enumerate(records, start=1):
        try:
            model(**record)
        except ValidationError as error:
            for detail in error.errors():
                field = ".".join(str(part) for part in detail["loc"])
                status["errors"].append(f"Ligne {index}, {field} : {detail['msg']}")

    for field in unique_fields(contract):
        values = [record.get(field) for record in records]
        if len(values) != len(set(values)):
            status["errors"].append(f"Valeurs en double dans {field}")

    status["valid"] = not status["errors"]

    timestamps = [
        datetime.fromisoformat(record["updated_at"].replace("Z", "+00:00"))
        for record in records
        if record.get("updated_at")
    ]

    if timestamps:
        age = (datetime.now(timezone.utc) - max(timestamps)).total_seconds() / 60
        status["age_minutes"] = round(age, 1)
        status["sla_respected"] = age <= contract["sla"]["freshness_max_minutes"]

    return status
