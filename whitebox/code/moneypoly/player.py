"""Player state and actions"""

from moneypoly.config import STARTING_BALANCE, BOARD_SIZE, GO_SALARY, JAIL_POSITION


class Player:
    """Represents a single player in a MoneyPoly game."""

    def __init__(self, name, balance=STARTING_BALANCE):
        self.name = name
        self.balance = balance
        self.position = 0
        self.properties = []
        self.in_jail = False
        self.jail_turns = 0
        self.get_out_of_jail_cards = 0
        self.is_eliminated = False


    def add_money(self, amount):
        """Add funds to this player's balance. Amount must be non-negative."""
        if amount < 0:
            raise ValueError(f"Cannot add a negative amount: {amount}")
        self.balance += amount

    def deduct_money(self, amount):
        """Deduct funds from this player's balance. Amount must be non-negative."""
        if amount < 0:
            raise ValueError(f"Cannot deduct a negative amount: {amount}")
        self.balance -= amount

    def is_bankrupt(self):
        """Return True if this player has no money remaining."""
        return self.balance <= 0

    def net_worth(self):
        """Calculate and return this player's total net worth."""
        return self.balance

    def move(self, steps):
        """
        Move this player forward by `steps` squares, wrapping around the board.
        Awards the Go salary if the player passes or lands on Go.
        Returns the new board position.
        """
        self.position = (self.position + steps) % BOARD_SIZE

        if self.position == 0:
            self.add_money(GO_SALARY)
            print(f"  {self.name} landed on Go and collected ${GO_SALARY}.")

        return self.position

    def go_to_jail(self):
        """Send this player directly to the Jail square."""
        self.position = JAIL_POSITION
        self.in_jail = True
        self.jail_turns = 0


    def add_property(self, prop):
        """Add a property tile to this player's holdings."""
        if prop not in self.properties:
            self.properties.append(prop)

    def remove_property(self, prop):
        """Remove a property tile from this player's holdings."""
        if prop in self.properties:
            self.properties.remove(prop)

    def count_properties(self):
        """Return the number of properties this player currently owns."""
        return len(self.properties)


    def status_line(self):
        """Return a concise one-line status string for this player."""
        jail_tag = " [JAILED]" if self.in_jail else ""
        return (
            f"{self.name}: ${self.balance}  "
            f"pos={self.position}  "
            f"props={len(self.properties)}"
            f"{jail_tag}"
        )

    def __repr__(self):
        return f"Player({self.name!r}, balance={self.balance}, pos={self.position})"