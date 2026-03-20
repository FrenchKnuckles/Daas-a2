from data_store import load, save
from registration import get_member

def update_leaderboard(finishing_order: list, payouts: dict) -> None:
    # Update leaderboard stats after a race
    board = load("leaderboard")

    for place_index, mid in enumerate(finishing_order):
        if mid not in board:
            # Initialise entry with member name
            try:
                name = get_member(mid)["name"]
            except KeyError:
                name = mid   # fallback if member was removed
            board[mid] = {
                "member_id":     mid,
                "name":          name,
                "races_entered": 0,
                "wins":          0,
                "podiums":       0,
                "total_earnings": 0.0,
            }

        entry = board[mid]
        entry["races_entered"] += 1

        if place_index == 0:
            entry["wins"] += 1

        if place_index < 3:
            entry["podiums"] += 1

        entry["total_earnings"] = round(
            entry["total_earnings"] + payouts.get(mid, 0.0), 2
        )

    save("leaderboard", board)


def get_leaderboard(top_n: int = None) -> list:
    # leaderboard sorted by wins, then podiums, then earnings
    board = load("leaderboard")
    ranked = sorted(
        board.values(),
        key=lambda e: (-e["wins"], -e["podiums"], -e["total_earnings"])
    )
    if top_n is not None:
        return ranked[:top_n]
    return ranked


def get_driver_stats(member_id: str) -> dict:
    board = load("leaderboard")
    if member_id not in board:
        raise KeyError(f"No leaderboard entry for member '{member_id}'.")
    return board[member_id]


def reset_leaderboard() -> None:
    # Clear leaderboard data (e.g., start of a new season)
    save("leaderboard", {})