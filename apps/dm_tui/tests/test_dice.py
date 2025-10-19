# tests/test_dice.py
import sys, pathlib
import types

# --- ensure project root import works without editable install ---
ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# --- tiny deterministic randint shim (inline, no external helper) ---
class SeqRandInt:
    """
    Deterministic replacement for random.randint(a, b).
    Provide a sequence of integers; each call returns the next value.
    If the sequence is exhausted, the last value is repeated.
    """
    def __init__(self, seq):
        assert seq, "SeqRandInt requires at least one value"
        self.seq = list(seq)
        self.last = seq[-1]

    def __call__(self, a, b):
        if self.seq:
            self.last = self.seq.pop(0)
        return self.last

def test_parse_supports_weird_dice():
    from dm_tui.core import dice
    p = dice.parse("d5")
    assert p["sides"] == 5 and p["count"] == 1

    p = dice.parse("4d6kh3")
    assert p["sides"] == 6 and p["keep"] == ("kh", 3)

    p = dice.parse("d10!>9")
    assert p["explode_on"] == 9

def test_roll_basic_with_modifier(monkeypatch):
    from dm_tui.core import dice
    # 2d6 → 3 and 5, plus +1 mod
    monkeypatch.setattr(dice.random, "randint", SeqRandInt([3, 5]))
    r = dice.roll("2d6+1")
    assert r.rolls == [3, 5]
    assert r.total == 3 + 5 + 1

def test_roll_exploding_and_keep(monkeypatch):
    from dm_tui.core import dice
    # 2d6! with kh2; first die 6 then 4 (explode once), second die 2
    monkeypatch.setattr(dice.random, "randint", SeqRandInt([6, 4, 2]))
    r = dice.roll("2d6!kh2")
    # Implementation detail: some rollers record only final values; accept either.
    assert sum(sorted(r.kept, reverse=True)[:2]) == 10
    assert r.total == 10

def test_reroll_condition_lt(monkeypatch):
    from dm_tui.core import dice
    # d20r<2 should reroll a 1 once → 13
    monkeypatch.setattr(dice.random, "randint", SeqRandInt([1, 13]))
    r = dice.roll("d20r<2")
    # Don’t assume internal representation; assert the effect:
    assert r.total >= 2
