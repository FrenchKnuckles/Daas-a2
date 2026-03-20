import uuid
from data_store import load, save
from crew_management import set_availability, get_available_by_role

MISSION_TYPES = {
    "delivery": {"required_roles": ["driver"]},
    "rescue":   {"required_roles": ["driver", "medic"]},
    "repair":   {"required_roles": ["mechanic"]},
    "recon":    {"required_roles": ["scout"]},
    "strategy": {"required_roles": ["strategist"]},
}
MISSION_STATUSES = {"pending", "active", "completed", "failed"}

def create_mission(
    mission_type: str, description: str,assigned_member_ids: list, ) -> dict:
    # Create and start a mission
    mission_type = mission_type.strip().lower()
    if mission_type not in MISSION_TYPES:
        raise ValueError(
            f"Invalid mission type '{mission_type}'. "
            f"Choose from: {', '.join(sorted(MISSION_TYPES))}."
        )

    description = description.strip()
    if not description:
        raise ValueError("Mission description cannot be empty.")

    if not assigned_member_ids:
        raise ValueError("At least one crew member must be assigned to a mission.")

    # Load members and validate each one
    members_store = load("members")
    assigned_members = []
    for mid in assigned_member_ids:
        if mid not in members_store:
            raise KeyError(f"No member found with ID '{mid}'.")
        member = members_store[mid]
        if not member["is_available"]:
            raise ValueError(
                f"Member '{member['name']}' is currently unavailable."
            )
        assigned_members.append(member)

    # Check required roles are covered
    assigned_roles = {m["role"] for m in assigned_members}
    required_roles = set(MISSION_TYPES[mission_type]["required_roles"])
    missing_roles = required_roles - assigned_roles
    if missing_roles:
        raise ValueError(
            f"Mission '{mission_type}' requires roles: {missing_roles}. "
            "Not covered by assigned members."
        )

    # Mark members as unavailable
    for mid in assigned_member_ids:
        set_availability(mid, False)

    mission_id = str(uuid.uuid4())
    mission = {
        "id":                  mission_id,
        "type":                mission_type,
        "description":         description,
        "assigned_member_ids": assigned_member_ids,
        "status":              "active",
    }

    missions = load("missions")
    missions[mission_id] = mission
    save("missions", missions)
    return mission

def complete_mission(mission_id: str, success: bool = True) -> dict:
    # Mark a mission as completed or failed, and free up all assigned members
    missions = load("missions")
    if mission_id not in missions:
        raise KeyError(f"No mission found with ID '{mission_id}'.")

    mission = missions[mission_id]
    if mission["status"] != "active":
        raise ValueError(
            f"Mission is '{mission['status']}', not 'active'. Cannot complete/fail it."
        )

    mission["status"] = "completed" if success else "failed"
    missions[mission_id] = mission
    save("missions", missions)

    # Free up all assigned members
    for mid in mission["assigned_member_ids"]:
        try:
            set_availability(mid, True)
        except KeyError:
            pass

    return mission

def check_roles_available(mission_type: str) -> bool:
    # Check whether required roles for a given mission type are currently available
    mission_type = mission_type.strip().lower()
    if mission_type not in MISSION_TYPES:
        raise ValueError(f"Invalid mission type '{mission_type}'.")

    required = MISSION_TYPES[mission_type]["required_roles"]
    for role in required:
        if not get_available_by_role(role):
            return False
    return True

def get_mission(mission_id: str) -> dict:
    # Fetch a mission by ID
    missions = load("missions")
    if mission_id not in missions:
        raise KeyError(f"No mission found with ID '{mission_id}'.")
    return missions[mission_id]

def get_all_missions() -> dict:
    # Return all missions
    return load("missions")