import uuid
from data_store import load, save

# Each member gets a unique ID, a name, and an initial role.
VALID_ROLES = {"driver", "mechanic", "strategist", "scout", "medic"}


def register_member(name: str, role: str) -> dict:
    name = name.strip()
    if not name:
        raise ValueError("Member name cannot be empty.")
    role = role.strip().lower()
    if role not in VALID_ROLES:
        raise ValueError(
            f"Invalid role '{role}'. Must be one of: {', '.join(sorted(VALID_ROLES))}."
        )

    members = load("members")
    member_id = str(uuid.uuid4())
    record = {
        "id":         member_id,
        "name":       name,
        "role":       role,
        "skill_level": 1,          # Initial skill level; updated by crew_management
        "is_available": True,      # Becomes False when assigned to a race/ task
    }
    members[member_id] = record
    save("members", members)
    return record


def get_member(member_id: str) -> dict:
    members = load("members")
    if member_id not in members:
        raise KeyError(f"No member found with ID '{member_id}'.")
    return members[member_id]


def get_all_members() -> dict:
    return load("members")


def get_members_by_role(role: str) -> list:
    role = role.strip().lower()
    return [m for m in load("members").values() if m["role"] == role]


def unregister_member(member_id: str) -> dict:
    members = load("members")
    if member_id not in members:
        raise KeyError(f"No member found with ID '{member_id}'.")
    removed = members.pop(member_id)
    save("members", members)
    return removed