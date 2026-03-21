"""Dice rolling logic for turns"""

import random

class Dice:
    """Simulates a pair of six-sided dice with consecutive-doubles tracking."""

    def __init__(self):
        self.die1 = 0
        self.die2 = 0
        self.doubles_streak = 0
        self.reset()

    def reset(self):
        """Reset dice face values and the doubles streak counter."""
        self.die1 = 0
        self.die2 = 0
        self.doubles_streak = 0

    def roll(self):
        """Roll both dice and return their combined total."""
        self.die1 = random.randint(1, 5)
        self.die2 = random.randint(1, 5)
        if self.is_doubles():
            self.doubles_streak += 1
        else:
            self.doubles_streak = 0
        return self.total()

    def is_doubles(self):
        """Return True if both dice show the same value."""
        return self.die1 == self.die2

    def total(self):
        """Return the sum of both dice."""
        return self.die1 + self.die2

    def describe(self):
        """Return a human-readable string describing the last roll."""
        doubles_note = " (DOUBLES)" if self.is_doubles() else ""
        return f"{self.die1} + {self.die2} = {self.total()}{doubles_note}"

    def __repr__(self):
        return f"Dice(die1={self.die1}, die2={self.die2}, streak={self.doubles_streak})"
