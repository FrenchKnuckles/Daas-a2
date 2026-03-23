# Integration Testing

## Diagram

For the control flow diagram, the graph consists of all modules except for data_store.py connections as it is currently used as the data storing mechanism, so load and save are called in almost every function. Instead below is the list of all the functions that call load and save in data_store.py

### Functions calling `load`

These functions have arrows pointing to `load`:

- add_cash()
- add_item()
- apply_damage()
- assign_role()
- complete_mission()
- complete_repair()
- create_mission()
- create_race()
- deduct_cash()
- get_all_conditions()
- get_all_members()
- get_all_missions()
- get_all_races()
- get_available_by_role()
- get_cash_balance()
- get_condition()
- get_condition_log()
- get_crew_summary()
- get_driver_stats()
- get_full_inventory()
- get_leaderboard()
- get_member()
- get_members_by_role()
- get_mission()
- get_race()
- get_results_for_race()
- is_race_eligible()
- list_items()
- record_result()
- register_car_condition()
- register_member()
- set_availability()
- set_car_condition()
- set_skill_level()
- start_repair()
- update_leaderboard()


### Functions calling `save`

These functions have arrows pointing to `save`:

- add_item()
- apply_damage()
- assign_role()
- complete_mission()
- complete_repair()
- create_mission()
- create_race()
- deduct_cash()
- record_result()
- register_car_condition()
- register_member()
- reset_leaderboard()
- set_availability()
- set_skill_level()
- start_repair()
- unregister_member()
- update_leaderboard()

## Modules

| # | Module | Role |
|---|--------|------|
| 1 | `registration.py` | Register and remove crew members |
| 2 | `crew_management.py` | Assign roles, set skill levels, manage availability |
| 3 | `inventory.py` | Track cars, parts, tools, and cash balance |
| 4 | `race_management.py` | Create races, enter drivers, start and cancel races |
| 5 | `results.py` | Record finishing order, distribute prize money |
| 6 | `mission_planning.py` | Assign missions with role validation |
| 7 | `leaderboard.py` | Track driver rankings across all races |
| 8 | `vehicle_condition.py` | Track car health, apply damage, manage repairs |

All data is stored in memory via `data_store.py` using a shared in-memory dictionary.

## How to Run the Tests

### Run all tests

Run from inside the `integration/` directory:

```bash
python -m pytest tests/test_integration.py -v
```

## Rules Enforced

- A member must be registered before a role can be assigned
- Only members with role `driver` may enter a race
- A driver must be available (not in another race or mission) to be entered
- The car entered in a race must exist in inventory
- Race results distribute prize money to the cash balance
- Car damage from a race updates the vehicle condition record
- Missions cannot start if required roles are unavailable
- A mechanic is locked during a repair and freed on completion
- A totaled car cannot be repaired and must be removed from inventory
