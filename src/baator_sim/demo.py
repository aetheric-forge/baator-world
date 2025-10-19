from __future__ import annotations
from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService
from baator_sim.engine import run_scene

def main():
    repo = FileSystemRepository(".")  # relative to project root
    world = WorldService(repo, world_name="demo")
    # bootstrap if empty
    if not world.state.factions:
        f = world.create_faction("Valkyr's House")
        p = world.create_plane("Baator Prime", entropy=0.2, mana=0.6)
        a1 = world.create_actor("Valkyr", faction_id=f, hp=12, power=3, agility=2)
        a2 = world.create_actor("Drone", hp=8, power=2, agility=1)
        s = world.create_scene("Hall of Mirrors", plane_id=p)
        world.add_actor_to_scene(a1, s)
        world.add_actor_to_scene(a2, s)
        world.save()

    # pick any scene
    scene_id = next(iter(world.state.scenes.keys()))
    log = run_scene(world, scene_id, seed=42, max_ticks=8)
    for e in log:
        print(e)

if __name__ == "__main__":
    main()