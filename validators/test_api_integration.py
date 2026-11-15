

import re
import pytest
import requests

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pydantic import ValidationError

# Support both execution from project root and validators folder
try:
    from validators.validate import load_contract, build_model
except ModuleNotFoundError:
    from validate import load_contract, build_model


# ==========================================
# 1. API CONFIGURATION
# ==========================================

APIS = [
    (
        "Merchandising",
        "http://localhost:8001/api/products/",
        "merchandising-products.yaml"
    ),
    (
        "Fulfillment",
        "http://localhost:8002/api/deliveries/",
        "fulfillment-orders.yaml"
    ),
    (
        "Customer Finance",
        "http://localhost:8003/api/payments/",
        "finance-invoices.yaml"
    )
]


# ==========================================
# 2. API RESPONSE HELPERS
# ==========================================

def get_api_response(api_url):

    try:
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        return response

    except requests.RequestException as error:
        pytest.fail(f"API connection failed: {error}")


def extract_records(data):

    if isinstance(data, list):
        return data

    if isinstance(data, dict):

        possible_keys = [
            "data", "results", "items",
            "products", "orders", "payments", "deliveries"
        ]

        for key in possible_keys:
            if key in data and isinstance(data[key], list):
                return data[key]

        return [data]

    raise ValueError("Invalid API response format")


def parse_datetime(value):

    if isinstance(value, datetime):
        result = value

    elif isinstance(value, str):
        try:
            result = datetime.fromisoformat(
                value.replace("Z", "+00:00")
            )
        except ValueError:
            return None

    else:
        return None

    # Assume UTC if the API returns a datetime without timezone
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)

    return result.astimezone(timezone.utc)


# ==========================================
# 3. TEST SCHEMA VALIDATION
# ==========================================

@pytest.mark.parametrize(
    "domain, api_url, contract_file",
    APIS
)
def test_api_data_matches_contract(domain, api_url, contract_file):

    print("\n" + "=" * 50)
    print(f"DOMAIN: {domain}")
    print("=" * 50)

    contract = load_contract(contract_file)
    model = build_model(contract)

    print(f"Contract loaded: {contract['name']}")

    response = get_api_response(api_url)

    try:
        records = extract_records(response.json())
    except (ValueError, requests.exceptions.JSONDecodeError) as error:
        pytest.fail(f"Invalid API response: {error}")

    assert len(records) > 0, f"{domain}: No records received"

    print(f"Number of records: {len(records)}")
    print("-" * 50)

    invalid_records = []

    for index, record in enumerate(records, start=1):

        try:
            model.model_validate(record)
            print(f"Record {index}: VALID")

        except ValidationError as error:
            invalid_records.append(index)
            print(f"Record {index}: INVALID")
            print(error)

    assert not invalid_records, (
        f"{domain}: Invalid records: {invalid_records}"
    )

    print(f"{domain}: ALL RECORDS ARE VALID")


# ==========================================
# 4. TEST UNIQUE IDs
# ==========================================

def get_unique_fields(contract):

    unique_fields = []

    for invariant in contract.get("invariants", []):

        match = re.search(
            r"^\s*(\w+)\s+is\s+unique\s*$",
            invariant,
            re.IGNORECASE
        )

        if match:
            unique_fields.append(match.group(1))

    return unique_fields


@pytest.mark.parametrize(
    "domain, api_url, contract_file",
    APIS
)
def test_unique_records(domain, api_url, contract_file):

    print("\n" + "=" * 50)
    print(f"UNIQUENESS TEST: {domain}")
    print("=" * 50)

    contract = load_contract(contract_file)
    response = get_api_response(api_url)

    records = extract_records(response.json())

    unique_fields = get_unique_fields(contract)

    assert unique_fields, (
        f"No uniqueness invariant found in {contract_file}"
    )

    for field in unique_fields:

        values = [
            record.get(field)
            for record in records
            if record.get(field) is not None
        ]

        duplicates = set(
            value for value in values
            if values.count(value) > 1
        )

        if duplicates:
            pytest.fail(
                f"{domain}: Duplicate values in {field}: "
                f"{duplicates}"
            )

        print(f"UNIQUE CHECK: {field} PASSED")

    print(f"{domain}: ALL UNIQUE CHECKS PASSED")


# ==========================================
# 5. GET DATA FRESHNESS TIMESTAMP
# ==========================================

TIMESTAMP_FIELDS = [
    "last_updated",
    "updated_at",
    "data_updated_at",
    "generated_at",
    "modified_at"
]


def get_freshness_timestamp(response, payload, records):

    # Option 1: Last-Modified HTTP header
    last_modified = response.headers.get("Last-Modified")

    if last_modified:
        try:
            return parsedate_to_datetime(
                last_modified
            ).astimezone(timezone.utc)
        except (TypeError, ValueError):
            pass

    # Option 2: Timestamp in API response metadata
    if isinstance(payload, dict):

        for field in TIMESTAMP_FIELDS:
            if field in payload:
                timestamp = parse_datetime(payload[field])

                if timestamp:
                    return timestamp

        metadata = payload.get("metadata")

        if isinstance(metadata, dict):
            for field in TIMESTAMP_FIELDS:
                if field in metadata:
                    timestamp = parse_datetime(metadata[field])

                    if timestamp:
                        return timestamp

    # Option 3: Timestamp in individual records
    timestamps = []

    for record in records:

        if not isinstance(record, dict):
            continue

        for field in TIMESTAMP_FIELDS:

            if field in record:
                timestamp = parse_datetime(record[field])

                if timestamp:
                    timestamps.append(timestamp)

    if timestamps:
        return max(timestamps)

    return None


# ==========================================
# 6. TEST SLA FRESHNESS
# ==========================================

@pytest.mark.parametrize(
    "domain, api_url, contract_file",
    APIS
)
def test_sla_freshness(domain, api_url, contract_file):

    print("\n" + "=" * 50)
    print(f"SLA FRESHNESS TEST: {domain}")
    print("=" * 50)

    contract = load_contract(contract_file)

    max_minutes = contract["sla"]["freshness_max_minutes"]

    response = get_api_response(api_url)
    payload = response.json()
    records = extract_records(payload)

    timestamp = get_freshness_timestamp(
        response,
        payload,
        records
    )

    if timestamp is None:
        pytest.skip(
            f"{domain}: No data freshness timestamp available. "
            "API must provide updated_at or Last-Modified."
        )

    now = datetime.now(timezone.utc)

    age_minutes = (
        now - timestamp
    ).total_seconds() / 60

    print(f"Maximum freshness: {max_minutes} minutes")
    print(f"Actual data age: {age_minutes:.2f} minutes")

    assert age_minutes <= max_minutes, (
        f"{domain}: SLA VIOLATED! "
        f"Data age is {age_minutes:.2f} minutes, "
        f"maximum allowed is {max_minutes} minutes."
    )

    assert age_minutes >= 0, (
        f"{domain}: Timestamp is in the future."
    )

    print(f"{domain}: SLA FRESHNESS PASSED")
