import builtins
import pytest
from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CardDeck
from moneypoly.config import GO_SALARY, JAIL_FINE
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup
from moneypoly import ui


class StubDice:
    def __init__(self, roll_value=4, doubles=False, streak_after_roll=0):
        self.roll_value = roll_value
        self._doubles = doubles
        self.doubles_streak = 0
        self._streak_after_roll = streak_after_roll

    def roll(self):
        self.doubles_streak = self._streak_after_roll
        return self.roll_value

    def is_doubles(self):
        return self._doubles

    def describe(self):
        return "stub roll"


@pytest.fixture
def game_two_players():
    return Game(["Alice", "Bob"])


def test_bank_pay_out_edges_and_insufficient():
    bank = Bank()
    assert bank.pay_out(0) == 0
    assert bank.pay_out(-1) == 0

    with pytest.raises(ValueError):
        bank.pay_out(bank.get_balance() + 1)


def test_bank_loan_tracking(game_two_players):
    bank = Bank()
    player = game_two_players.players[0]
    start = player.balance

    bank.give_loan(player, 120)

    assert player.balance == start + 120
    assert bank.loan_count() == 1
    assert bank.total_loans_issued() == 120


def test_card_deck_draw_cycles_and_peek():
    deck = CardDeck([
        {"description": "c1", "action": "collect", "value": 10},
        {"description": "c2", "action": "pay", "value": 5},
    ])

    assert deck.peek()["description"] == "c1"
    assert deck.draw()["description"] == "c1"
    assert deck.draw()["description"] == "c2"
    assert deck.draw()["description"] == "c1"


def test_card_deck_empty_returns_none():
    deck = CardDeck([])
    assert deck.draw() is None
    assert deck.peek() is None


def test_player_add_deduct_negative_raises():
    player = Player("P1")

    with pytest.raises(ValueError):
        player.add_money(-1)

    with pytest.raises(ValueError):
        player.deduct_money(-1)


def test_player_move_wraps_and_collects_go_salary():
    player = Player("P1")
    player.position = 39
    start = player.balance

    pos = player.move(1)

    assert pos == 0
    assert player.balance == start + GO_SALARY


def test_player_go_to_jail_sets_state():
    player = Player("P1")
    player.go_to_jail()

    assert player.in_jail is True
    assert player.jail_turns == 0


def test_property_mortgage_unmortgage_cycle():
    prop = Property("X", 1, 100, 10)

    assert prop.mortgage() == 50
    assert prop.mortgage() == 0
    assert prop.unmortgage() == 55
    assert prop.unmortgage() == 0


def test_property_is_available_states():
    prop = Property("X", 1, 100, 10)
    assert prop.is_available() is True

    prop.is_mortgaged = True
    assert prop.is_available() is False

    prop.is_mortgaged = False
    prop.owner = Player("Owner")
    assert prop.is_available() is False


def test_board_tile_and_lookup_and_purchasable_branches(game_two_players):
    board = Board()

    assert board.get_tile_type(0) == "go"
    assert board.get_tile_type(1) == "property"
    assert board.get_tile_type(12) == "blank"

    assert board.get_property_at(12) is None
    prop = board.get_property_at(1)
    assert prop is not None

    assert board.is_purchasable(12) is False
    assert board.is_purchasable(1) is True

    prop.is_mortgaged = True
    assert board.is_purchasable(1) is False

    prop.is_mortgaged = False
    prop.owner = game_two_players.players[0]
    assert board.is_purchasable(1) is False


def test_ui_safe_int_input_valid_and_invalid(monkeypatch):
    monkeypatch.setattr(builtins, "input", lambda _: "123")
    assert ui.safe_int_input("n", default=7) == 123

    monkeypatch.setattr(builtins, "input", lambda _: "bad")
    assert ui.safe_int_input("n", default=7) == 7


def test_handle_property_tile_branches_buy_auction_skip_owner_and_rent(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    other = game.players[1]
    prop = game.board.get_property_at(1)

    calls = {"buy": 0, "auction": 0, "rent": 0}

    def fake_buy(_player, _prop):
        calls["buy"] += 1

    def fake_auction(_prop):
        calls["auction"] += 1

    def fake_rent(_player, _prop):
        calls["rent"] += 1

    monkeypatch.setattr(game, "buy_property", fake_buy)
    monkeypatch.setattr(game, "auction_property", fake_auction)
    monkeypatch.setattr(game, "pay_rent", fake_rent)

    prop.owner = None
    monkeypatch.setattr(builtins, "input", lambda _: "b")
    game._handle_property_tile(player, prop)

    prop.owner = None
    monkeypatch.setattr(builtins, "input", lambda _: "a")
    game._handle_property_tile(player, prop)

    prop.owner = None
    monkeypatch.setattr(builtins, "input", lambda _: "s")
    game._handle_property_tile(player, prop)

    prop.owner = player
    game._handle_property_tile(player, prop)

    prop.owner = other
    game._handle_property_tile(player, prop)

    assert calls["buy"] == 1
    assert calls["auction"] == 1
    assert calls["rent"] == 1


def test_game_buy_property_success_and_failure(game_two_players):
    game = game_two_players
    player = game.players[0]
    prop = game.board.get_property_at(1)

    player.balance = prop.price - 1
    assert game.buy_property(player, prop) is False

    player.balance = prop.price + 100
    assert game.buy_property(player, prop) is True
    assert prop.owner == player


def test_game_trade_success_and_failure(game_two_players):
    game = game_two_players
    seller, buyer = game.players
    prop = game.board.get_property_at(1)

    assert game.trade(seller, buyer, prop, 50) is False

    prop.owner = seller
    seller.add_property(prop)
    buyer.balance = 10
    assert game.trade(seller, buyer, prop, 20) is False

    buyer.balance = 100
    assert game.trade(seller, buyer, prop, 20) is True
    assert prop.owner == buyer


def test_game_auction_no_bids_and_winner(game_two_players, monkeypatch):
    game = game_two_players
    prop = game.board.get_property_at(3)

    monkeypatch.setattr(ui, "safe_int_input", lambda *_args, **_kwargs: 0)
    game.auction_property(prop)
    assert prop.owner is None

    bids = iter([10, 30])
    monkeypatch.setattr(ui, "safe_int_input", lambda *_args, **_kwargs: next(bids))
    game.auction_property(prop)
    assert prop.owner == game.players[1]


def test_game_play_turn_jail_and_doubles_branches(monkeypatch, game_two_players):
    game = game_two_players

    game.players[0].in_jail = True
    called = {"jail": 0}

    def fake_handle_jail_turn(_player):
        called["jail"] += 1

    monkeypatch.setattr(game, "_handle_jail_turn", fake_handle_jail_turn)
    game.play_turn()
    assert called["jail"] == 1

    game.current_index = 0
    game.players[0].in_jail = False
    game.dice = StubDice(roll_value=5, doubles=False, streak_after_roll=3)
    game.play_turn()
    assert game.players[0].in_jail is True

    game.players[0].in_jail = False
    game.current_index = 0
    game.dice = StubDice(roll_value=3, doubles=True, streak_after_roll=0)
    monkeypatch.setattr(game, "_move_and_resolve", lambda *_args, **_kwargs: None)
    game.play_turn()
    assert game.current_index == 0


def test_handle_jail_turn_card_pay_and_mandatory_release(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]

    game.dice = StubDice(roll_value=4)
    monkeypatch.setattr(game, "_move_and_resolve", lambda *_args, **_kwargs: None)

    player.in_jail = True
    player.get_out_of_jail_cards = 1
    monkeypatch.setattr(ui, "confirm", lambda _msg: True)
    game._handle_jail_turn(player)
    assert player.in_jail is False
    assert player.get_out_of_jail_cards == 0

    player.in_jail = True
    player.get_out_of_jail_cards = 0
    player.jail_turns = 0
    monkeypatch.setattr(ui, "confirm", lambda _msg: True)
    game._handle_jail_turn(player)
    assert player.in_jail is False

    player.in_jail = True
    player.get_out_of_jail_cards = 0
    player.jail_turns = 2
    player.balance = 200
    monkeypatch.setattr(ui, "confirm", lambda _msg: False)
    game._handle_jail_turn(player)
    assert player.in_jail is False
    assert player.balance == 200 - JAIL_FINE


def test_apply_card_action_branches(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    other = game.players[1]

    start = player.balance
    game._apply_card(player, {"description": "c", "action": "collect", "value": 50})
    assert player.balance == start + 50

    start = player.balance
    game._apply_card(player, {"description": "c", "action": "pay", "value": 10})
    assert player.balance == start - 10

    game._apply_card(player, {"description": "c", "action": "jail", "value": 0})
    assert player.in_jail is True

    player.in_jail = False
    player.get_out_of_jail_cards = 0
    game._apply_card(player, {"description": "c", "action": "jail_free", "value": 0})
    assert player.get_out_of_jail_cards == 1

    prop = game.board.get_property_at(39)
    prop.owner = None
    monkeypatch.setattr(builtins, "input", lambda _msg: "s")
    player.position = 38
    game._apply_card(player, {"description": "c", "action": "move_to", "value": 0})
    assert player.position == 0

    player.balance = 1000
    other.balance = 1000
    game._apply_card(player, {"description": "c", "action": "birthday", "value": 10})
    assert player.balance == 1010
    assert other.balance == 990

    player.balance = 1000
    other.balance = 1000
    game._apply_card(player, {"description": "c", "action": "collect_from_all", "value": 10})
    assert player.balance == 1010
    assert other.balance == 990


def test_find_winner_should_pick_highest_net_worth(game_two_players):
    game = game_two_players
    game.players[0].balance = 2000
    game.players[1].balance = 1000
    assert game.find_winner() == game.players[0]


def test_pay_rent_should_transfer_to_owner(game_two_players):
    game = game_two_players
    payer, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner

    payer.balance = 500
    owner.balance = 500
    game.pay_rent(payer, prop)

    assert owner.balance > 500


def test_property_group_all_owned_by_requires_full_group():
    group = PropertyGroup("Test", "test")
    p1 = Property("A", 1, 100, 10)
    p2 = Property("B", 2, 100, 10)
    group.add_property(p1)
    group.add_property(p2)

    owner = Player("Owner")
    p1.owner = owner
    p2.owner = None

    assert group.all_owned_by(owner) is False


def test_dice_roll_should_use_six_sided_bounds(monkeypatch):
    from moneypoly import dice as dice_module

    seen = []

    def fake_randint(a, b):
        seen.append((a, b))
        return 1

    monkeypatch.setattr(dice_module.random, "randint", fake_randint)
    d = dice_module.Dice()
    d.roll()

    assert seen == [(1, 6), (1, 6)]


def test_move_and_resolve_go_to_jail_tile(game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 29

    game._move_and_resolve(player, 1)

    assert player.in_jail is True


def test_move_and_resolve_income_tax_deducts_and_collects(game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 3
    player.balance = 1000
    bank_before = game.bank.get_balance()

    game._move_and_resolve(player, 1)

    assert player.balance == 800
    assert game.bank.get_balance() == bank_before + 200


def test_move_and_resolve_luxury_tax_deducts_and_collects(game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 37
    player.balance = 1000
    bank_before = game.bank.get_balance()

    game._move_and_resolve(player, 1)

    assert player.balance == 925
    assert game.bank.get_balance() == bank_before + 75


def test_move_and_resolve_free_parking_no_balance_change(game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 19
    player.balance = 777
    bank_before = game.bank.get_balance()

    game._move_and_resolve(player, 1)

    assert player.balance == 777
    assert game.bank.get_balance() == bank_before


def test_move_and_resolve_chance_draw_and_apply_called(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 6
    called = {"apply": 0}

    monkeypatch.setattr(game.decks["chance"], "draw", lambda: {"description": "c", "action": "pay", "value": 1})

    def fake_apply(_player, _card):
        called["apply"] += 1

    monkeypatch.setattr(game, "_apply_card", fake_apply)
    game._move_and_resolve(player, 1)

    assert called["apply"] == 1


def test_move_and_resolve_community_draw_and_apply_called(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 1
    called = {"apply": 0}

    monkeypatch.setattr(game.decks["community_chest"], "draw", lambda: {"description": "c", "action": "collect", "value": 1})

    def fake_apply(_player, _card):
        called["apply"] += 1

    monkeypatch.setattr(game, "_apply_card", fake_apply)
    game._move_and_resolve(player, 1)

    assert called["apply"] == 1


def test_move_and_resolve_railroad_branch_without_property(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 4
    called = {"handle": 0}

    def fake_handle(_player, _prop):
        called["handle"] += 1

    monkeypatch.setattr(game, "_handle_property_tile", fake_handle)
    game._move_and_resolve(player, 1)

    assert called["handle"] == 0


def test_move_and_resolve_property_branch_calls_handler(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 0
    called = {"handle": 0}

    def fake_handle(_player, _prop):
        called["handle"] += 1

    monkeypatch.setattr(game, "_handle_property_tile", fake_handle)
    game._move_and_resolve(player, 1)

    assert called["handle"] == 1


def test_move_and_resolve_blank_tile_path(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    player.position = 11
    called = {"check": 0}

    def fake_check(_player):
        called["check"] += 1

    monkeypatch.setattr(game, "_check_bankruptcy", fake_check)
    game._move_and_resolve(player, 1)

    assert called["check"] == 1


def test_pay_rent_returns_when_mortgaged(game_two_players):
    game = game_two_players
    payer, owner = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    prop.is_mortgaged = True
    payer.balance = 500
    owner.balance = 500

    game.pay_rent(payer, prop)

    assert payer.balance == 500
    assert owner.balance == 500


def test_pay_rent_returns_when_no_owner(game_two_players):
    game = game_two_players
    payer = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = None
    payer.balance = 500

    game.pay_rent(payer, prop)

    assert payer.balance == 500


def test_mortgage_property_non_owner_fails(game_two_players):
    game = game_two_players
    owner, other = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner

    assert game.mortgage_property(other, prop) is False


def test_mortgage_property_already_mortgaged_fails(game_two_players):
    game = game_two_players
    owner = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = owner
    prop.is_mortgaged = True

    assert game.mortgage_property(owner, prop) is False


def test_unmortgage_property_non_owner_fails(game_two_players):
    game = game_two_players
    owner, other = game.players
    prop = game.board.get_property_at(1)
    prop.owner = owner
    prop.is_mortgaged = True

    assert game.unmortgage_property(other, prop) is False


def test_unmortgage_property_not_mortgaged_fails(game_two_players):
    game = game_two_players
    owner = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = owner
    prop.is_mortgaged = False

    assert game.unmortgage_property(owner, prop) is False


def test_unmortgage_property_insufficient_balance_fails(game_two_players):
    game = game_two_players
    owner = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = owner
    prop.is_mortgaged = True
    owner.balance = 1

    assert game.unmortgage_property(owner, prop) is False


def test_apply_card_unknown_action_no_effect(game_two_players):
    game = game_two_players
    player = game.players[0]
    before = (player.balance, player.position, player.in_jail, player.get_out_of_jail_cards)

    game._apply_card(player, {"description": "unknown", "action": "no_op", "value": 99})

    after = (player.balance, player.position, player.in_jail, player.get_out_of_jail_cards)
    assert before == after


def test_apply_card_move_to_property_invokes_property_handler(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    called = {"handle": 0}

    def fake_handle(_player, _prop):
        called["handle"] += 1

    monkeypatch.setattr(game, "_handle_property_tile", fake_handle)
    game._apply_card(player, {"description": "move", "action": "move_to", "value": 1})

    assert called["handle"] == 1


def test_check_bankruptcy_releases_assets_and_removes_player(game_two_players):
    game = game_two_players
    player = game.players[0]
    prop = game.board.get_property_at(1)
    prop.owner = player
    prop.is_mortgaged = True
    player.add_property(prop)
    player.balance = 0
    game.current_index = 1

    game._check_bankruptcy(player)

    assert player not in game.players
    assert prop.owner is None
    assert prop.is_mortgaged is False
    assert game.current_index == 0

def test_player_move_past_go_should_collect_salary():
    player = Player("P1")
    player.position = 39
    start = player.balance

    player.move(2)

    assert player.balance == start + GO_SALARY

def test_game_init_with_single_player_should_raise_value_error():
    with pytest.raises(ValueError):
        Game(["Solo"])


def test_buy_property_with_exact_balance_should_succeed(game_two_players):
    game = game_two_players
    player = game.players[0]
    prop = game.board.get_property_at(1)
    player.balance = prop.price

    result = game.buy_property(player, prop)

    assert result is True
    assert player.balance == 0
    assert prop.owner == player


def test_trade_with_zero_cash_should_fail(game_two_players):
    game = game_two_players
    seller, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = seller
    seller.add_property(prop)

    assert game.trade(seller, buyer, prop, 0) is False


def test_trade_with_negative_cash_should_fail(game_two_players):
    game = game_two_players
    seller, buyer = game.players
    prop = game.board.get_property_at(1)
    prop.owner = seller
    seller.add_property(prop)

    assert game.trade(seller, buyer, prop, -10) is False


def test_handle_jail_turn_voluntary_fine_deducts_player_balance(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    player.in_jail = True
    player.get_out_of_jail_cards = 0
    player.jail_turns = 0
    player.balance = 300

    monkeypatch.setattr(ui, "confirm", lambda _msg: True)
    monkeypatch.setattr(game, "_move_and_resolve", lambda *_args, **_kwargs: None)
    game.dice = StubDice(roll_value=4)

    game._handle_jail_turn(player)

    assert player.balance == 300 - JAIL_FINE


def test_bank_collect_negative_amount_should_not_reduce_funds():
    bank = Bank()
    before = bank.get_balance()

    bank.collect(-100)

    assert bank.get_balance() == before


def test_bank_give_loan_should_reduce_bank_funds(game_two_players):
    bank = Bank()
    player = game_two_players.players[0]
    before = bank.get_balance()

    bank.give_loan(player, 100)

    assert bank.get_balance() == before - 100


def test_empty_property_group_all_owned_by_returns_false():
    group = PropertyGroup("Empty", "gray")
    owner = Player("Owner")

    assert group.all_owned_by(owner) is False


def test_run_ends_immediately_when_one_player_left(monkeypatch):
    game = Game(["A", "B"])
    game.players = [game.players[0]]

    called = {"turn": 0}

    def fake_play_turn():
        called["turn"] += 1

    monkeypatch.setattr(game, "play_turn", fake_play_turn)
    game.run()

    assert called["turn"] == 0


def test_interactive_menu_exits_on_zero_choice(monkeypatch, game_two_players):
    game = game_two_players
    player = game.players[0]
    monkeypatch.setattr(ui, "safe_int_input", lambda *_args, **_kwargs: 0)

    game.interactive_menu(player)
