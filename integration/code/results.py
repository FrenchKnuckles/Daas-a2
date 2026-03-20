import uuid
from data_store import load, save
from race_management import get_race
from crew_management import set_availability
from inventory import add_cash, set_car_condition

PLACE_PRIZE_MULTIPLIERS = {1: 1.0, 2: 0.5, 3: 0.25}   # fraction of prize_pool per place

def record_result( race_id: str,finishing_order: list, # list of member_ids, index 0 = 1st place
    prize_pool: float, car_damage: dict = None,) -> dict:
    # Record the final result of a race
    race = get_race(race_id)

    if race["status"] != "in_progress":
        raise ValueError(
            f"Race '{race['name']}' is not in_progress (status: '{race['status']}')."
        )

    if prize_pool < 0:
        raise ValueError("Prize pool cannot be negative.")

    # Validate all finishers are entered drivers
    entered = set(race["drivers"])
    for mid in finishing_order:
        if mid not in entered:
            raise ValueError(
                f"Member '{mid}' is not an entered driver in race '{race['name']}'."
            )

    # Distribute prize money to top 3
    payouts = {}
    for place_index, mid in enumerate(finishing_order[:3]):
        place = place_index + 1
        payout = round(prize_pool * PLACE_PRIZE_MULTIPLIERS[place], 2)
        payouts[mid] = payout
        if payout > 0:
            add_cash(payout)

    # Update car conditions
    car_damage = car_damage or {}
    driver_to_car = dict(zip(race["drivers"], race["cars"]))
    for mid, condition in car_damage.items():
        car_name = driver_to_car.get(mid)
        if car_name:
            set_car_condition(car_name, condition)

    # Free up all drivers
    for mid in race["drivers"]:
        try:
            set_availability(mid, True)
        except KeyError:
            pass

    # Mark race completed
    races = load("races")
    races[race_id]["status"] = "completed"
    save("races", races)

    # Build and save result record
    result_id = str(uuid.uuid4())
    result = {
        "id":              result_id,
        "race_id":         race_id,
        "race_name":       race["name"],
        "finishing_order": finishing_order,
        "prize_pool":      prize_pool,
        "payouts":         payouts,
        "car_damage":      car_damage,
    }

    results = load("results")
    results[result_id] = result
    save("results", results)
    return result

def get_result(result_id: str) -> dict:
    # Fetch a result record by ID
    results = load("results")
    if result_id not in results:
        raise KeyError(f"No result found with ID '{result_id}'.")
    return results[result_id]

def get_results_for_race(race_id: str) -> list:
    # Return all results associated with a given race_id
    return [r for r in load("results").values() if r["race_id"] == race_id]

def get_all_results() -> dict:
    # Return all result records
    return load("results")