
import pytest
from pydantic import ValidationError

from validate import load_contract, build_model


# ==========================================
# 1. LOAD THE THREE CONTRACTS AND MODELS
# ==========================================

@pytest.fixture(scope="module")
def models():

    products_contract = load_contract("merchandising-products.yaml")
    orders_contract = load_contract("fulfillment-orders.yaml")
    invoices_contract = load_contract("finance-invoices.yaml")

    return {
        "products": build_model(products_contract),
        "orders": build_model(orders_contract),
        "invoices": build_model(invoices_contract)
    }


# ==========================================
# 2. TEST DATA
# ==========================================

PRODUCT = {
    "product_id": "P001",
    "name": "Lipstick",
    "brand": "Maybelline",
    "category": "Makeup",
    "price": 25.5,
    "volume_ml": 10,
    "stock_qty": 50,
    "updated_at": "2026-11-15T13:00:00Z"
}

ORDER = {
    "order_id": "O001",
    "product_id": "P001",
    "quantity": 2,
    "status": "Shipped",
    "carrier": "DHL",
    "shipped_at": "2026-11-11T10:00:00",
    "updated_at": "2026-11-15T13:00:00Z"
}

INVOICE = {
    "invoice_id": "I001",
    "order_id": "O001",
    "amount": 51.0,
    "currency": "TND",
    "payment_method": "Card",
    "payment_status": "Paid",
    "updated_at": "2026-11-15T13:00:00Z"
}


# ==========================================
# 3. VALID DATA TESTS (3)
# ==========================================

@pytest.mark.parametrize("domain,data", [
    ("products", PRODUCT),
    ("orders", ORDER),
    ("invoices", INVOICE)
])
def test_valid_data(models, domain, data):

    model = models[domain]

    result = model.model_validate(data)

    assert result is not None


# ==========================================
# 4. OPTIONAL FIELDS CAN BE MISSING (3)
# ==========================================

@pytest.mark.parametrize("domain,data,field", [
    ("products", PRODUCT, "volume_ml"),
    ("orders", ORDER, "carrier"),
    ("orders", ORDER, "shipped_at")
])
def test_optional_field_may_be_missing(models, domain, data, field):

    test_data = data.copy()
    test_data.pop(field)

    result = models[domain].model_validate(test_data)

    assert getattr(result, field) is None


# ==========================================
# 5. REQUIRED FIELDS MUST EXIST (3)
# ==========================================

@pytest.mark.parametrize("domain,data,field", [
    ("products", PRODUCT, "name"),
    ("orders", ORDER, "order_id"),
    ("invoices", INVOICE, "amount")
])
def test_missing_required_field(models, domain, data, field):

    test_data = data.copy()
    test_data.pop(field)

    with pytest.raises(ValidationError):
        models[domain].model_validate(test_data)


# ==========================================
# 6. WRONG DATA TYPES (3)
# ==========================================

@pytest.mark.parametrize("domain,data,field,value", [
    ("products", PRODUCT, "price", "not-a-number"),
    ("orders", ORDER, "quantity", "many"),
    ("invoices", INVOICE, "amount", "invalid")
])
def test_wrong_type(models, domain, data, field, value):

    test_data = data.copy()
    test_data[field] = value

    with pytest.raises(ValidationError):
        models[domain].model_validate(test_data)


# ==========================================
# 7. BUSINESS INVARIANTS (4)
# ==========================================

@pytest.mark.parametrize("domain,data,field,value", [
    ("products", PRODUCT, "price", 0),
    ("products", PRODUCT, "stock_qty", -1),
    ("orders", ORDER, "quantity", 0),
    ("invoices", INVOICE, "amount", -10)
])
def test_business_invariants(models, domain, data, field, value):

    test_data = data.copy()
    test_data[field] = value

    with pytest.raises(ValidationError):
        models[domain].model_validate(test_data)


# ==========================================
# 8. EXTRA FIELDS ARE NOT ALLOWED (3)
# ==========================================

@pytest.mark.parametrize("domain,data", [
    ("products", PRODUCT),
    ("orders", ORDER),
    ("invoices", INVOICE)
])
def test_extra_field_rejected(models, domain, data):

    test_data = data.copy()
    test_data["unexpected_field"] = "test"

    with pytest.raises(ValidationError):
        models[domain].model_validate(test_data)


# ==========================================
# 9. RENAMED FIELDS BREAK THE CONTRACT (3)
# ==========================================

@pytest.mark.parametrize("domain,data,old_name,new_name", [
    ("products", PRODUCT, "price", "unit_price"),
    ("orders", ORDER, "quantity", "qty"),
    ("invoices", INVOICE, "amount", "total")
])
def test_renamed_required_field(models, domain, data, old_name, new_name):

    test_data = data.copy()

    test_data[new_name] = test_data.pop(old_name)

    with pytest.raises(ValidationError):
        models[domain].model_validate(test_data)


# ==========================================
# 10. REQUIRED FIELDS CANNOT BE NULL (3)
# ==========================================

@pytest.mark.parametrize("domain,data,field", [
    ("products", PRODUCT, "name"),
    ("orders", ORDER, "status"),
    ("invoices", INVOICE, "currency")
])
def test_null_required_field(models, domain, data, field):

    test_data = data.copy()
    test_data[field] = None

    with pytest.raises(ValidationError):
        models[domain].model_validate(test_data)


# ==========================================
# 11. OPTIONAL FIELDS CAN BE NULL (3)
# ==========================================

@pytest.mark.parametrize("domain,data,field", [
    ("products", PRODUCT, "volume_ml"),
    ("orders", ORDER, "carrier"),
    ("orders", ORDER, "shipped_at")
])
def test_optional_field_can_be_null(models, domain, data, field):

    test_data = data.copy()
    test_data[field] = None

    result = models[domain].model_validate(test_data)

    assert getattr(result, field) is None


# ==========================================
# 12. INVALID NUMERIC TYPES (3)
# ==========================================

@pytest.mark.parametrize("domain,data,field", [
    ("products", PRODUCT, "stock_qty"),
    ("orders", ORDER, "quantity"),
    ("invoices", INVOICE, "amount")
])
def test_invalid_numeric_type(models, domain, data, field):

    test_data = data.copy()
    test_data[field] = "abc"

    with pytest.raises(ValidationError):
        models[domain].model_validate(test_data)


# ==========================================
# 13. INVALID DATETIME (1)
# ==========================================

def test_invalid_datetime(models):

    test_data = ORDER.copy()
    test_data["shipped_at"] = "not-a-date"

    with pytest.raises(ValidationError):
        models["orders"].model_validate(test_data)


# ==========================================
# 14. VALID BOUNDARY VALUES (2)
# ==========================================

def test_zero_stock_is_valid(models):

    test_data = PRODUCT.copy()
    test_data["stock_qty"] = 0

    result = models["products"].model_validate(test_data)

    assert result.stock_qty == 0


def test_small_positive_price_is_valid(models):

    test_data = PRODUCT.copy()
    test_data["price"] = 0.01

    result = models["products"].model_validate(test_data)

    assert result.price == 0.01
