"""
Modules under test:
  registration      <-> crew_management
  registration      <-> race_management
  inventory         <-> race_management
  inventory         <-> vehicle_condition
  race_management   <-> results
  results           <-> inventory(cash)
  results           <-> leaderboard
  results           <-> vehicle_condition
  vehicle_condition <-> crew_management(mechanic locking)
  mission_planning  <-> crew_management
"""


import pytest
from code import registration
from code import crew_management
from code import inventory
from code import race_management
from code import results
from code import mission_planning
from code import leaderboard
from code import vehicle_condition

def _make_driver(name="Ana", skill=5):
    m = registration.register_member(name, "driver")
    crew_management.set_skill_level(m["id"], skill)
    return m

def _make_mechanic(name="Ben"):
    return registration.register_member(name, "mechanic")

def _add_car(car_name="FastCar", condition="good"):
    inventory.add_item("cars", car_name, 1, condition=condition)
    vehicle_condition.register_car_condition(car_name, condition)
    return car_name

def _full_race_setup(d1_name="D1", d2_name="D2", car1="C1", car2="C2", race_name="TestRace"):
    """Register two drivers, two cars, create and start a race."""
    d1 = _make_driver(d1_name)
    d2 = _make_driver(d2_name)
    _add_car(car1)
    _add_car(car2)
    race = race_management.create_race(race_name, "Track")
    race_management.enter_race(race["id"], d1["id"], car1)
    race_management.enter_race(race["id"], d2["id"], car2)
    race_management.start_race(race["id"])
    return race, d1, d2


# ─────────────────────────────────────────────────────────────────────────────
# 1. Registration <-> Crew Management
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistrationCrewIntegration:
    """
    Why: A crew member must be registered before their role or skill can be
    managed. Tests verify the handoff between registration and crew_management.
    """

    def test_assign_role_after_registration(self):
        """
        Scenario: Register a driver, then promote to strategist.
        Modules: registration -> crew_management
        Expected: Role updates persist and are reflected in the member record.
        """
        m = registration.register_member("Carlos", "driver")
        updated = crew_management.assign_role(m["id"], "strategist")
        assert updated["role"] == "strategist"
        assert registration.get_member(m["id"])["role"] == "strategist"

    def test_set_skill_requires_registered_member(self):
        """
        Scenario: Set skill level on a non-existent member.
        Modules: crew_management
        Expected: KeyError — member must be registered first.
        """
        with pytest.raises(KeyError):
            crew_management.set_skill_level("fake-id-999", 7)

    def test_skill_level_persists_after_role_change(self):
        """
        Scenario: Set skill, then change role; skill should be unchanged.
        Modules: registration -> crew_management -> crew_management
        Expected: Skill level is not reset when role changes.
        """
        m = registration.register_member("Diana", "mechanic")
        crew_management.set_skill_level(m["id"], 9)
        crew_management.assign_role(m["id"], "driver")
        member = registration.get_member(m["id"])
        assert member["skill_level"] == 9
        assert member["role"] == "driver"

    def test_invalid_role_assignment_rejected(self):
        """
        Scenario: Try to assign a nonsense role.
        Modules: registration -> crew_management
        Expected: ValueError — only VALID_ROLES are accepted.
        """
        m = registration.register_member("Eve", "driver")
        with pytest.raises(ValueError, match="Invalid role"):
            crew_management.assign_role(m["id"], "ninja")


# ─────────────────────────────────────────────────────────────────────────────
# 2. Registration <-> Race Management
# ─────────────────────────────────────────────────────────────────────────────

class TestRegistrationRaceIntegration:
    """
    Why: Core business rule — only registered drivers may enter races.
    """

    def test_registered_driver_can_enter_race(self):
        """
        Scenario: Register a driver, add a car, enter the race.
        Modules: registration -> inventory -> race_management
        Expected: Driver appears in race's driver list.
        """
        driver = _make_driver("Gina")
        inventory.add_item("cars", "Racer1", 1)
        race = race_management.create_race("SunsetGP", "Highway")
        updated = race_management.enter_race(race["id"], driver["id"], "Racer1")
        assert driver["id"] in updated["drivers"]

    def test_non_driver_role_blocked_from_race(self):
        """
        Scenario: Try to enter a mechanic in a race.
        Modules: registration -> race_management
        Expected: ValueError — only drivers may race.
        """
        mech = _make_mechanic("Harry")
        inventory.add_item("cars", "Racer2", 1)
        race = race_management.create_race("DawnRace", "Suburbs")
        with pytest.raises(ValueError, match="Only drivers"):
            race_management.enter_race(race["id"], mech["id"], "Racer2")

    def test_unregistered_member_cannot_enter_race(self):
        """
        Scenario: Use a fake member_id to enter a race.
        Modules: race_management -> registration.get_member
        Expected: KeyError — member not found.
        """
        inventory.add_item("cars", "Racer3", 1)
        race = race_management.create_race("MidnightRun", "Port")
        with pytest.raises(KeyError):
            race_management.enter_race(race["id"], "not-a-real-id", "Racer3")

    def test_driver_marked_unavailable_after_entering_race(self):
        """
        Scenario: Driver enters a race; check availability flag is toggled.
        Modules: registration -> race_management -> crew_management
        Expected: Driver is_available becomes False.
        """
        driver = _make_driver("Iris")
        inventory.add_item("cars", "Turbo", 1)
        race = race_management.create_race("TurboGP", "Freeway")
        race_management.enter_race(race["id"], driver["id"], "Turbo")
        assert not registration.get_member(driver["id"])["is_available"]

    def test_car_not_in_inventory_blocks_entry(self):
        """
        Scenario: Try to enter race with a car not in inventory.
        Modules: race_management -> inventory.car_exists
        Expected: ValueError — car must exist in inventory.
        """
        driver = _make_driver("Jake")
        race = race_management.create_race("GhostRace", "Tunnel")
        with pytest.raises(ValueError, match="not available in inventory"):
            race_management.enter_race(race["id"], driver["id"], "NonExistentCar")

    def test_driver_cannot_enter_same_race_twice(self):
        """
        Scenario: Same driver tries to enter the same race twice.
        Modules: race_management
        Expected: ValueError citing 'already entered' (not 'unavailable').
        """
        driver = _make_driver("Kim")
        inventory.add_item("cars", "SpeedX", 1)
        race = race_management.create_race("DoubleRace", "Bridge")
        race_management.enter_race(race["id"], driver["id"], "SpeedX")
        with pytest.raises(ValueError, match="already entered"):
            race_management.enter_race(race["id"], driver["id"], "SpeedX")


# ─────────────────────────────────────────────────────────────────────────────
# 3. Race Management <-> Results <-> Inventory (cash)
# ─────────────────────────────────────────────────────────────────────────────

class TestRaceResultsInventoryIntegration:
    """
    Why: Completing a race must distribute prize money and update inventory.
    This is the core financial loop of the system.
    """

    def test_prize_money_added_to_inventory_on_completion(self):
        """
        Scenario: Complete a race with a $1000 prize pool.
        Modules: results -> inventory.add_cash
        Expected: Balance increases by sum of payouts (1st=100%, 2nd=50%).
        """
        race, d1, d2 = _full_race_setup()
        initial_cash = inventory.get_cash_balance()
        results.record_result(race["id"], [d1["id"], d2["id"]], 1000.0)
        expected = round(initial_cash + 1000.0 + 500.0, 2)
        assert inventory.get_cash_balance() == expected

    def test_drivers_freed_after_race_completion(self):
        """
        Scenario: After race completes, all drivers should be available again.
        Modules: results -> crew_management.set_availability
        Expected: Both drivers have is_available = True.
        """
        race, d1, d2 = _full_race_setup("Leo", "Mia", "LC1", "MC1", "FreeRace")
        results.record_result(race["id"], [d1["id"], d2["id"]], 500.0)
        assert registration.get_member(d1["id"])["is_available"]
        assert registration.get_member(d2["id"])["is_available"]

    def test_race_marked_completed_after_result(self):
        """
        Scenario: Record result; verify race status changes to 'completed'.
        Modules: results -> race_management (status update)
        Expected: Race status == 'completed'.
        """
        race, d1, d2 = _full_race_setup("Ned", "Ola", "NC1", "OC1", "StatusRace")
        results.record_result(race["id"], [d1["id"], d2["id"]], 0.0)
        assert race_management.get_race(race["id"])["status"] == "completed"

    def test_cannot_record_result_for_non_in_progress_race(self):
        """
        Scenario: Try to record result on a scheduled (not started) race.
        Modules: results -> race_management
        Expected: ValueError — race must be in_progress first.
        """
        d1 = _make_driver("Nina")
        inventory.add_item("cars", "ZoomCar", 1)
        race = race_management.create_race("BadRace", "Alley")
        race_management.enter_race(race["id"], d1["id"], "ZoomCar")
        with pytest.raises(ValueError, match="not in_progress"):
            results.record_result(race["id"], [d1["id"]], 100.0)

    def test_non_entered_driver_in_finishing_order_rejected(self):
        """
        Scenario: Finishing order includes a member not entered in the race.
        Modules: results
        Expected: ValueError.
        """
        race, d1, d2 = _full_race_setup("Pam", "Quinn", "PC1", "QC1", "BadFinish")
        outsider = _make_driver("Oscar")
        with pytest.raises(ValueError):
            results.record_result(race["id"], [d1["id"], outsider["id"]], 500.0)

    def test_zero_prize_pool_completes_without_cash_change(self):
        """
        Scenario: Race with $0 prize pool.
        Modules: results -> inventory
        Expected: Cash balance unchanged after race.
        """
        race, d1, d2 = _full_race_setup("Rex", "Sue", "RC1", "SC1", "FreeRace2")
        initial = inventory.get_cash_balance()
        results.record_result(race["id"], [d1["id"], d2["id"]], 0.0)
        assert inventory.get_cash_balance() == initial


# ─────────────────────────────────────────────────────────────────────────────
# 4. Results <-> Leaderboard
# ─────────────────────────────────────────────────────────────────────────────

class TestResultsLeaderboardIntegration:
    """
    Why: Leaderboard must reflect cumulative race performance across
    multiple races. Updated automatically by results.record_result.
    """

    def _run_race(self, name, d1, d2, car1, car2, prize=500.0):
        inventory.add_item("cars", car1, 1)
        inventory.add_item("cars", car2, 1)
        race = race_management.create_race(name, "Track")
        race_management.enter_race(race["id"], d1["id"], car1)
        race_management.enter_race(race["id"], d2["id"], car2)
        race_management.start_race(race["id"])
        results.record_result(race["id"], [d1["id"], d2["id"]], prize)

    def test_winner_gets_win_on_leaderboard(self):
        """
        Scenario: Run one race; winner should have 1 win on leaderboard.
        Modules: results -> leaderboard.update_leaderboard
        Expected: Winner's wins == 1, podiums == 1.
        """
        d1 = _make_driver("Tara")
        d2 = _make_driver("Uma")
        self._run_race("Race1", d1, d2, "T1", "U1")
        stats = leaderboard.get_driver_stats(d1["id"])
        assert stats["wins"] == 1
        assert stats["podiums"] == 1

    def test_runner_up_gets_podium_not_win(self):
        """
        Scenario: Runner-up should have 0 wins but 1 podium.
        Modules: results -> leaderboard
        Expected: 2nd place wins == 0, podiums == 1.
        """
        d1 = _make_driver("Vera")
        d2 = _make_driver("Wade")
        self._run_race("Race2", d1, d2, "V1", "W1")
        stats = leaderboard.get_driver_stats(d2["id"])
        assert stats["wins"] == 0
        assert stats["podiums"] == 1

    def test_leaderboard_sorted_by_wins(self):
        """
        Scenario: One driver wins two races; should rank first on leaderboard.
        Modules: results -> leaderboard.get_leaderboard
        Expected: Driver with 2 wins ranked above driver with 0 wins.
        """
        d1 = _make_driver("Xena")
        d2 = _make_driver("Yuto")
        self._run_race("WinTest1", d1, d2, "X1", "Y1")
        self._run_race("WinTest2", d1, d2, "X2", "Y2")
        board = leaderboard.get_leaderboard()
        assert board[0]["member_id"] == d1["id"]
        assert board[0]["wins"] == 2

    def test_earnings_accumulate_across_races(self):
        """
        Scenario: Same driver wins two races with different prize pools.
        Modules: results -> leaderboard
        Expected: total_earnings equals sum of both 1st-place shares.
        """
        d1 = _make_driver("Zara")
        d2 = _make_driver("Aaron")
        self._run_race("EarnR1", d1, d2, "Z1", "A1", prize=1000.0)
        self._run_race("EarnR2", d1, d2, "Z2", "A2", prize=2000.0)
        stats = leaderboard.get_driver_stats(d1["id"])
        assert stats["total_earnings"] == 1000.0 + 2000.0


# ─────────────────────────────────────────────────────────────────────────────
# 5. Mission Planning <-> Crew Management
# ─────────────────────────────────────────────────────────────────────────────

class TestMissionCrewIntegration:
    """
    Why: Missions must validate role availability before starting and must
    lock/free crew members correctly.
    """

    def test_successful_mission_creation(self):
        """
        Scenario: Assign a delivery mission to an available driver.
        Modules: mission_planning -> crew_management.get_available_by_role
        Expected: Mission created with status 'active'.
        """
        driver = _make_driver("Boris")
        m = mission_planning.create_mission("delivery", "Drop package", [driver["id"]])
        assert m["status"] == "active"

    def test_driver_unavailable_during_mission(self):
        """
        Scenario: Start a mission with a driver; driver should be locked.
        Modules: mission_planning -> crew_management.set_availability
        Expected: Driver's is_available = False during mission.
        """
        driver = _make_driver("Cora")
        mission_planning.create_mission("delivery", "Courier run", [driver["id"]])
        assert not registration.get_member(driver["id"])["is_available"]

    def test_mission_requires_correct_role(self):
        """
        Scenario: Assign a rescue mission without a medic.
        Modules: mission_planning
        Expected: ValueError — medic role is missing from assigned members.
        """
        driver = _make_driver("Drew")
        with pytest.raises(ValueError, match="requires roles"):
            mission_planning.create_mission("rescue", "Extract target", [driver["id"]])

    def test_mission_with_all_required_roles(self):
        """
        Scenario: Assign rescue mission with both a driver and a medic.
        Modules: registration -> mission_planning
        Expected: Mission starts successfully.
        """
        driver = _make_driver("Elsa")
        medic = registration.register_member("Fred", "medic")
        m = mission_planning.create_mission(
            "rescue", "Save the crew", [driver["id"], medic["id"]]
        )
        assert m["status"] == "active"

    def test_crew_freed_after_mission_completion(self):
        """
        Scenario: Complete a mission; all assigned members become available.
        Modules: mission_planning -> crew_management.set_availability
        Expected: Driver is_available = True after mission completes.
        """
        driver = _make_driver("Gail")
        m = mission_planning.create_mission("delivery", "Quick drop", [driver["id"]])
        mission_planning.complete_mission(m["id"])
        assert registration.get_member(driver["id"])["is_available"]

    def test_unavailable_member_cannot_be_assigned(self):
        """
        Scenario: Driver already in a race; try to assign to a mission too.
        Modules: race_management -> mission_planning
        Expected: ValueError — member is not available.
        """
        driver = _make_driver("Hugo")
        inventory.add_item("cars", "BusyCar", 1)
        race = race_management.create_race("BusyRace", "Uptown")
        race_management.enter_race(race["id"], driver["id"], "BusyCar")
        with pytest.raises(ValueError, match="unavailable"):
            mission_planning.create_mission("delivery", "Parallel job", [driver["id"]])

    def test_check_roles_available_returns_false_when_all_busy(self):
        """
        Scenario: Only mechanic is in a mission; role check returns False.
        Modules: mission_planning -> crew_management.get_available_by_role
        Expected: check_roles_available('repair') == False.
        """
        mech = _make_mechanic("Iris2")
        mission_planning.create_mission("repair", "Fix engine", [mech["id"]])
        assert not mission_planning.check_roles_available("repair")

    def test_failed_mission_also_frees_crew(self):
        """
        Scenario: Mark a mission as failed; crew should still be freed.
        Modules: mission_planning -> crew_management
        Expected: Driver available, mission status == 'failed'.
        """
        driver = _make_driver("Jana")
        m = mission_planning.create_mission("delivery", "Risky drop", [driver["id"]])
        mission_planning.complete_mission(m["id"], success=False)
        assert registration.get_member(driver["id"])["is_available"]
        assert mission_planning.get_mission(m["id"])["status"] == "failed"


# ─────────────────────────────────────────────────────────────────────────────
# 6. Vehicle Condition <-> Inventory
# ─────────────────────────────────────────────────────────────────────────────

class TestVehicleConditionInventoryIntegration:
    """
    Why: vehicle_condition is the source of truth for car health.
    It must stay in sync with the inventory car records.
    """

    def test_register_car_condition_syncs_inventory(self):
        """
        Scenario: Add a car to inventory, register its condition.
        Modules: inventory.add_item -> vehicle_condition.register_car_condition
        Expected: inventory car condition matches registered condition.
        """
        inventory.add_item("cars", "Alpha", 1, condition="good")
        vehicle_condition.register_car_condition("Alpha", "good")
        inv_car = inventory.get_item("cars", "Alpha")
        vc = vehicle_condition.get_condition("Alpha")
        assert inv_car["condition"] == "good"
        assert vc["condition"] == "good"

    def test_apply_damage_degrades_condition(self):
        """
        Scenario: Car starts 'good'; apply 2 levels of damage.
        Modules: vehicle_condition.apply_damage -> inventory.set_car_condition
        Expected: Condition drops to 'worn' (good -> worn is 2 steps back: good->worn->damaged).
        """
        inventory.add_item("cars", "Beta", 1, condition="good")
        vehicle_condition.register_car_condition("Beta", "good")
        rec = vehicle_condition.apply_damage("Beta", severity=2)
        # good(4) - 2 = damaged(2)
        assert rec["condition"] == "damaged"
        assert inventory.get_item("cars", "Beta")["condition"] == "damaged"

    def test_apply_damage_grounds_car(self):
        """
        Scenario: Apply enough damage to ground a car (below 'good').
        Modules: vehicle_condition
        Expected: is_grounded = True when condition not in RACE_ELIGIBLE_CONDITIONS.
        """
        inventory.add_item("cars", "Gamma", 1, condition="good")
        vehicle_condition.register_car_condition("Gamma", "good")
        rec = vehicle_condition.apply_damage("Gamma", severity=1)
        # good -> worn
        assert rec["is_grounded"] is True

    def test_totaled_car_cannot_take_more_damage(self):
        """
        Scenario: Car already totaled; try to apply more damage.
        Modules: vehicle_condition
        Expected: ValueError — cannot damage a totaled car.
        """
        inventory.add_item("cars", "Delta", 1, condition="totaled")
        vehicle_condition.register_car_condition("Delta", "totaled")
        with pytest.raises(ValueError, match="already totaled"):
            vehicle_condition.apply_damage("Delta", severity=1)

    def test_car_without_condition_record_raises_keyerror(self):
        """
        Scenario: Call apply_damage on a car with no condition record.
        Modules: vehicle_condition
        Expected: KeyError.
        """
        inventory.add_item("cars", "Ghost", 1)
        with pytest.raises(KeyError):
            vehicle_condition.apply_damage("Ghost", severity=1)

    def test_is_race_eligible_reflects_condition(self):
        """
        Scenario: Car starts 'good' (eligible); damaged to 'worn' (not eligible).
        Modules: vehicle_condition.is_race_eligible
        Expected: True before damage, False after.
        """
        inventory.add_item("cars", "Epsilon", 1, condition="good")
        vehicle_condition.register_car_condition("Epsilon", "good")
        assert vehicle_condition.is_race_eligible("Epsilon") is True
        vehicle_condition.apply_damage("Epsilon", severity=1)
        assert vehicle_condition.is_race_eligible("Epsilon") is False


# ─────────────────────────────────────────────────────────────────────────────
# 7. Vehicle Condition <-> Crew Management (mechanic locking)
# ─────────────────────────────────────────────────────────────────────────────

class TestVehicleConditionCrewIntegration:
    """
    Why: Repairs require a mechanic. The mechanic must be locked during
    repair and freed once the repair completes.
    """

    def test_start_repair_locks_mechanic(self):
        """
        Scenario: Start a repair; mechanic should become unavailable.
        Modules: vehicle_condition.start_repair -> crew_management.set_availability
        Expected: Mechanic is_available = False during repair.
        """
        mech = _make_mechanic("Karl")
        inventory.add_item("cars", "Zeta", 1, condition="damaged")
        vehicle_condition.register_car_condition("Zeta", "damaged")
        vehicle_condition.start_repair("Zeta", mech["id"])
        assert not registration.get_member(mech["id"])["is_available"]

    def test_complete_repair_frees_mechanic(self):
        """
        Scenario: Complete repair; mechanic should be available again.
        Modules: vehicle_condition.complete_repair -> crew_management.set_availability
        Expected: Mechanic is_available = True, car condition improved.
        """
        mech = _make_mechanic("Lena2")
        inventory.add_item("cars", "Eta", 1, condition="damaged")
        vehicle_condition.register_car_condition("Eta", "damaged")
        vehicle_condition.start_repair("Eta", mech["id"])
        rec = vehicle_condition.complete_repair("Eta")
        assert registration.get_member(mech["id"])["is_available"]
        assert rec["condition"] == "worn"   # damaged -> worn (one level up)

    def test_repair_improves_condition_by_one_level(self):
        """
        Scenario: Car is 'critical'; complete one repair.
        Modules: vehicle_condition
        Expected: Condition improves from 'critical' to 'damaged'.
        """
        mech = _make_mechanic("Marc")
        inventory.add_item("cars", "Theta", 1, condition="critical")
        vehicle_condition.register_car_condition("Theta", "critical")
        vehicle_condition.start_repair("Theta", mech["id"])
        rec = vehicle_condition.complete_repair("Theta")
        assert rec["condition"] == "damaged"

    def test_non_mechanic_cannot_start_repair(self):
        """
        Scenario: Assign a driver as the repairer.
        Modules: vehicle_condition -> crew_management (role check)
        Expected: ValueError — must be a mechanic.
        """
        driver = _make_driver("Nora")
        inventory.add_item("cars", "Iota", 1, condition="damaged")
        vehicle_condition.register_car_condition("Iota", "damaged")
        with pytest.raises(ValueError, match="not a mechanic"):
            vehicle_condition.start_repair("Iota", driver["id"])

    def test_unavailable_mechanic_cannot_start_repair(self):
        """
        Scenario: Mechanic is in a mission; try to assign to repair.
        Modules: mission_planning -> vehicle_condition
        Expected: ValueError — mechanic is unavailable.
        """
        mech = _make_mechanic("Ollie")
        mission_planning.create_mission("repair", "Other job", [mech["id"]])
        inventory.add_item("cars", "Kappa", 1, condition="worn")
        vehicle_condition.register_car_condition("Kappa", "worn")
        with pytest.raises(ValueError, match="unavailable"):
            vehicle_condition.start_repair("Kappa", mech["id"])

    def test_totaled_car_cannot_be_repaired(self):
        """
        Scenario: Car is totaled; attempt to start a repair.
        Modules: vehicle_condition
        Expected: ValueError — totaled cars cannot be repaired.
        """
        mech = _make_mechanic("Pete2")
        inventory.add_item("cars", "Lambda", 1, condition="totaled")
        vehicle_condition.register_car_condition("Lambda", "totaled")
        with pytest.raises(ValueError, match="totaled"):
            vehicle_condition.start_repair("Lambda", mech["id"])

    def test_full_service_restores_to_excellent(self):
        """
        Scenario: Perform a full service on a damaged car.
        Modules: vehicle_condition.full_service -> inventory + crew_management
        Expected: Car condition jumps to 'excellent'; mechanic freed immediately.
        """
        mech = _make_mechanic("Quinn2")
        inventory.add_item("cars", "Mu", 1, condition="damaged")
        vehicle_condition.register_car_condition("Mu", "damaged")
        rec = vehicle_condition.full_service("Mu", mech["id"])
        assert rec["condition"] == "excellent"
        assert registration.get_member(mech["id"])["is_available"]
        assert inventory.get_item("cars", "Mu")["condition"] == "excellent"

    def test_double_repair_raises_error(self):
        """
        Scenario: Start a repair, then try to start another on the same car.
        Modules: vehicle_condition
        Expected: ValueError — repair already in progress.
        """
        mech1 = _make_mechanic("Rosa2")
        mech2 = _make_mechanic("Seth2")
        inventory.add_item("cars", "Nu", 1, condition="damaged")
        vehicle_condition.register_car_condition("Nu", "damaged")
        vehicle_condition.start_repair("Nu", mech1["id"])
        with pytest.raises(ValueError, match="already has a repair"):
            vehicle_condition.start_repair("Nu", mech2["id"])


# ─────────────────────────────────────────────────────────────────────────────
# 8. End-to-End Scenarios (all modules together)
# ─────────────────────────────────────────────────────────────────────────────

class TestEndToEndScenarios:
    """
    Why: Verify complete workflows spanning all 8 modules simultaneously.
    These simulate realistic usage patterns of the full system.
    """

    def test_full_race_lifecycle_with_damage_and_repair(self):
        """
        Scenario: Full workflow — register, race, damage car, repair.
        Modules: ALL
        Expected: Leaderboard updated; cash correct; damaged car repaired.
        """
        # Register crew
        d1 = registration.register_member("Leo", "driver")
        d2 = registration.register_member("Mia", "driver")
        mech = registration.register_member("Nick", "mechanic")
        crew_management.set_skill_level(d1["id"], 8)

        # Inventory + condition
        inventory.add_item("cars", "NightRider", 1, condition="good")
        inventory.add_item("cars", "DayRunner", 1, condition="good")
        vehicle_condition.register_car_condition("NightRider", "good")
        vehicle_condition.register_car_condition("DayRunner", "good")
        initial_cash = inventory.get_cash_balance()

        # Race
        race = race_management.create_race("GrandFinal", "Main Circuit")
        race_management.enter_race(race["id"], d1["id"], "NightRider")
        race_management.enter_race(race["id"], d2["id"], "DayRunner")
        race_management.start_race(race["id"])

        # Result with car damage
        result = results.record_result(
            race["id"],
            finishing_order=[d1["id"], d2["id"]],
            prize_pool=2000.0,
            car_damage={d2["id"]: "damaged"},
        )

        # Check cash
        assert result["payouts"][d1["id"]] == 2000.0
        assert result["payouts"][d2["id"]] == 1000.0
        assert inventory.get_cash_balance() == round(initial_cash + 3000.0, 2)

        # Apply damage via vehicle_condition to keep vc in sync
        vehicle_condition.apply_damage("DayRunner", severity=2)
        assert not vehicle_condition.is_race_eligible("DayRunner")

        # Repair
        vehicle_condition.start_repair("DayRunner", mech["id"])
        assert not registration.get_member(mech["id"])["is_available"]
        vehicle_condition.complete_repair("DayRunner")
        assert registration.get_member(mech["id"])["is_available"]

        # Leaderboard
        board = leaderboard.get_leaderboard()
        assert board[0]["name"] == "Leo"

    def test_race_cancel_frees_drivers(self):
        """
        Scenario: Cancel a race after entering drivers.
        Modules: registration -> race_management.cancel_race -> crew_management
        Expected: Drivers available after cancellation.
        """
        d1 = _make_driver("Ned2")
        inventory.add_item("cars", "CancelCar", 1)
        race = race_management.create_race("CancelledRace", "Outskirts")
        race_management.enter_race(race["id"], d1["id"], "CancelCar")
        assert not registration.get_member(d1["id"])["is_available"]
        race_management.cancel_race(race["id"])
        assert registration.get_member(d1["id"])["is_available"]

    def test_damaged_car_triggers_repair_mission(self):
        """
        Scenario: Race ends with car damage; repair mission assigned.
        Modules: results -> vehicle_condition -> mission_planning -> crew_management
        Expected: Repair mission active only if mechanic is available.
        """
        d1 = _make_driver("Olga")
        d2 = _make_driver("Pete3")
        mech = _make_mechanic("Rita")
        inventory.add_item("cars", "FragileCar", 1, condition="good")
        inventory.add_item("cars", "SolidCar", 1, condition="good")
        vehicle_condition.register_car_condition("FragileCar", "good")
        vehicle_condition.register_car_condition("SolidCar", "good")

        race = race_management.create_race("RiskyRace", "Industrial Zone")
        race_management.enter_race(race["id"], d1["id"], "FragileCar")
        race_management.enter_race(race["id"], d2["id"], "SolidCar")
        race_management.start_race(race["id"])
        results.record_result(
            race["id"], [d1["id"], d2["id"]], prize_pool=0.0,
            car_damage={d1["id"]: "damaged"},
        )

        # Sync damage into vehicle_condition
        vehicle_condition.apply_damage("FragileCar", severity=2)

        # Mechanic is available → repair mission should succeed
        assert mission_planning.check_roles_available("repair")
        m = mission_planning.create_mission("repair", "Fix FragileCar", [mech["id"]])
        assert m["status"] == "active"

    def test_grounded_car_condition_log_records_events(self):
        """
        Scenario: Damage a car then repair it; log should contain all events.
        Modules: vehicle_condition (damage + repair)
        Expected: Log contains 'registered', 'damage', 'repair_started', 'repair_completed'.
        """
        mech = _make_mechanic("Uma2")
        inventory.add_item("cars", "LogCar", 1, condition="good")
        vehicle_condition.register_car_condition("LogCar", "good")
        vehicle_condition.apply_damage("LogCar", severity=1)
        vehicle_condition.start_repair("LogCar", mech["id"])
        vehicle_condition.complete_repair("LogCar")

        log = vehicle_condition.get_condition_log("LogCar")
        event_types = [entry["event"] for entry in log]
        assert "registered" in event_types
        assert "damage" in event_types
        assert "repair_started" in event_types
        assert "repair_completed" in event_types


# ─────────────────────────────────────────────────────────────────────────────
# 9. Race Entry Fee <-> Inventory (cash deduction)
# ─────────────────────────────────────────────────────────────────────────────

class TestRaceEntryFeeInventoryIntegration:
    """
    Why: Races with an entry fee must deduct from the cash balance when a
    driver enters. This validates the financial link between race_management
    and inventory that is separate from prize payouts.
    """

    def test_entry_fee_deducted_from_balance_on_race_entry(self):
        """
        Scenario: Create a race with a $500 entry fee; enter one driver.
        Modules: race_management -> inventory.deduct_cash
        Expected: Cash balance decreases by $500.
        """
        driver = _make_driver("Sven")
        inventory.add_item("cars", "SvenCar", 1)
        race = race_management.create_race("FeeRace", "Docks", entry_fee=500.0)
        initial_cash = inventory.get_cash_balance()
        race_management.enter_race(race["id"], driver["id"], "SvenCar")
        assert inventory.get_cash_balance() == round(initial_cash - 500.0, 2)

    def test_multiple_drivers_each_pay_entry_fee(self):
        """
        Scenario: Two drivers enter the same race with a $200 entry fee.
        Modules: race_management -> inventory.deduct_cash (x2)
        Expected: Cash balance decreases by $400 total.
        """
        d1 = _make_driver("Tilda")
        d2 = _make_driver("Ulrich")
        inventory.add_item("cars", "TC1", 1)
        inventory.add_item("cars", "UC1", 1)
        race = race_management.create_race("DoubleFeeRace", "Harbour", entry_fee=200.0)
        initial_cash = inventory.get_cash_balance()
        race_management.enter_race(race["id"], d1["id"], "TC1")
        race_management.enter_race(race["id"], d2["id"], "UC1")
        assert inventory.get_cash_balance() == round(initial_cash - 400.0, 2)

    def test_zero_entry_fee_does_not_change_balance(self):
        """
        Scenario: Race with no entry fee; entering should not touch the balance.
        Modules: race_management -> inventory
        Expected: Cash balance unchanged after entry.
        """
        driver = _make_driver("Viola")
        inventory.add_item("cars", "VCar", 1)
        race = race_management.create_race("FreeEntryRace", "Suburbs", entry_fee=0.0)
        initial_cash = inventory.get_cash_balance()
        race_management.enter_race(race["id"], driver["id"], "VCar")
        assert inventory.get_cash_balance() == initial_cash

    def test_insufficient_funds_blocks_race_entry(self):
        """
        Scenario: Drain the cash balance, then attempt to enter a race with a fee.
        Modules: inventory.deduct_cash -> race_management
        Expected: ValueError — not enough funds to pay the entry fee.
        """
        driver = _make_driver("Walt")
        inventory.add_item("cars", "WCar", 1)
        # Drain most of the balance
        current = inventory.get_cash_balance()
        inventory.deduct_cash(current - 50.0)
        race = race_management.create_race("ExpensiveRace", "Uphill", entry_fee=500.0)
        with pytest.raises(ValueError, match="Insufficient"):
            race_management.enter_race(race["id"], driver["id"], "WCar")


# ─────────────────────────────────────────────────────────────────────────────
# 10. Driver Re-entry After Race Completion
# ─────────────────────────────────────────────────────────────────────────────

class TestDriverReentryAfterRace:
    """
    Why: Once a race completes, all drivers must be freed so they can enter
    subsequent races. This confirms the availability cycle works end-to-end
    across two consecutive race lifecycles.
    """

    def test_driver_can_enter_second_race_after_first_completes(self):
        """
        Scenario: Driver completes race 1; enters and races in race 2.
        Modules: results -> crew_management -> race_management
        Expected: Driver successfully enters race 2 with no availability error.
        """
        driver = _make_driver("Xavier")
        inventory.add_item("cars", "XCar1", 1)
        inventory.add_item("cars", "XCar2", 1)

        race1 = race_management.create_race("Race1X", "North Loop")
        race_management.enter_race(race1["id"], driver["id"], "XCar1")
        race_management.start_race(race1["id"])
        results.record_result(race1["id"], [driver["id"]], prize_pool=0.0)

        assert registration.get_member(driver["id"])["is_available"]

        race2 = race_management.create_race("Race2X", "South Loop")
        updated = race_management.enter_race(race2["id"], driver["id"], "XCar2")
        assert driver["id"] in updated["drivers"]

    def test_driver_locked_in_race1_cannot_enter_race2(self):
        """
        Scenario: Driver is in an active race; try to enter a second race.
        Modules: race_management (availability check)
        Expected: ValueError — driver is unavailable.
        """
        driver = _make_driver("Yuki")
        inventory.add_item("cars", "YCar1", 1)
        inventory.add_item("cars", "YCar2", 1)

        race1 = race_management.create_race("ActiveRace1", "East Side")
        race_management.enter_race(race1["id"], driver["id"], "YCar1")

        race2 = race_management.create_race("ActiveRace2", "West Side")
        with pytest.raises(ValueError, match="unavailable"):
            race_management.enter_race(race2["id"], driver["id"], "YCar2")


# ─────────────────────────────────────────────────────────────────────────────
# 11. Three-Driver Podium — Earnings and Leaderboard
# ─────────────────────────────────────────────────────────────────────────────

class TestThreeDriverPodium:
    """
    Why: The payout multipliers apply to the top 3 places. With only two drivers
    most tests never exercise 3rd-place logic. These cases confirm the full
    podium — 1st (100%), 2nd (50%), 3rd (25%) — is handled correctly in both
    inventory cash and leaderboard stats.
    """

    def _setup_three_driver_race(self, race_name):
        d1 = _make_driver("Anya")
        d2 = _make_driver("Bruno")
        d3 = _make_driver("Cara")
        for car, drv in [("AC1", d1), ("BC1", d2), ("CC1", d3)]:
            inventory.add_item("cars", car, 1)
        race = race_management.create_race(race_name, "Grand Circuit")
        race_management.enter_race(race["id"], d1["id"], "AC1")
        race_management.enter_race(race["id"], d2["id"], "BC1")
        race_management.enter_race(race["id"], d3["id"], "CC1")
        race_management.start_race(race["id"])
        return race, d1, d2, d3

    def test_third_place_receives_correct_payout(self):
        """
        Scenario: Three-driver race with a $1000 prize pool.
        Modules: results -> inventory
        Expected: 3rd-place driver earns $250 (25% of pool).
        """
        race, d1, d2, d3 = self._setup_three_driver_race("PodiumRace1")
        result = results.record_result(
            race["id"], [d1["id"], d2["id"], d3["id"]], prize_pool=1000.0
        )
        assert result["payouts"][d3["id"]] == 250.0

    def test_third_place_gets_podium_on_leaderboard(self):
        """
        Scenario: Three-driver race; 3rd-place driver should have a podium entry.
        Modules: results -> leaderboard
        Expected: 3rd driver podiums == 1, wins == 0.
        """
        race, d1, d2, d3 = self._setup_three_driver_race("PodiumRace2")
        results.record_result(
            race["id"], [d1["id"], d2["id"], d3["id"]], prize_pool=600.0
        )
        stats = leaderboard.get_driver_stats(d3["id"])
        assert stats["podiums"] == 1
        assert stats["wins"] == 0

    def test_fourth_place_receives_no_payout(self):
        """
        Scenario: Four drivers; 4th place finisher gets no prize money.
        Modules: results -> inventory
        Expected: 4th-place driver absent from payouts dict.
        """
        d4 = _make_driver("Dave")
        inventory.add_item("cars", "DC1", 1)

        race, d1, d2, d3 = self._setup_three_driver_race("PodiumRace3")
        # Manually add d4 into the already-created race
        races = race_management.get_all_races()
        race_id = race["id"]
        race_management.enter_race(race_id, d4["id"], "DC1")

        result = results.record_result(
            race_id,
            [d1["id"], d2["id"], d3["id"], d4["id"]],
            prize_pool=1000.0,
        )
        assert d4["id"] not in result["payouts"]

    def test_total_cash_added_equals_sum_of_all_payouts(self):
        """
        Scenario: Three-driver race; verify total cash added = 1st + 2nd + 3rd payouts.
        Modules: results -> inventory
        Expected: Balance delta == 1000 + 500 + 250 == 1750.
        """
        race, d1, d2, d3 = self._setup_three_driver_race("PodiumRace4")
        initial = inventory.get_cash_balance()
        results.record_result(
            race["id"], [d1["id"], d2["id"], d3["id"]], prize_pool=1000.0
        )
        assert inventory.get_cash_balance() == round(initial + 1750.0, 2)


# ─────────────────────────────────────────────────────────────────────────────
# 12. Leaderboard Edge Cases
# ─────────────────────────────────────────────────────────────────────────────

class TestLeaderboardEdgeCases:
    """
    Why: The leaderboard is queried externally and must handle drivers who
    have never raced as well as ties in wins broken by podiums and earnings.
    """

    def test_stats_for_never_raced_driver_raises_keyerror(self):
        """
        Scenario: Call get_driver_stats on a registered driver with no race history.
        Modules: leaderboard
        Expected: KeyError — no entry exists yet for this driver.
        """
        driver = _make_driver("Zoe")
        with pytest.raises(KeyError):
            leaderboard.get_driver_stats(driver["id"])

    def test_leaderboard_tiebreak_by_podiums(self):
        """
        Scenario: Two drivers with equal wins; the one with more podiums ranks higher.
        Modules: results -> leaderboard.get_leaderboard
        Expected: Driver with more podiums appears first.
        """
        d1 = _make_driver("Finn")
        d2 = _make_driver("Greta")
        d3 = _make_driver("Hans")

        # Race 1: d1 wins, d2 second
        for car in ["F1", "G1", "H1"]:
            inventory.add_item("cars", car, 1)
        r1 = race_management.create_race("TieRace1", "Loop A")
        race_management.enter_race(r1["id"], d1["id"], "F1")
        race_management.enter_race(r1["id"], d2["id"], "G1")
        race_management.start_race(r1["id"])
        results.record_result(r1["id"], [d1["id"], d2["id"]], prize_pool=0.0)

        # Race 2: d2 wins, d3 second — d1 sits this one out
        for car in ["G2", "H2"]:
            inventory.add_item("cars", car, 1)
        r2 = race_management.create_race("TieRace2", "Loop B")
        race_management.enter_race(r2["id"], d2["id"], "G2")
        race_management.enter_race(r2["id"], d3["id"], "H2")
        race_management.start_race(r2["id"])
        results.record_result(r2["id"], [d2["id"], d3["id"]], prize_pool=0.0)

        # d1: 1 win, 1 podium  |  d2: 1 win, 2 podiums
        board = leaderboard.get_leaderboard()
        ids_in_order = [e["member_id"] for e in board]
        assert ids_in_order.index(d2["id"]) < ids_in_order.index(d1["id"])

    def test_reset_leaderboard_clears_all_entries(self):
        """
        Scenario: Run a race, reset the leaderboard, check it is empty.
        Modules: leaderboard.reset_leaderboard
        Expected: get_leaderboard() returns an empty list after reset.
        """
        race, d1, d2 = _full_race_setup("ResetRace", "D1r", "C1r", "C2r")
        results.record_result(race["id"], [d1["id"], d2["id"]], prize_pool=100.0)
        leaderboard.reset_leaderboard()
        assert leaderboard.get_leaderboard() == []


# ─────────────────────────────────────────────────────────────────────────────
# 13. Mission Completion Unlocks Follow-on Actions
# ─────────────────────────────────────────────────────────────────────────────

class TestMissionCompletionFollowOn:
    """
    Why: After a mission ends, the freed crew should be immediately usable
    for races or other missions. These tests confirm the state machine
    resets correctly and the system does not leave stale locks behind.
    """

    def test_driver_can_race_after_mission_completes(self):
        """
        Scenario: Driver finishes a delivery mission then enters a race.
        Modules: mission_planning -> crew_management -> race_management
        Expected: Driver successfully enters race after mission is completed.
        """
        driver = _make_driver("Isla")
        m = mission_planning.create_mission("delivery", "Quick run", [driver["id"]])
        mission_planning.complete_mission(m["id"])

        inventory.add_item("cars", "IslaRacer", 1)
        race = race_management.create_race("PostMissionRace", "Highway")
        updated = race_management.enter_race(race["id"], driver["id"], "IslaRacer")
        assert driver["id"] in updated["drivers"]

    def test_same_member_can_run_sequential_missions(self):
        """
        Scenario: Driver completes mission 1, then immediately starts mission 2.
        Modules: mission_planning -> crew_management -> mission_planning
        Expected: Second mission created with status 'active'.
        """
        driver = _make_driver("Jett")
        m1 = mission_planning.create_mission("delivery", "First drop", [driver["id"]])
        mission_planning.complete_mission(m1["id"])

        m2 = mission_planning.create_mission("delivery", "Second drop", [driver["id"]])
        assert m2["status"] == "active"
        assert not registration.get_member(driver["id"])["is_available"]

    def test_completing_already_completed_mission_raises_error(self):
        """
        Scenario: Attempt to complete a mission that is already marked completed.
        Modules: mission_planning
        Expected: ValueError — mission is not 'active'.
        """
        driver = _make_driver("Kira")
        m = mission_planning.create_mission("delivery", "One-time job", [driver["id"]])
        mission_planning.complete_mission(m["id"])
        with pytest.raises(ValueError, match="not 'active'"):
            mission_planning.complete_mission(m["id"])


# ─────────────────────────────────────────────────────────────────────────────
# 14. Race Result Car Damage Syncs to Inventory
# ─────────────────────────────────────────────────────────────────────────────

class TestResultCarDamageSyncsInventory:
    """
    Why: When record_result receives a car_damage dict, it calls
    inventory.set_car_condition. This test class specifically validates that
    the inventory record is updated through the results module — a different
    path from vehicle_condition.apply_damage.
    """

    def test_car_condition_in_inventory_updated_via_result(self):
        """
        Scenario: Race ends; winner's car recorded as 'damaged' in car_damage.
        Modules: results -> inventory.set_car_condition
        Expected: inventory car record shows 'damaged' condition.
        """
        race, d1, d2 = _full_race_setup("DamageSync1", "DS1", "DSC1", "DSC2")
        results.record_result(
            race["id"],
            [d1["id"], d2["id"]],
            prize_pool=0.0,
            car_damage={d1["id"]: "damaged"},
        )
        car_in_inv = inventory.get_item("cars", "DSC1")
        assert car_in_inv["condition"] == "damaged"

    def test_undamaged_cars_keep_original_condition(self):
        """
        Scenario: Race ends; only one car is listed in car_damage.
        Modules: results -> inventory
        Expected: The car NOT in car_damage retains its original condition.
        """
        inventory.add_item("cars", "CleanA", 1, condition="good")
        inventory.add_item("cars", "CleanB", 1, condition="good")
        d1 = _make_driver("Liam")
        d2 = _make_driver("Maya")
        race = race_management.create_race("PartialDamage", "Track Z")
        race_management.enter_race(race["id"], d1["id"], "CleanA")
        race_management.enter_race(race["id"], d2["id"], "CleanB")
        race_management.start_race(race["id"])
        results.record_result(
            race["id"],
            [d1["id"], d2["id"]],
            prize_pool=0.0,
            car_damage={d1["id"]: "worn"},
        )
        assert inventory.get_item("cars", "CleanB")["condition"] == "good"
