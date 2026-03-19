from data_store import load, save
from registration import VALID_ROLES

MIN_SKILL = 1
MAX_SKILL = 10

def assign_role(member_id: str, new_role: str) -> dict:
    # Change the role of an existing crew member
    new_role = new_role.strip().lower()
    if new_role not in VALID_ROLES:
        raise ValueError(
            f"Invalid role '{new_role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}."
        )
    members = load("members")
    if member_id not in members:
        raise KeyError(f"No member found with ID '{member_id}'.")
    members[member_id]["role"] = new_role
    save("members", members)
    return members[member_id]


def set_skill_level(member_id: str, skill_level: int) -> dict:
    # Set the skill level of a crew member
    if not isinstance(skill_level, int) or not (MIN_SKILL <= skill_level <= MAX_SKILL):
        raise ValueError(
            f"Skill level must be an integer between {MIN_SKILL} and {MAX_SKILL}."
        )

    members = load("members")
    if member_id not in members:
        raise KeyError(f"No member found with ID '{member_id}'.")
    members[member_id]["skill_level"] = skill_level
    save("members", members)
    return members[member_id]


def set_availability(member_id: str, available: bool) -> dict:
    # Mark a member as available or unavailable
    members = load("members")
    if member_id not in members:
        raise KeyError(f"No member found with ID '{member_id}'.")

    members[member_id]["is_available"] = available
    save("members", members)
    return members[member_id]


def get_available_by_role(role: str) -> list:
    # return all available members with the specified role
    role = role.strip().lower()
    return [
        m for m in load("members").values()
        if m["role"] == role and m["is_available"]
    ]


def get_crew_summary() -> list:
    # Return a summary list of all crew members sorted by name
    members = load("members")
    return sorted(members.values(), key=lambda m: m["name"])