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
}

_STORE = copy.deepcopy(_DEFAULTS)

def load(store_name: str) -> dict:
    # returns a deep copy of the named store
    if store_name not in _STORE:
        raise KeyError(f"Unknown store '{store_name}'.")
    return copy.deepcopy(_STORE[store_name])
 
 
def save(store_name: str, data) -> None:
    # replaces the named store with a deep copy
    if store_name not in _STORE:
        raise KeyError(f"Unknown store '{store_name}'.")
    _STORE[store_name] = copy.deepcopy(data)
