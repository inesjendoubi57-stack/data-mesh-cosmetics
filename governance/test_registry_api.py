
from fastapi.testclient import TestClient

from registry_api import app

client = TestClient(app)

VALID_PRODUCT = {
    "product_id": "1",
    "name": "Lipstick",
    "brand": "Maybelline",
    "category": "Makeup",
    "price": 25.5,
    "volume_ml": None,
    "stock_qty": 50,
    "updated_at": "2026-11-17T10:00:00Z",
}


def validate(records):
    response = client.post(
        "/validate",
        json={"contract_name": "merchandising-products", "records": records},
    )
    assert response.status_code == 200
    return response.json()


def test_registered_contracts_are_listed():
    names = {contract["name"] for contract in client.get("/contracts").json()}
    assert names == {"merchandising-products", "fulfillment-orders", "finance-invoices"}


def test_contract_can_be_read():
    contract = client.get("/contracts/finance-invoices").json()
    assert contract["version"] == "1.0.0"


def test_unknown_contract_returns_404():
    assert client.get("/contracts/unknown").status_code == 404


def test_valid_payload_is_accepted():
    assert validate([VALID_PRODUCT])["valid"] is True


def test_negative_price_is_rejected():
    result = validate([{**VALID_PRODUCT, "price": -5}])
    assert result["valid"] is False
    assert "price" in result["errors"][0]


def test_renamed_field_is_rejected():
    record = dict(VALID_PRODUCT)
    record["unit_price"] = record.pop("price")
    assert validate([record])["valid"] is False


def test_duplicate_ids_are_rejected():
    result = validate([VALID_PRODUCT, VALID_PRODUCT])
    assert "Duplicate values in product_id" in result["errors"]


def test_rename_proposal_is_incompatible():
    result = client.get(
        "/compatibility/merchandising-products",
        params={"proposal": "merchandising-products-rename-price.yaml"},
    ).json()
    assert result["status"] == "INCOMPATIBLE"
    assert result["accepted"] is False


def test_optional_field_proposal_is_accepted():
    result = client.get(
        "/compatibility/merchandising-products",
        params={"proposal": "merchandising-products-add-image-url.yaml"},
    ).json()
    assert result["status"] == "REVIEW_REQUIRED"
    assert result["accepted"] is True


def test_unknown_proposal_returns_404():
    response = client.get(
        "/compatibility/merchandising-products",
        params={"proposal": "../registry.json"},
    )
    assert response.status_code == 404
