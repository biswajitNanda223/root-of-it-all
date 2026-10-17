from fastapi.testclient import TestClient

from billing_service.infrastructure.models import Base
from rio_auth import JwtTokens

from .conftest import SECRET

I = "/api/v1/invoices"  # noqa: E741
BODY = {"order_id": 1, "customer_id": "42", "amount": "25.00"}


def _hdr(sub: str, admin: bool = False) -> dict[str, str]:
    return {"Authorization": f"Bearer {JwtTokens(SECRET).issue(sub, {'adm': admin})}"}


def test_own_metadata_only_has_billing_tables() -> None:
    assert set(Base.metadata.tables) == {"invoices"}


def test_probes_and_auth_required(client: TestClient) -> None:
    assert client.get("/health/ready").json() == {"status": "ok"}
    assert client.get(I).status_code == 401


def test_only_admins_issue_and_one_invoice_per_order(client: TestClient) -> None:
    assert client.post(I, json=BODY, headers=_hdr("42")).status_code == 403
    assert client.post(I, json=BODY, headers=_hdr("1", admin=True)).status_code == 201
    assert client.post(I, json=BODY, headers=_hdr("1", admin=True)).status_code == 409
    bad = client.post(I, json={**BODY, "order_id": 2, "amount": "0"}, headers=_hdr("1", admin=True))
    assert bad.status_code == 422


def test_customer_isolation_and_state_machine(client: TestClient) -> None:
    admin, owner, other = _hdr("1", admin=True), _hdr("42"), _hdr("43")
    inv = client.post(I, json=BODY, headers=admin).json()
    assert client.get(f"{I}/{inv['id']}", headers=other).status_code == 403
    assert client.get(I, headers=other).json()["total"] == 0
    assert client.get(I, headers=owner).json()["total"] == 1
    assert client.get(I, headers=admin).json()["total"] == 1
    assert client.post(f"{I}/{inv['id']}/void", headers=owner).status_code == 403
    assert client.post(f"{I}/{inv['id']}/pay", headers=owner).json()["status"] == "paid"
    assert client.post(f"{I}/{inv['id']}/pay", headers=owner).status_code == 409
    assert client.post(f"{I}/{inv['id']}/void", headers=admin).status_code == 409
    assert client.get(f"{I}/999", headers=admin).status_code == 404
