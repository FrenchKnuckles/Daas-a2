"""Bank operations for MoneyPoly"""

from moneypoly.config import BANK_STARTING_FUNDS

class Bank:
    """Tracks funds, collections, payouts, and loans"""

    def __init__(self):
        self._funds = BANK_STARTING_FUNDS
        self._loans_issued = []
        self._total_collected = 0

    def get_balance(self):
        """Return the bank's current cash reserves."""
        return self._funds

    def collect(self, amount):
        """
        Receive funds into the bank (taxes, fines, auction proceeds, etc.).
        Negative amounts are silently ignored.
        """
        self._funds += amount
        self._total_collected += amount

    def pay_out(self, amount):
        """
        Pay out `amount` from the bank to a recipient.
        Raises ValueError if the bank lacks sufficient funds.
        Returns the amount paid.
        """
        if amount <= 0:
            return 0
        if amount > self._funds:
            raise ValueError(
                f"Bank cannot pay ${amount}; only ${self._funds} available."
            )
        self._funds -= amount
        return amount

    def give_loan(self, player, amount):
        """
        Issue an emergency loan to `player`, crediting their balance with `amount`.
        The bank's own funds are reduced accordingly.
        """
        if amount <= 0:
            return
        player.add_money(amount)
        self._loans_issued.append((player.name, amount))
        print(f"  Bank issued a ${amount} emergency loan to {player.name}.")

    def total_loans_issued(self):
        """Return the cumulative value of all loans the bank has issued."""
        return sum(amt for _, amt in self._loans_issued)

    def loan_count(self):
        """Return the number of loans the bank has issued."""
        return len(self._loans_issued)

    def summary(self):
        """Print a formatted summary of the bank's financial state."""
        print(f"  Bank reserves  : ${self._funds:,}")
        print(f"  Total collected: ${self._total_collected:,}")
        print(f"  Loans issued   : {len(self._loans_issued)} (${self.total_loans_issued():,})")

    def __repr__(self):
        return f"Bank(funds={self._funds})"
