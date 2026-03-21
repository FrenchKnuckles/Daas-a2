"""Console UI helpers for displaying and collecting game information"""

def print_banner(title):
    """Print a decorated section header."""
    width = 52
    print("\n" + "=" * width)
    print(f"  {title}")
    print("=" * width)


def print_player_card(player):
    """Print a detailed status card for a single player."""
    jail_line = f"  Status  : IN JAIL (turn {player.jail_turns}/3)\n" if player.in_jail else ""
    print(f"\n  Player  : {player.name}")
    print(f"  Balance : ${player.balance:,}")
    print(f"  Worth   : ${player.net_worth():,}")
    print(f"  Position: {player.position}")
    print(jail_line, end="")
    if player.get_out_of_jail_cards:
        print(f"  Jail cards: {player.get_out_of_jail_cards}")
    if player.properties:
        print("  Properties:")
        for prop in player.properties:
            tag = " [MORTGAGED]" if prop.is_mortgaged else ""
            print(f"    {prop.name:<32} rent ${prop.get_rent()}{tag}")
    else:
        print("  Properties: none")


def print_standings(players):
    """Print a compact leaderboard for all active players."""
    print("\n  [ Standings ]")
    ranked = sorted(players, key=lambda p: p.net_worth(), reverse=True)
    for i, player in enumerate(ranked, start=1):
        jail_tag = " [JAILED]" if player.in_jail else ""
        print(
            f"  {i}. {player.name:<16} "
            f"${player.balance:>6,}  "
            f"({player.count_properties()} props)"
            f"{jail_tag}"
        )


def print_board_ownership(board):
    """Print a table showing every property and its current owner."""
    print("\n  [ Property Register ]")
    print(f"  {'Pos':>3}  {'Property':<32}  {'Price':>5}  {'Rent':>4}  Owner")
    print("  " + "-" * 64)
    for prop in board.properties:
        owner = prop.owner.name if prop.owner else "---"
        mortgage_flag = "*" if prop.is_mortgaged else " "
        print(
            f"  {prop.position:>3}  {prop.name:<32}  "
            f"${prop.price:>4}  ${prop.get_rent():>3}  "
            f"{mortgage_flag}{owner}"
        )
    print("  (* = mortgaged)")


def format_currency(amount):
    """Return a formatted currency string, e.g. '$1,500'."""
    return f"${amount:,}"


def safe_int_input(prompt, default=0):
    """
    Prompt the user for an integer, returning `default` on invalid input.
    """
    try:
        return int(input(prompt))
    except:
        return default


def confirm(prompt):
    """Prompt the user for a yes/no answer. Returns True for 'y'."""
    return input(prompt).strip().lower() == "y"
