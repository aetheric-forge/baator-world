from __future__ import annotations
from pathlib import Path
from baator_data.fs_repo import FileSystemRepository
from baator_services.world import WorldService
from baator_services.content import ContentLoader
from baator_rules.markdown import ruleset_to_markdown

def main():
    repo = FileSystemRepository(".")
    world = WorldService(repo, world_name="content_demo")
    loader = ContentLoader(world)
    report = loader.load_pack("baator_base")
    world.save()
    print(f"Loaded factions={report.factions}, planes={report.planes}, rules={report.rules}")
    # If rules present, render to Markdown
    rules = getattr(world, "_meta", {}).get("rules", [])
    if rules:
        md = ruleset_to_markdown(rules, title="Baator Base Rules")
        out = Path("worlds") / "baator_base_rules.md"
        out.write_text(md)
        print(f"Wrote Markdown: {out}")

if __name__ == "__main__":
    main()