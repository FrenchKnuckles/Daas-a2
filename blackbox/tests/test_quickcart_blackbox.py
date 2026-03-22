import math
from typing import Any, Dict

import pytest

pytestmark = pytest.mark.usefixtures("ensure_server_up")


def _request(session, method: str, base_url: str, path: str, headers: Dict[str, str], json: Dict[str, Any] | None = None):
    return session.request(method, f"{base_url}{path}", headers=headers, json=json, timeout=8)


def _pick_key(record: Dict[str, Any], *keys: str):
    for key in keys:
        if key in record:
            return record[key]
    return None


def extract_list_payload(data: Any) -> list:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "items", "users", "products", "result"):
            value = data.get(key)
            if isinstance(value, list):
                return value
    return []


def extract_int_id(record: Dict[str, Any], candidates: tuple):
    for key in candidates:
        value = record.get(key)
        if isinstance(value, int):
            return value
        if isinstance(value, str) and value.isdigit():
            return int(value)
    return None


# ADMIN ENDPOINTS

class TestAdmin:
    def test_users_list(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/users", admin_headers)
        assert resp.status_code == 200
        users = extract_list_payload(resp.json())
        assert isinstance(users, list)

    def test_single_user_lookup(self, session, base_url, admin_headers, existing_user_id):
        resp = _request(session, "GET", base_url, f"/api/v1/admin/users/{existing_user_id}", admin_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    def test_nonexistent_user_returns_404(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/users/999999999", admin_headers)
        assert resp.status_code == 404

    def test_carts_list(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/carts", admin_headers)
        assert resp.status_code == 200

    def test_orders_list(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/orders", admin_headers)
        assert resp.status_code == 200

    def test_products_list(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/products", admin_headers)
        assert resp.status_code == 200

    def test_coupons_list(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/coupons", admin_headers)
        assert resp.status_code == 200

    def test_tickets_list(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/tickets", admin_headers)
        assert resp.status_code == 200

    def test_addresses_list(self, session, base_url, admin_headers):
        resp = _request(session, "GET", base_url, "/api/v1/admin/addresses", admin_headers)
        assert resp.status_code == 200


# PROFILE

class TestProfile:
    def test_get_profile_has_user_fields(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/profile", user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert any(k in data for k in ("user_id", "id", "name", "email", "phone"))

    def test_put_name_min_length(self, session, base_url, user_headers):
        resp = _request(
            session, "PUT", base_url, "/api/v1/profile", user_headers,
            json={"name": "AB", "phone": "9876543210"},
        )
        assert resp.status_code == 200

    def test_put_name_max_length(self, session, base_url, user_headers):
        resp = _request(
            session, "PUT", base_url, "/api/v1/profile", user_headers,
            json={"name": "A" * 50, "phone": "9876543210"},
        )
        assert resp.status_code == 200

    def test_put_name_too_long(self, session, base_url, user_headers):
        resp = _request(
            session, "PUT", base_url, "/api/v1/profile", user_headers,
            json={"name": "A" * 51, "phone": "9876543210"},
        )
        assert resp.status_code == 400

    def test_put_phone_too_long(self, session, base_url, user_headers):
        resp = _request(
            session, "PUT", base_url, "/api/v1/profile", user_headers,
            json={"name": "Valid Name", "phone": "12345678901"},
        )
        assert resp.status_code == 400

    def test_put_phone_non_numeric(self, session, base_url, user_headers):
        resp = _request(
            session, "PUT", base_url, "/api/v1/profile", user_headers,
            json={"name": "Valid Name", "phone": "abcdefghij"},
        )
        assert resp.status_code == 400

    def test_put_missing_name(self, session, base_url, user_headers):
        resp = _request(
            session, "PUT", base_url, "/api/v1/profile", user_headers,
            json={"phone": "9876543210"},
        )
        assert resp.status_code == 400

    def test_put_missing_phone(self, session, base_url, user_headers):
        resp = _request(
            session, "PUT", base_url, "/api/v1/profile", user_headers,
            json={"name": "Valid Name"},
        )
        assert resp.status_code == 400


# ADDRESSES

class TestAddresses:
    def test_get_addresses(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/addresses", user_headers)
        assert resp.status_code == 200
        assert isinstance(extract_list_payload(resp.json()), list)

    def test_create_office_label(self, session, base_url, user_headers):
        payload = {
            "label": "OFFICE",
            "street": "456 Office Park",
            "city": "Mumbai",
            "pincode": "400001",
            "is_default": False,
        }
        resp = _request(session, "POST", base_url, "/api/v1/addresses", user_headers, json=payload)
        assert resp.status_code in (200, 201)

    def test_create_city_too_short(self, session, base_url, user_headers):
        payload = {
            "label": "HOME",
            "street": "Valid Street",
            "city": "A",
            "pincode": "500001",
            "is_default": False,
        }
        resp = _request(session, "POST", base_url, "/api/v1/addresses", user_headers, json=payload)
        assert resp.status_code == 400

    def test_create_pincode_too_short(self, session, base_url, user_headers):
        payload = {
            "label": "HOME",
            "street": "Valid Street",
            "city": "Hyd",
            "pincode": "5000",
            "is_default": False,
        }
        resp = _request(session, "POST", base_url, "/api/v1/addresses", user_headers, json=payload)
        assert resp.status_code == 400

    def test_create_pincode_too_long(self, session, base_url, user_headers):
        payload = {
            "label": "HOME",
            "street": "Valid Street",
            "city": "Hyd",
            "pincode": "5000011",
            "is_default": False,
        }
        resp = _request(session, "POST", base_url, "/api/v1/addresses", user_headers, json=payload)
        assert resp.status_code == 400

    def test_create_returns_address_id(self, session, base_url, user_headers):
        payload = {
            "label": "OTHER",
            "street": "99 Test Avenue",
            "city": "Pune",
            "pincode": "411001",
            "is_default": False,
        }
        resp = _request(session, "POST", base_url, "/api/v1/addresses", user_headers, json=payload)
        assert resp.status_code in (200, 201)
        data = resp.json()
        address_obj = _pick_key(data, "address", "data", "result") or data
        assert extract_int_id(address_obj, ("address_id", "id")) is not None

    def test_only_one_default_at_a_time(self, session, base_url, user_headers):
        for i in range(2):
            _request(
                session, "POST", base_url, "/api/v1/addresses", user_headers,
                json={
                    "label": "HOME",
                    "street": f"Default Test Street {i + 1}",
                    "city": "Delhi",
                    "pincode": "110001",
                    "is_default": True,
                },
            )

        resp = _request(session, "GET", base_url, "/api/v1/addresses", user_headers)
        assert resp.status_code == 200
        addresses = extract_list_payload(resp.json())
        defaults = [a for a in addresses if a.get("is_default") is True]
        assert len(defaults) <= 1, "More than one address is marked as default"

    def test_delete_nonexistent(self, session, base_url, user_headers):
        resp = _request(session, "DELETE", base_url, "/api/v1/addresses/999999999", user_headers)
        assert resp.status_code == 404

    def test_update_street_is_reflected(self, session, base_url, user_headers):
        create_resp = _request(
            session, "POST", base_url, "/api/v1/addresses", user_headers,
            json={
                "label": "OTHER",
                "street": "Original Street 10",
                "city": "Chennai",
                "pincode": "600001",
                "is_default": False,
            },
        )
        assert create_resp.status_code in (200, 201)
        data = create_resp.json()
        address_obj = _pick_key(data, "address", "data", "result") or data
        addr_id = extract_int_id(address_obj, ("address_id", "id"))
        if addr_id is None:
            pytest.skip("Could not extract address_id from create response")

        update_resp = _request(
            session, "PUT", base_url, f"/api/v1/addresses/{addr_id}", user_headers,
            json={"street": "Updated Street 99", "is_default": False},
        )
        assert update_resp.status_code == 200
        updated = update_resp.json()
        updated_obj = _pick_key(updated, "address", "data", "result") or updated
        street = _pick_key(updated_obj, "street")
        if street is not None:
            assert street == "Updated Street 99"


# PRODUCTS

class TestProducts:
    def test_product_detail_fields(self, session, base_url, user_headers, existing_product_id):
        resp = _request(session, "GET", base_url, f"/api/v1/products/{existing_product_id}", user_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert any(k in data for k in ("product_id", "id", "name"))

    def test_product_price_is_numeric(self, session, base_url, user_headers, existing_product_id):
        resp = _request(session, "GET", base_url, f"/api/v1/products/{existing_product_id}", user_headers)
        assert resp.status_code == 200
        price = _pick_key(resp.json(), "price", "unit_price")
        if price is not None:
            assert isinstance(price, (int, float))

    def test_product_list_search_param(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/products?search=a", user_headers)
        assert resp.status_code in (200, 400)

    def test_product_list_sort_asc(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/products?sort=price_asc", user_headers)
        assert resp.status_code in (200, 400)

    def test_product_list_sort_desc(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/products?sort=price_desc", user_headers)
        assert resp.status_code in (200, 400)


# CART

class TestCart:
    def test_get_cart(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/cart", user_headers)
        assert resp.status_code == 200

    def test_update_quantity_to_zero(self, session, base_url, user_headers, existing_product_id):
        _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": existing_product_id, "quantity": 1},
        )
        resp = _request(
            session, "POST", base_url, "/api/v1/cart/update", user_headers,
            json={"product_id": existing_product_id, "quantity": 0},
        )
        assert resp.status_code == 400

    def test_remove_absent_product(self, session, base_url, user_headers):
        _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        resp = _request(
            session, "POST", base_url, "/api/v1/cart/remove", user_headers,
            json={"product_id": 999999998},
        )
        assert resp.status_code == 404

    def test_clear_leaves_cart_empty(self, session, base_url, user_headers, existing_product_id):
        _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": existing_product_id, "quantity": 1},
        )
        clear_resp = _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        assert clear_resp.status_code in (200, 204)

        cart_resp = _request(session, "GET", base_url, "/api/v1/cart", user_headers)
        assert cart_resp.status_code == 200
        payload = cart_resp.json()
        items = extract_list_payload(payload)
        if not items and isinstance(payload, dict):
            items = _pick_key(payload, "cart_items", "items") or []
        assert len(items) == 0

    def test_add_quantity_over_stock(self, session, base_url, user_headers, existing_product_id):
        resp = _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": existing_product_id, "quantity": 9999999},
        )
        assert resp.status_code == 400


# CHECKOUT
class TestCheckout:
    def _prep_cart(self, session, base_url, user_headers, product_id):
        _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        add_resp = _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": product_id, "quantity": 1},
        )
        assert add_resp.status_code in (200, 201)

    def test_empty_cart_rejected(self, session, base_url, user_headers):
        _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        resp = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={"payment_method": "COD"},
        )
        assert resp.status_code == 400

    def test_cod_checkout(self, session, base_url, user_headers, existing_product_id):
        self._prep_cart(session, base_url, user_headers, existing_product_id)
        resp = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={"payment_method": "COD"},
        )
        assert resp.status_code in (200, 201, 400)

    def test_card_sets_payment_status_paid(self, session, base_url, user_headers, existing_product_id):
        self._prep_cart(session, base_url, user_headers, existing_product_id)
        resp = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={"payment_method": "CARD"},
        )
        if resp.status_code not in (200, 201):
            pytest.skip("Checkout did not succeed")
        data = resp.json()
        order = _pick_key(data, "order", "data", "result")
        if isinstance(order, dict) and "payment_status" in order:
            assert order["payment_status"] == "PAID"

    def test_cod_sets_payment_status_pending(self, session, base_url, user_headers, existing_product_id):
        self._prep_cart(session, base_url, user_headers, existing_product_id)
        resp = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={"payment_method": "COD"},
        )
        if resp.status_code not in (200, 201):
            pytest.skip("Checkout did not succeed")
        data = resp.json()
        order = _pick_key(data, "order", "data", "result")
        if isinstance(order, dict) and "payment_status" in order:
            assert order["payment_status"] == "PENDING"

    def test_missing_payment_method(self, session, base_url, user_headers, existing_product_id):
        self._prep_cart(session, base_url, user_headers, existing_product_id)
        resp = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={},
        )
        assert resp.status_code == 400

    def test_gst_calculation(self, session, base_url, user_headers, existing_product_id):
        self._prep_cart(session, base_url, user_headers, existing_product_id)
        checkout_resp = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={"payment_method": "CARD"},
        )
        if checkout_resp.status_code not in (200, 201):
            pytest.skip("Checkout failed")
        data = checkout_resp.json()
        order = _pick_key(data, "order", "data", "result") or data
        order_id = extract_int_id(order, ("order_id", "id"))
        if order_id is None:
            pytest.skip("Could not extract order_id")

        invoice_resp = _request(session, "GET", base_url, f"/api/v1/orders/{order_id}/invoice", user_headers)
        if invoice_resp.status_code != 200:
            pytest.skip("Invoice endpoint unavailable")
        inv = invoice_resp.json()
        subtotal = _pick_key(inv, "subtotal", "sub_total")
        gst = _pick_key(inv, "gst", "gst_amount", "tax")
        total = _pick_key(inv, "total", "grand_total")
        if all(isinstance(v, (int, float)) for v in (subtotal, gst, total)):
            assert math.isclose(gst, round(subtotal * 0.05, 2), abs_tol=0.01), \
                f"GST mismatch: expected {subtotal * 0.05:.2f}, got {gst}"
            assert math.isclose(total, round(subtotal + gst, 2), abs_tol=0.01), \
                f"Total mismatch: expected {subtotal + gst:.2f}, got {total}"


# WALLET
class TestWallet:
    def test_get_balance(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/wallet", user_headers)
        assert resp.status_code == 200
        data = resp.json()
        balance = _pick_key(data, "balance", "wallet_balance", "amount")
        if balance is not None:
            assert isinstance(balance, (int, float))

    def test_add_valid_amount(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/wallet/add", user_headers,
            json={"amount": 500},
        )
        assert resp.status_code in (200, 201)

    def test_add_zero_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/wallet/add", user_headers,
            json={"amount": 0},
        )
        assert resp.status_code == 400

    def test_add_negative_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/wallet/add", user_headers,
            json={"amount": -100},
        )
        assert resp.status_code == 400

    def test_add_over_limit_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/wallet/add", user_headers,
            json={"amount": 100001},
        )
        assert resp.status_code == 400

    def test_add_at_limit_accepted(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/wallet/add", user_headers,
            json={"amount": 100000},
        )
        assert resp.status_code in (200, 201)

    def test_pay_deducts_exact_amount(self, session, base_url, user_headers):
        _request(
            session, "POST", base_url, "/api/v1/wallet/add", user_headers,
            json={"amount": 1000},
        )
        before_resp = _request(session, "GET", base_url, "/api/v1/wallet", user_headers)
        assert before_resp.status_code == 200
        before_balance = _pick_key(before_resp.json(), "balance", "wallet_balance", "amount")
        if not isinstance(before_balance, (int, float)):
            pytest.skip("Cannot read wallet balance")

        pay_amount = 50
        pay_resp = _request(
            session, "POST", base_url, "/api/v1/wallet/pay", user_headers,
            json={"amount": pay_amount},
        )
        assert pay_resp.status_code in (200, 201)

        after_resp = _request(session, "GET", base_url, "/api/v1/wallet", user_headers)
        after_balance = _pick_key(after_resp.json(), "balance", "wallet_balance", "amount")
        if isinstance(after_balance, (int, float)):
            assert math.isclose(after_balance, before_balance - pay_amount, abs_tol=0.01)

    def test_pay_insufficient_balance(self, session, base_url, user_headers):
        balance_resp = _request(session, "GET", base_url, "/api/v1/wallet", user_headers)
        balance = _pick_key(balance_resp.json(), "balance", "wallet_balance", "amount") or 0
        resp = _request(
            session, "POST", base_url, "/api/v1/wallet/pay", user_headers,
            json={"amount": balance + 999999},
        )
        assert resp.status_code == 400

    def test_pay_zero_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/wallet/pay", user_headers,
            json={"amount": 0},
        )
        assert resp.status_code == 400


# LOYALTY POINTS
class TestLoyalty:
    def test_get_points(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/loyalty", user_headers)
        assert resp.status_code == 200
        data = resp.json()
        points = _pick_key(data, "points", "loyalty_points", "balance")
        if points is not None:
            assert isinstance(points, (int, float))

    def test_redeem_zero_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/loyalty/redeem", user_headers,
            json={"points": 0},
        )
        assert resp.status_code == 400

    def test_redeem_negative_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/loyalty/redeem", user_headers,
            json={"points": -10},
        )
        assert resp.status_code == 400

    def test_redeem_more_than_balance_rejected(self, session, base_url, user_headers):
        points_resp = _request(session, "GET", base_url, "/api/v1/loyalty", user_headers)
        current = _pick_key(points_resp.json(), "points", "loyalty_points", "balance") or 0
        resp = _request(
            session, "POST", base_url, "/api/v1/loyalty/redeem", user_headers,
            json={"points": int(current) + 999999},
        )
        assert resp.status_code == 400


# ORDERS
class TestOrders:
    def test_get_orders(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/orders", user_headers)
        assert resp.status_code == 200
        assert isinstance(extract_list_payload(resp.json()), list)

    def test_get_nonexistent_order(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/orders/999999999", user_headers)
        assert resp.status_code == 404

    def test_cancel_nonexistent_order(self, session, base_url, user_headers):
        resp = _request(session, "POST", base_url, "/api/v1/orders/999999999/cancel", user_headers)
        assert resp.status_code == 404

    def test_cancel_restores_stock(self, session, base_url, user_headers, existing_product_id, admin_headers):
        prod_before = _request(session, "GET", base_url, f"/api/v1/products/{existing_product_id}", user_headers)
        stock_before = _pick_key(prod_before.json(), "stock", "quantity", "stock_quantity")

        _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        add_resp = _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": existing_product_id, "quantity": 1},
        )
        if add_resp.status_code not in (200, 201):
            pytest.skip("Could not add to cart")

        checkout_resp = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={"payment_method": "CARD"},
        )
        if checkout_resp.status_code not in (200, 201):
            pytest.skip("Checkout failed")

        data = checkout_resp.json()
        order = _pick_key(data, "order", "data", "result") or data
        order_id = extract_int_id(order, ("order_id", "id"))
        if order_id is None:
            pytest.skip("Could not extract order_id")

        cancel_resp = _request(session, "POST", base_url, f"/api/v1/orders/{order_id}/cancel", user_headers)
        assert cancel_resp.status_code in (200, 201)

        if not isinstance(stock_before, (int, float)):
            pytest.skip("Stock before was not numeric")

        prod_after = _request(session, "GET", base_url, f"/api/v1/products/{existing_product_id}", user_headers)
        stock_after = _pick_key(prod_after.json(), "stock", "quantity", "stock_quantity")
        if isinstance(stock_after, (int, float)):
            assert stock_after == stock_before, \
                f"Stock not restored: before={stock_before}, after={stock_after}"

    def test_invoice_has_required_fields(self, session, base_url, user_headers, existing_product_id):
        _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        add = _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": existing_product_id, "quantity": 1},
        )
        if add.status_code not in (200, 201):
            pytest.skip("Could not add item to cart")

        co = _request(
            session, "POST", base_url, "/api/v1/checkout", user_headers,
            json={"payment_method": "CARD"},
        )
        if co.status_code not in (200, 201):
            pytest.skip("Checkout failed")

        order = _pick_key(co.json(), "order", "data", "result") or co.json()
        order_id = extract_int_id(order, ("order_id", "id"))
        if order_id is None:
            pytest.skip("No order_id")

        inv = _request(session, "GET", base_url, f"/api/v1/orders/{order_id}/invoice", user_headers)
        assert inv.status_code == 200
        inv_data = inv.json()
        assert any(k in inv_data for k in ("subtotal", "sub_total")), "Invoice missing subtotal"
        assert any(k in inv_data for k in ("gst", "gst_amount", "tax")), "Invoice missing GST"
        assert any(k in inv_data for k in ("total", "grand_total")), "Invoice missing total"


# COUPONS

class TestCoupons:
    def _first_active_coupon(self, session, base_url, admin_headers):
        resp = session.get(f"{base_url}/api/v1/admin/coupons", headers=admin_headers, timeout=8)
        if resp.status_code != 200:
            return None
        for coupon in extract_list_payload(resp.json()):
            if not (coupon.get("is_expired") or coupon.get("expired")):
                return coupon
        return None

    def test_apply_nonexistent_code(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/coupon/apply", user_headers,
            json={"code": "INVALIDCOUPON99999"},
        )
        assert resp.status_code in (400, 404)

    def test_apply_valid_coupon_lowers_total(self, session, base_url, user_headers, admin_headers, existing_product_id):
        coupon = self._first_active_coupon(session, base_url, admin_headers)
        if coupon is None:
            pytest.skip("No active coupon available")
        code = _pick_key(coupon, "code", "coupon_code")
        if not code:
            pytest.skip("Could not read coupon code")

        _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": existing_product_id, "quantity": 1},
        )

        before_total = _pick_key(
            _request(session, "GET", base_url, "/api/v1/cart", user_headers).json(),
            "total", "cart_total", "grand_total",
        )

        apply_resp = _request(
            session, "POST", base_url, "/api/v1/coupon/apply", user_headers,
            json={"code": code},
        )
        if apply_resp.status_code not in (200, 201):
            pytest.skip(f"Coupon could not be applied (status {apply_resp.status_code})")

        after_total = _pick_key(
            _request(session, "GET", base_url, "/api/v1/cart", user_headers).json(),
            "total", "cart_total", "grand_total", "discounted_total",
        )
        if isinstance(before_total, (int, float)) and isinstance(after_total, (int, float)):
            assert after_total <= before_total, "Coupon did not reduce cart total"

    def test_remove_coupon(self, session, base_url, user_headers, admin_headers, existing_product_id):
        coupon = self._first_active_coupon(session, base_url, admin_headers)
        if coupon is None:
            pytest.skip("No active coupon available")
        code = _pick_key(coupon, "code", "coupon_code")
        if not code:
            pytest.skip("Could not read coupon code")

        _request(session, "DELETE", base_url, "/api/v1/cart/clear", user_headers)
        _request(
            session, "POST", base_url, "/api/v1/cart/add", user_headers,
            json={"product_id": existing_product_id, "quantity": 1},
        )
        _request(session, "POST", base_url, "/api/v1/coupon/apply", user_headers, json={"code": code})

        remove_resp = _request(
            session, "POST", base_url, "/api/v1/coupon/remove", user_headers,
            json={"code": code},
        )
        assert remove_resp.status_code in (200, 201, 204)

# REVIEWS
class TestReviews:
    def test_get_reviews(self, session, base_url, user_headers, existing_product_id):
        resp = _request(session, "GET", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers)
        assert resp.status_code == 200
        assert isinstance(extract_list_payload(resp.json()), list)

    def test_rating_1_accepted(self, session, base_url, user_headers, existing_product_id):
        resp = _request(
            session, "POST", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers,
            json={"rating": 1, "comment": "Not great at all."},
        )
        assert resp.status_code in (200, 201)

    def test_rating_5_accepted(self, session, base_url, user_headers, existing_product_id):
        resp = _request(
            session, "POST", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers,
            json={"rating": 5, "comment": "Excellent product!"},
        )
        assert resp.status_code in (200, 201)

    def test_rating_6_rejected(self, session, base_url, user_headers, existing_product_id):
        resp = _request(
            session, "POST", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers,
            json={"rating": 6, "comment": "Too high"},
        )
        assert resp.status_code == 400

    def test_empty_comment_rejected(self, session, base_url, user_headers, existing_product_id):
        resp = _request(
            session, "POST", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers,
            json={"rating": 3, "comment": ""},
        )
        assert resp.status_code == 400

    def test_comment_over_200_chars_rejected(self, session, base_url, user_headers, existing_product_id):
        resp = _request(
            session, "POST", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers,
            json={"rating": 3, "comment": "A" * 201},
        )
        assert resp.status_code == 400

    def test_average_rating_is_numeric(self, session, base_url, user_headers, existing_product_id):
        for rating in (1, 2):
            _request(
                session, "POST", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers,
                json={"rating": rating, "comment": f"Rating {rating} test"},
            )
        resp = _request(session, "GET", base_url, f"/api/v1/products/{existing_product_id}/reviews", user_headers)
        assert resp.status_code == 200
        avg = _pick_key(resp.json(), "average_rating", "avg_rating", "average")
        if isinstance(avg, (int, float)) and avg != 0:
            assert avg >= 1

# SUPPORT TICKETS
class TestSupportTickets:
    def test_get_tickets(self, session, base_url, user_headers):
        resp = _request(session, "GET", base_url, "/api/v1/support/tickets", user_headers)
        assert resp.status_code == 200
        assert isinstance(extract_list_payload(resp.json()), list)

    def test_empty_message_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Valid Subject", "message": ""},
        )
        assert resp.status_code == 400

    def test_message_over_500_chars_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Valid Subject", "message": "A" * 501},
        )
        assert resp.status_code == 400

    def test_subject_min_length_accepted(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Hello", "message": "Valid message body here."},
        )
        assert resp.status_code in (200, 201)

    def test_subject_max_length_accepted(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "A" * 100, "message": "Valid message body here."},
        )
        assert resp.status_code in (200, 201)

    def test_subject_over_max_rejected(self, session, base_url, user_headers):
        resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "A" * 101, "message": "Valid message body here."},
        )
        assert resp.status_code == 400

    def test_message_stored_verbatim(self, session, base_url, user_headers):
        unique_message = "Unique message with special chars: !@#$% 12345"
        create_resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Storage check", "message": unique_message},
        )
        assert create_resp.status_code in (200, 201)
        body = create_resp.json()
        ticket_obj = _pick_key(body, "ticket", "data", "result")
        if isinstance(ticket_obj, dict):
            saved = _pick_key(ticket_obj, "message", "body")
            if saved is not None:
                assert saved == unique_message

    def test_open_to_in_progress(self, session, base_url, user_headers):
        create_resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Status check one", "message": "Moving to in progress"},
        )
        assert create_resp.status_code in (200, 201)
        ticket_obj = _pick_key(create_resp.json(), "ticket", "data", "result")
        if not isinstance(ticket_obj, dict):
            pytest.skip("Could not extract ticket")
        ticket_id = extract_int_id(ticket_obj, ("ticket_id", "id"))
        if ticket_id is None:
            pytest.skip("Missing ticket_id")

        resp = _request(
            session, "PUT", base_url, f"/api/v1/support/tickets/{ticket_id}", user_headers,
            json={"status": "IN_PROGRESS"},
        )
        assert resp.status_code in (200, 201)

    def test_in_progress_to_closed(self, session, base_url, user_headers):
        create_resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Status check two", "message": "Moving through full flow"},
        )
        assert create_resp.status_code in (200, 201)
        ticket_obj = _pick_key(create_resp.json(), "ticket", "data", "result")
        if not isinstance(ticket_obj, dict):
            pytest.skip("Could not extract ticket")
        ticket_id = extract_int_id(ticket_obj, ("ticket_id", "id"))
        if ticket_id is None:
            pytest.skip("Missing ticket_id")

        _request(
            session, "PUT", base_url, f"/api/v1/support/tickets/{ticket_id}", user_headers,
            json={"status": "IN_PROGRESS"},
        )
        resp = _request(
            session, "PUT", base_url, f"/api/v1/support/tickets/{ticket_id}", user_headers,
            json={"status": "CLOSED"},
        )
        assert resp.status_code in (200, 201)

    def test_open_to_closed_skipping_in_progress(self, session, base_url, user_headers):
        create_resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Skip step test", "message": "Trying to skip IN_PROGRESS"},
        )
        assert create_resp.status_code in (200, 201)
        ticket_obj = _pick_key(create_resp.json(), "ticket", "data", "result")
        if not isinstance(ticket_obj, dict):
            pytest.skip("Could not extract ticket")
        ticket_id = extract_int_id(ticket_obj, ("ticket_id", "id"))
        if ticket_id is None:
            pytest.skip("Missing ticket_id")

        resp = _request(
            session, "PUT", base_url, f"/api/v1/support/tickets/{ticket_id}", user_headers,
            json={"status": "CLOSED"},
        )
        assert resp.status_code == 400

    def test_backward_status_transition(self, session, base_url, user_headers):
        create_resp = _request(
            session, "POST", base_url, "/api/v1/support/ticket", user_headers,
            json={"subject": "Backward test", "message": "Trying to go back to open"},
        )
        assert create_resp.status_code in (200, 201)
        ticket_obj = _pick_key(create_resp.json(), "ticket", "data", "result")
        if not isinstance(ticket_obj, dict):
            pytest.skip("Could not extract ticket")
        ticket_id = extract_int_id(ticket_obj, ("ticket_id", "id"))
        if ticket_id is None:
            pytest.skip("Missing ticket_id")

        adv = _request(
            session, "PUT", base_url, f"/api/v1/support/tickets/{ticket_id}", user_headers,
            json={"status": "IN_PROGRESS"},
        )
        if adv.status_code not in (200, 201):
            pytest.skip("Could not advance ticket")

        resp = _request(
            session, "PUT", base_url, f"/api/v1/support/tickets/{ticket_id}", user_headers,
            json={"status": "OPEN"},
        )
        assert resp.status_code == 400
