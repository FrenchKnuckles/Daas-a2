# Integration Testing

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
