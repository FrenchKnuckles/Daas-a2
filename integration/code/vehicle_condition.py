from datetime import datetime, timezone
from data_store import load, save
from inventory import car_exists, set_car_condition
from crew_management import set_availability

CONDITION_LEVELS = ["totaled", "critical", "damaged", "worn", "good", "excellent"]
RACE_ELIGIBLE_CONDITIONS = {"good", "excellent"}
REPAIRABLE_CONDITIONS = {"critical", "damaged", "worn"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _load_vc() -> dict:
    return load("vehicle_condition")


def _save_vc(data: dict) -> None:
    save("vehicle_condition", data)


def register_car_condition(car_name: str, initial_condition: str = "good") -> dict:
    #Create a condition record for a car that already exists in inventory
    
    if not car_exists(car_name):
        raise KeyError(f"Car '{car_name}' does not exist in inventory.")
    if initial_condition not in CONDITION_LEVELS:
        raise ValueError(
            f"Invalid condition '{initial_condition}'. "
            f"Must be one of: {CONDITION_LEVELS}."
        )

    vc = _load_vc()
    record = {
        "car_name":  car_name,
        "condition": initial_condition,
        "is_grounded": initial_condition not in RACE_ELIGIBLE_CONDITIONS,
        "repair_in_progress": False,
        "assigned_mechanic_id": None,
        "log": [
            {"event": "registered", "condition": initial_condition, "timestamp": _now()}
        ],
    }
    vc[car_name] = record
    _save_vc(vc)
    # Keep inventory in sync
    set_car_condition(car_name, initial_condition)
    return record


def get_condition(car_name: str) -> dict:
    vc = _load_vc()
    if car_name not in vc:
        raise KeyError(f"No condition record for car '{car_name}'.")
    return vc[car_name]


def apply_damage(car_name: str, severity: int = 1, notes: str = "") -> dict:

    if severity < 1:
        raise ValueError("Damage severity must be at least 1.")

    vc = _load_vc()
    if car_name not in vc:
        raise KeyError(f"No condition record for car '{car_name}'.")

    record = vc[car_name]
    if record["condition"] == "totaled":
        raise ValueError(f"Car '{car_name}' is already totaled and cannot take more damage.")

    current_idx = CONDITION_LEVELS.index(record["condition"])
    new_idx = max(0, current_idx - severity)
    new_condition = CONDITION_LEVELS[new_idx]

    record["condition"] = new_condition
    record["is_grounded"] = new_condition not in RACE_ELIGIBLE_CONDITIONS
    record["log"].append({
        "event":     "damage",
        "condition": new_condition,
        "severity":  severity,
        "notes":     notes,
        "timestamp": _now(),
    })

    vc[car_name] = record
    _save_vc(vc)
    set_car_condition(car_name, new_condition)
    return record


def start_repair(car_name: str, mechanic_id: str) -> dict:
    #Assign an available mechanic to repair a car
    #Car must be in a repairable condition (not 'good', 'excellent', or 'totaled')

    vc = _load_vc()
    if car_name not in vc:
        raise KeyError(f"No condition record for car '{car_name}'.")

    record = vc[car_name]

    if record["condition"] == "totaled":
        raise ValueError(
            f"Car '{car_name}' is totaled and cannot be repaired. Remove it from inventory."
        )
    if record["condition"] not in REPAIRABLE_CONDITIONS:
        raise ValueError(
            f"Car '{car_name}' is in '{record['condition']}' condition and does not need repair."
        )
    if record["repair_in_progress"]:
        raise ValueError(f"Car '{car_name}' already has a repair in progress.")

    # Validate mechanic
    members = load("members")
    if mechanic_id not in members:
        raise KeyError(f"No member found with ID '{mechanic_id}'.")
    mechanic = members[mechanic_id]
    if mechanic["role"] != "mechanic":
        raise ValueError(
            f"'{mechanic['name']}' is a '{mechanic['role']}', not a mechanic."
        )
    if not mechanic["is_available"]:
        raise ValueError(f"Mechanic '{mechanic['name']}' is currently unavailable.")

    # Lock mechanic
    set_availability(mechanic_id, False)

    record["repair_in_progress"] = True
    record["assigned_mechanic_id"] = mechanic_id
    record["log"].append({
        "event":       "repair_started",
        "mechanic_id": mechanic_id,
        "mechanic":    mechanic["name"],
        "timestamp":   _now(),
    })

    vc[car_name] = record
    _save_vc(vc)
    return record


def complete_repair(car_name: str) -> dict:
    #Finish a repair, improving condition by one level (max 'good')
    #assigned mechanic is freed
    vc = _load_vc()
    if car_name not in vc:
        raise KeyError(f"No condition record for car '{car_name}'.")

    record = vc[car_name]
    if not record["repair_in_progress"]:
        raise ValueError(f"Car '{car_name}' has no repair in progress.")

    current_idx = CONDITION_LEVELS.index(record["condition"])
    # Cap at 'good' (index 4) — full restoration requires a full service
    good_idx = CONDITION_LEVELS.index("good")
    new_idx = min(current_idx + 1, good_idx)
    new_condition = CONDITION_LEVELS[new_idx]

    mechanic_id = record["assigned_mechanic_id"]
    record["condition"] = new_condition
    record["is_grounded"] = new_condition not in RACE_ELIGIBLE_CONDITIONS
    record["repair_in_progress"] = False
    record["assigned_mechanic_id"] = None
    record["log"].append({
        "event":       "repair_completed",
        "condition":   new_condition,
        "mechanic_id": mechanic_id,
        "timestamp":   _now(),
    })

    vc[car_name] = record
    _save_vc(vc)
    set_car_condition(car_name, new_condition)

    # Free mechanic
    if mechanic_id:
        try:
            set_availability(mechanic_id, True)
        except KeyError:
            pass

    return record


def full_service(car_name: str, mechanic_id: str) -> dict:
    #Performing a full service restores condition directly to 'excellent'
    #Requires a mechanic, Bypasses the one level at a time repair limit
    vc = _load_vc()
    if car_name not in vc:
        raise KeyError(f"No condition record for car '{car_name}'.")

    record = vc[car_name]
    if record["condition"] == "totaled":
        raise ValueError(f"Car '{car_name}' is totaled and cannot be serviced.")
    if record["repair_in_progress"]:
        raise ValueError(f"Car '{car_name}' already has a repair in progress.")

    members = load("members")
    if mechanic_id not in members:
        raise KeyError(f"No member found with ID '{mechanic_id}'.")
    mechanic = members[mechanic_id]
    if mechanic["role"] != "mechanic":
        raise ValueError(f"'{mechanic['name']}' is not a mechanic.")
    if not mechanic["is_available"]:
        raise ValueError(f"Mechanic '{mechanic['name']}' is unavailable.")

    set_availability(mechanic_id, False)

    record["condition"] = "excellent"
    record["is_grounded"] = False
    record["log"].append({
        "event":       "full_service",
        "mechanic_id": mechanic_id,
        "mechanic":    mechanic["name"],
        "timestamp":   _now(),
    })

    vc[car_name] = record
    _save_vc(vc)
    set_car_condition(car_name, "excellent")
    set_availability(mechanic_id, True)
    return record


def is_race_eligible(car_name: str) -> bool:
    # True if the car is in a condition suitable for racing
    vc = _load_vc()
    if car_name not in vc:
        raise KeyError(f"No condition record for car '{car_name}'.")
    return not vc[car_name]["is_grounded"]


def get_all_conditions() -> dict:
    # vehicle condition records
    return _load_vc()


def get_condition_log(car_name: str) -> list:
    # event log for a specific car
    return get_condition(car_name)["log"]