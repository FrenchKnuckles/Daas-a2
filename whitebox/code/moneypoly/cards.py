"""Card definitions and deck behavior """

import random

CHANCE_CARDS = [
    {"description": "Advance to Go. Collect $200.",                          "action": "move_to",  "value": 0},
    {"description": "Bank pays you a dividend of $50.",                      "action": "collect",  "value": 50},
    {"description": "Go to Jail. Go directly to Jail.",                      "action": "jail",     "value": 0},
    {"description": "Pay a poor tax of $15.",                                "action": "pay",      "value": 15},
    {"description": "You have won a crossword competition. Collect $100.",   "action": "collect",  "value": 100},
    {"description": "Your building and loan matures. Collect $150.",         "action": "collect",  "value": 150},
    {"description": "Pay school fees of $150.",                              "action": "pay",      "value": 150},
    {"description": "Advance to Boardwalk.",                                 "action": "move_to",  "value": 39},
    {"description": "Get Out of Jail Free. Keep until needed.",              "action": "jail_free","value": 0},
    {"description": "Speeding fine — pay $15.",                              "action": "pay",      "value": 15},
    {"description": "You are assessed for street repairs. Pay $40.",         "action": "pay",      "value": 40},
    {"description": "Collect $50 from every other player.",                  "action": "collect_from_all", "value": 50},
]

COMMUNITY_CHEST_CARDS = [
    {"description": "Bank error in your favour. Collect $200.",              "action": "collect",  "value": 200},
    {"description": "Doctor's fees. Pay $50.",                               "action": "pay",      "value": 50},
    {"description": "From sale of stock you get $50.",                       "action": "collect",  "value": 50},
    {"description": "Go to Jail.",                                           "action": "jail",     "value": 0},
    {"description": "Holiday fund matures. Receive $100.",                   "action": "collect",  "value": 100},
    {"description": "Income tax refund. Collect $20.",                       "action": "collect",  "value": 20},
    {"description": "It is your birthday. Collect $10 from every player.",   "action": "birthday", "value": 10},
    {"description": "Life insurance matures. Collect $100.",                 "action": "collect",  "value": 100},
    {"description": "Pay hospital fees of $100.",                            "action": "pay",      "value": 100},
    {"description": "Pay school fees of $50.",                               "action": "pay",      "value": 50},
    {"description": "Receive $25 consultancy fee.",                          "action": "collect",  "value": 25},
    {"description": "Get Out of Jail Free.",                                 "action": "jail_free","value": 0},
]


class CardDeck:
    """Represents an ordered deck of Chance or Community Chest cards."""

    def __init__(self, cards):
        self.cards = list(cards)
        self.index = 0

    def draw(self):
        """
        Draw the next card from the deck, cycling back to the start
        when the deck is exhausted. Returns the card dict.
        """
        if not self.cards:
            return None
        card = self.cards[self.index % len(self.cards)]
        self.index += 1
        return card

    def peek(self):
        """Return the next card without advancing the index."""
        if not self.cards:
            return None
        return self.cards[self.index % len(self.cards)]

    def reshuffle(self):
        """Shuffle the deck and reset the draw index."""
        random.shuffle(self.cards)
        self.index = 0

    def cards_remaining(self):
        """Return how many cards remain before the deck cycles."""
        return len(self.cards) - (self.index % len(self.cards))

    def __len__(self):
        return len(self.cards)

    def __repr__(self):
        return f"CardDeck({len(self.cards)} cards, next={self.index % len(self.cards)})"
