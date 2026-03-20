import copy

_DEFAULTS = {
    "members": {},
    "inventory": {
        "cars": {},
        "spare_parts": {},
        "tools": {},
        "cash_balance": 100000.0,
    },
    "races": {},
    "results": {},
    "missions": {},
    "leaderboard": {},
    "vehicle_condition": {},
}

_STORE = copy.deepcopy(_DEFAULTS)

def load(store_name: str) -> dict:
    if store_name not in _STORE:
        raise KeyError(f"Unknown store '{store_name}'.")
    return copy.deepcopy(_STORE[store_name])


def save(store_name: str, data) -> None:
    if store_name not in _STORE:
        raise KeyError(f"Unknown store '{store_name}'.")
    _STORE[store_name] = copy.deepcopy(data)

def reset(store_name: str) -> None:
    if store_name not in _DEFAULTS:
        raise KeyError(f"Unknown store '{store_name}'.")
    _STORE[store_name] = copy.deepcopy(_DEFAULTS[store_name])

def reset_all() -> None:
    for name in _DEFAULTS:
        _STORE[name] = copy.deepcopy(_DEFAULTS[name])