from data_store import load, save

ITEM_CATEGORIES = {"cars", "spare_parts", "tools"}


def _load_inventory() -> dict:
    return load("inventory")


def _save_inventory(inv: dict) -> None:
    save("inventory", inv)


def get_cash_balance() -> float:
    # return the current cash balance
    return _load_inventory()["cash_balance"]


def add_cash(amount: float) -> float:
    #Add funds to the cash balance (e.g., prize money, bet winnings)
    if amount <= 0:
        raise ValueError("Amount to add must be positive.")
    inv = _load_inventory()
    inv["cash_balance"] = round(inv["cash_balance"] + amount, 2)
    _save_inventory(inv)
    return inv["cash_balance"]


def deduct_cash(amount: float) -> float:
    # deduct funds from the cash balance (e.g., race entry fees, bets)
    if amount <= 0:
        raise ValueError("Amount to deduct must be positive.")
    inv = _load_inventory()
    if inv["cash_balance"] < amount:
        raise ValueError(
            f"Insufficient funds. Balance: {inv['cash_balance']}, Requested: {amount}."
        )
    inv["cash_balance"] = round(inv["cash_balance"] - amount, 2)
    _save_inventory(inv)
    return inv["cash_balance"]


def add_item(category: str, item_name: str, quantity: int = 1, **attributes) -> dict:
    # add or update an item in the specified category
    if category not in ITEM_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'. Choose from: {ITEM_CATEGORIES}.")
    if quantity < 1:
        raise ValueError("Quantity must be at least 1.")

    inv = _load_inventory()
    cat = inv[category]

    if item_name in cat:
        cat[item_name]["quantity"] += quantity
    else:
        cat[item_name] = {"quantity": quantity, **attributes}

    _save_inventory(inv)
    return cat[item_name]


def remove_item(category: str, item_name: str, quantity: int = 1) -> dict:
    # remove a quantity of an item. Deletes the record if quantity reaches 0

    if category not in ITEM_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'.")

    inv = _load_inventory()
    cat = inv[category]

    if item_name not in cat:
        raise KeyError(f"Item '{item_name}' not found in '{category}'.")
    if cat[item_name]["quantity"] < quantity:
        raise ValueError(
            f"Cannot remove {quantity} of '{item_name}'; only {cat[item_name]['quantity']} available."
        )

    cat[item_name]["quantity"] -= quantity
    if cat[item_name]["quantity"] == 0:
        del cat[item_name]

    _save_inventory(inv)
    return inv[category].get(item_name, {"quantity": 0, "removed": True})


def get_item(category: str, item_name: str) -> dict:
    # fetch a specific item
    if category not in ITEM_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'.")
    inv = _load_inventory()
    if item_name not in inv[category]:
        raise KeyError(f"Item '{item_name}' not found in '{category}'.")
    return inv[category][item_name]


def list_items(category: str) -> dict:
    # list all items in a category
    if category not in ITEM_CATEGORIES:
        raise ValueError(f"Invalid category '{category}'.")
    return _load_inventory()[category]


def car_exists(car_name: str) -> bool:
    # Check whether a car is available in inventory (quantity >= 1)
    inv = _load_inventory()
    car = inv["cars"].get(car_name)
    return car is not None and car.get("quantity", 0) >= 1


def set_car_condition(car_name: str, condition: str) -> dict:
    # update the condition of a car (e.g., 'good', 'damaged', 'totaled')
    inv = _load_inventory()
    if car_name not in inv["cars"]:
        raise KeyError(f"Car '{car_name}' not found in inventory.")
    inv["cars"][car_name]["condition"] = condition
    _save_inventory(inv)
    return inv["cars"][car_name]


def get_full_inventory() -> dict:
    # return the complete inventory snapshot
    return _load_inventory()