# tests/test_facets.py
from __future__ import annotations

import pytest
from uuid import uuid4, UUID

from baator.kernel.commands import Command
from baator.kernel.layers import Layer
from baator.domain import Actor
from baator.util import clamp
from baator.domain.facets import PhysicalFacet, CyberFacet, MythicFacet


# ---------- utilities ----------

def mk_actor(name: str = "Valkyr") -> Actor:
    return Actor(id=uuid4(), name=name)


# ---------- clamp correctness ----------

def test_clamp_basic():
    assert clamp(5, 0, 10) == 5
    assert clamp(-1, 0, 10) == 0
    assert clamp(999, 0, 10) == 10

def test_clamp_edges():
    assert clamp(0, 0, 10) == 0
    assert clamp(10, 0, 10) == 10


# ---------- facet attachment & routing ----------

def test_attach_and_dispatch_physical_damage_records_event_and_updates_state():
    a = mk_actor()
    phys = PhysicalFacet(hp=10, stamina=5)
    a.attach_facet(phys)

    cmd = Command(name="physical.take_damage", payload={"layer": Layer.PHYSICAL.value, "amount": 3})
    a.act(cmd)

    # state mutated
    assert phys.hp == 7

    # event recorded & enriched
    evts = a.pull_events()
    assert len(evts) == 1
    evt = evts[0]
    assert evt.name == "physical.damage_taken"
    # enrichment
    assert evt.payload.get("layer") == Layer.PHYSICAL.value
    assert isinstance(evt.payload.get("actor_id"), UUID)
    # facet-specific payload
    assert evt.payload["amount"] == 3
    assert evt.payload["hp"] == 7


def test_dispatch_to_missing_facet_raises():
    a = mk_actor()
    cmd = Command(name="physical.take_damage", payload={"layer": Layer.PHYSICAL.value, "amount": 1})
    with pytest.raises(ValueError):
        a.act(cmd)


def test_multiple_facets_can_coexist_and_isolated_state_is_respected():
    a = mk_actor()
    phys = PhysicalFacet(hp=10, stamina=5)
    cyber = CyberFacet(firewall=3, integrity=8)
    myth  = MythicFacet(essence=6, wards=2)
    a.attach_facet(phys)
    a.attach_facet(cyber)
    a.attach_facet(myth)

    # hit physical
    a.act(Command(name="physical.take_damage", payload={"layer": Layer.PHYSICAL.value, "amount": 4}))
    # hit cyber
    a.act(Command(name="cyber.ice_attack", payload={"layer": Layer.CYBER.value, "damage": 2}))
    # invoke mythic
    a.act(Command(name="mythic.invocation", payload={"layer": Layer.MYTHIC.value, "cost": 1}))

    # state isolation
    assert phys.hp == 6
    assert cyber.integrity == 6
    assert myth.essence == 5

    # events are namespaced and layered
    names = [e.name for e in a.pull_events()]
    assert "physical.damage_taken" in names
    assert "cyber.integrity_damaged" in names
    assert "mythic.invoked" in names


# ---------- facet behavior specifics ----------

def test_mythic_invocation_success_and_failure_paths():
    a = mk_actor()
    myth = MythicFacet(essence=1, wards=0)
    a.attach_facet(myth)

    # success (cost 1)
    a.act(Command(name="mythic.invocation", payload={"layer": Layer.MYTHIC.value, "cost": 1}))
    ev1 = a.pull_events()[0]
    assert ev1.name == "mythic.invoked"
    assert ev1.payload["essence"] == 0

    # failure (insufficient essence)
    a.act(Command(name="mythic.invocation", payload={"layer": Layer.MYTHIC.value, "cost": 2}))
    ev2 = a.pull_events()[0]
    assert ev2.name == "mythic.invocation_failed"
    assert ev2.payload["reason"] == "insufficient_essence"

def test_cyber_ice_attack_reduces_integrity_but_not_below_zero():
    a = mk_actor()
    cyber = CyberFacet(firewall=3, integrity=2)
    a.attach_facet(cyber)

    a.act(Command(name="cyber.ice_attack", payload={"layer": Layer.CYBER.value, "damage": 5}))
    assert cyber.integrity == 0

    evt = a.pull_events()[0]
    assert evt.name == "cyber.integrity_damaged"
    assert evt.payload["integrity"] == 0


# ---------- resilience / no-op semantics ----------

def test_unknown_command_on_facet_is_noop_eventwise_but_does_not_crash():
    a = mk_actor()
    phys = PhysicalFacet(hp=9, stamina=5)
    a.attach_facet(phys)

    a.act(Command(name="physical.unknown_verb", payload={"layer": Layer.PHYSICAL.value}))
    evts = a.pull_events()
    assert evts == []          # no events emitted
    assert phys.hp == 9        # no state change
