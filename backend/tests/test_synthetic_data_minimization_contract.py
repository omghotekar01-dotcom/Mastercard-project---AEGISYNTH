from app.schemas import Transaction
from app.simulator import PaymentWorld


_FORBIDDEN_CREDENTIAL_FIELDS = {
    "pan",
    "card_number",
    "cvv",
    "cvc",
    "expiry",
    "expiry_date",
    "account_number",
    "iban",
    "routing_number",
    "payment_token",
    "auth_token",
    "credential",
    "password",
    "pin",
}


def test_synthetic_transaction_contract_excludes_payment_credentials():
    """Benchmark evidence must remain synthetic feature data, never payment credentials."""
    schema_fields = set(Transaction.model_fields)
    assert schema_fields.isdisjoint(_FORBIDDEN_CREDENTIAL_FIELDS)

    world = PaymentWorld(seed=42)
    rows = world.benign(3) + world.attack(3, "ghost_merchant_swarm", hardness=0.2)

    for row in rows:
        payload_fields = set(row.model_dump())
        assert payload_fields == schema_fields
        assert payload_fields.isdisjoint(_FORBIDDEN_CREDENTIAL_FIELDS)
