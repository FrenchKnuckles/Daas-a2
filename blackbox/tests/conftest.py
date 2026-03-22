from typing import Any, Dict, Iterable, Optional

import pytest
import requests


def _extract_list_payload(data: Any) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "items", "users", "products", "result"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def _extract_int_id(record: Dict[str, Any], candidates: Iterable[str]) -> Optional[int]:
    for key in candidates:
        value = record.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


@pytest.fixture(scope="session")
def base_url() -> str:
    return "http://localhost:8080"


@pytest.fixture(scope="session")
def roll_number() -> str:
    return "2024114005"


@pytest.fixture(scope="session")
def admin_headers(roll_number: str) -> Dict[str, str]:
    return {"X-Roll-Number": roll_number}


@pytest.fixture(scope="session")
def session() -> requests.Session:
    return requests.Session()


@pytest.fixture(scope="session")
def ensure_server_up(base_url: str, session: requests.Session, admin_headers: Dict[str, str]) -> None:
    try:
        response = session.get(f"{base_url}/api/v1/admin/users", headers=admin_headers, timeout=8)
    except requests.RequestException as exc:
        pytest.skip(f"QuickCart server not reachable at {base_url}: {exc}")
    if response.status_code >= 500:
        pytest.skip(f"QuickCart server unhealthy at {base_url} (status={response.status_code})")


@pytest.fixture(scope="session")
def users_payload(
    ensure_server_up: None,
    base_url: str,
    session: requests.Session,
    admin_headers: Dict[str, str],
) -> list:
    response = session.get(f"{base_url}/api/v1/admin/users", headers=admin_headers, timeout=8)
    assert response.status_code == 200, response.text
    return _extract_list_payload(response.json())


@pytest.fixture(scope="session")
def products_payload(
    ensure_server_up: None,
    base_url: str,
    session: requests.Session,
    admin_headers: Dict[str, str],
) -> list:
    response = session.get(f"{base_url}/api/v1/admin/products", headers=admin_headers, timeout=8)
    assert response.status_code == 200, response.text
    return _extract_list_payload(response.json())


@pytest.fixture(scope="session")
def existing_user_id(users_payload: list) -> int:
    for user in users_payload:
        user_id = _extract_int_id(user, ("user_id", "id"))
        if user_id is not None and user_id > 0:
            return user_id
    pytest.skip("No usable user found from /api/v1/admin/users")


@pytest.fixture(scope="session")
def user_headers(roll_number: str, existing_user_id: int) -> Dict[str, str]:
    return {
        "X-Roll-Number": roll_number,
        "X-User-ID": str(existing_user_id),
        "Content-Type": "application/json",
    }


@pytest.fixture(scope="session")
def existing_product_id(products_payload: list) -> int:
    active_candidates = []
    fallback_candidates = []
    for product in products_payload:
        product_id = _extract_int_id(product, ("product_id", "id"))
        if product_id is None:
            continue
        fallback_candidates.append(product_id)
        is_active = product.get("is_active")
        if is_active is None:
            is_active = product.get("active")
        if is_active is True:
            active_candidates.append(product_id)

    if active_candidates:
        return active_candidates[0]
    if fallback_candidates:
        return fallback_candidates[0]

    pytest.skip("No usable product found from /api/v1/admin/products")


def extract_list_payload(data: Any) -> list:
    return _extract_list_payload(data)


def extract_int_id(record: Dict[str, Any], candidates: Iterable[str]) -> Optional[int]:
    return _extract_int_id(record, candidates)
