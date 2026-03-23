import uuid
from data_store import load, save
from registration import get_member
from crew_management import set_availability
from inventory import car_exists, deduct_cash

RACE_STATUSES = {"scheduled", "in_progress", "completed", "cancelled"}

def create_race(name: str, location: str, entry_fee: float = 0.0) -> dict:
    # Create a new race entry
    name = name.strip()
    location = location.strip()
    if not name:
        raise ValueError("Race name cannot be empty.")
    if not location:
        raise ValueError("Race location cannot be empty.")
    if entry_fee < 0:
        raise ValueError("Entry fee cannot be negative.")

    races = load("races")

    # Prevent duplicate race names
    for race in races.values():
        if race["name"].lower() == name.lower():
            raise ValueError(f"A race named '{name}' already exists.")

    race_id = str(uuid.uuid4())
    record = {
        "id":        race_id,
        "name":      name,
        "location":  location,
        "entry_fee": entry_fee,
        "status":    "scheduled",
        "drivers":   [],   # list of member_ids
        "cars":      [],   # list of car names (parallel to drivers)
    }
    races[race_id] = record
    save("races", races)
    return record

def enter_race(race_id: str, member_id: str, car_name: str) -> dict:
    # Enter a driver into a race with a specific car
    races = load("races")
    if race_id not in races:
        raise KeyError(f"No race found with ID '{race_id}'.")

    race = races[race_id]
    if race["status"] not in {"scheduled", "in_progress"}:
        raise ValueError(
            f"Race '{race['name']}' is '{race['status']}' and cannot accept new entries."
        )

    member = get_member(member_id)
    if member["role"] != "driver":
        raise ValueError(
            f"'{member['name']}' has role '{member['role']}', not 'driver'. "
            "Only drivers may enter races."
        )

    if member_id in race["drivers"]:
        raise ValueError(f"'{member['name']}' is already entered in this race.")

    if not member["is_available"]:
        raise ValueError(f"'{member['name']}' is currently unavailable.")

    if not car_exists(car_name):
        raise ValueError(f"Car '{car_name}' is not available in inventory.")

    entry_fee = race.get("entry_fee", 0.0)
    if entry_fee > 0:
        deduct_cash(entry_fee)

    race["drivers"].append(member_id)
    race["cars"].append(car_name)
    races[race_id] = race
    save("races", races)

    # Mark driver as unavailable
    set_availability(member_id, False)

    return race

def start_race(race_id: str) -> dict:
    #Transition a race from 'scheduled' to 'in_progress'
    races = load("races")
    if race_id not in races:
        raise KeyError(f"No race found with ID '{race_id}'.")

    race = races[race_id]
    if race["status"] != "scheduled":
        raise ValueError(f"Race '{race['name']}' cannot be started; status is '{race['status']}'.")
    if not race["drivers"]:
        raise ValueError(f"Race '{race['name']}' has no drivers entered.")

    race["status"] = "in_progress"
    save("races", races)
    return race

def cancel_race(race_id: str) -> dict:
    # Cancel a race and free up all entered drivers
    races = load("races")
    if race_id not in races:
        raise KeyError(f"No race found with ID '{race_id}'.")

    race = races[race_id]
    if race["status"] == "completed":
        raise ValueError(f"Cannot cancel a completed race.")

    # Free all drivers
    for mid in race["drivers"]:
        try:
            set_availability(mid, True)
        except KeyError:
            pass  # member may have been removed

    race["status"] = "cancelled"
    save("races", races)
    return race

def get_race(race_id: str) -> dict:
    # Fetch a race by ID
    races = load("races")
    if race_id not in races:
        raise KeyError(f"No race found with ID '{race_id}'.")
    return races[race_id]

def get_all_races() -> dict:
    # Return all races
    return load("races")