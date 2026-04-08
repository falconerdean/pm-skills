#!/usr/bin/env python3
"""
Merges per-epic story files into a consolidated story_map.json.
Run: python3 scripts/merge_stories.py --dir <output_directory>
"""

import json
import sys
from pathlib import Path
from typing import Dict, List


def merge_story_files(output_dir: Path) -> dict:
    """Merge all phase6_stories_*.json files into a single story map."""
    story_files = sorted(output_dir.glob("phase6_stories_*.json"))
    if not story_files:
        print("ERROR: No story files found")
        sys.exit(1)

    epics = []
    all_stories = []
    total_points = 0
    total_stories = 0

    for sf in story_files:
        with open(sf) as f:
            data = json.load(f)

        epic_id = data.get("epic_id", sf.stem.replace("phase6_stories_", ""))
        epic_title = data.get("epic_title", epic_id)
        stories = data.get("stories", [])
        epic_points = sum(s.get("story_points", 0) for s in stories)

        epics.append({
            "epic_id": epic_id,
            "epic_title": epic_title,
            "story_count": len(stories),
            "total_points": epic_points,
            "story_ids": [s.get("id") for s in stories]
        })

        all_stories.extend(stories)
        total_points += epic_points
        total_stories += len(stories)

    # Build cross-epic dependency map
    story_to_epic = {}
    for epic in epics:
        for sid in epic["story_ids"]:
            story_to_epic[sid] = epic["epic_id"]

    cross_deps = []
    for story in all_stories:
        sid = story.get("id")
        deps = story.get("dependencies", {})
        if isinstance(deps, list):
            # Some agents write dependencies as a flat list; skip cross-epic analysis
            continue
        blocked_by_list = deps.get("blocked_by", deps.get("blocked_by_stories", []))
        if isinstance(blocked_by_list, str):
            blocked_by_list = [blocked_by_list]
        for blocked_by in blocked_by_list:
            if blocked_by in story_to_epic:
                from_epic = story_to_epic.get(blocked_by)
                to_epic = story_to_epic.get(sid)
                if from_epic and to_epic and from_epic != to_epic:
                    cross_deps.append({
                        "from_story": blocked_by,
                        "from_epic": from_epic,
                        "to_story": sid,
                        "to_epic": to_epic
                    })

    # Check feature coverage (if phase4 exists)
    features_file = output_dir / "phase4_features.json"
    coverage = {"features_total": 0, "features_covered": 0, "missing_features": []}
    if features_file.exists():
        with open(features_file) as f:
            features_data = json.load(f)
        mvp_features = set(features_data.get("mvp_boundary", {}).get("must_have", []))
        coverage["features_total"] = len(mvp_features)

        # Check epics file for feature mapping
        epics_file = output_dir / "phase5_epics.json"
        if epics_file.exists():
            with open(epics_file) as f:
                epics_data = json.load(f)
            covered = set()
            for epic in epics_data.get("epics", []):
                for feat in epic.get("features_included", []):
                    fid = feat.get("id") if isinstance(feat, dict) else feat
                    covered.add(fid)
            coverage["features_covered"] = len(mvp_features & covered)
            coverage["missing_features"] = list(mvp_features - covered)

    story_map = {
        "generated_at": "",
        "total_epics": len(epics),
        "total_stories": total_stories,
        "total_story_points": total_points,
        "epics_summary": epics,
        "stories": all_stories,
        "cross_epic_dependencies": cross_deps,
        "feature_coverage": coverage,
        "validation": {
            "stories_with_ac": sum(1 for s in all_stories if s.get("acceptance_criteria")),
            "stories_with_design_needs": sum(
                1 for s in all_stories
                if (isinstance(s.get("design_needs"), dict) and s["design_needs"].get("requires_mockup"))
                or (isinstance(s.get("design_needs"), str) and s["design_needs"])
            ),
            "stories_with_tech_notes": sum(1 for s in all_stories if s.get("technical_notes")),
            "stories_with_points": sum(1 for s in all_stories if s.get("story_points"))
        }
    }

    return story_map


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--dir":
        print("Usage: python3 merge_stories.py --dir <output_directory>")
        sys.exit(1)

    output_dir = Path(sys.argv[2])
    if not output_dir.exists():
        print(f"ERROR: Directory not found: {output_dir}")
        sys.exit(1)

    story_map = merge_story_files(output_dir)

    output_file = output_dir / "story_map.json"
    with open(output_file, "w") as f:
        json.dump(story_map, f, indent=2)

    print(f"Story map written to: {output_file}")
    print(f"  Epics: {story_map['total_epics']}")
    print(f"  Stories: {story_map['total_stories']}")
    print(f"  Total Points: {story_map['total_story_points']}")
    if story_map["cross_epic_dependencies"]:
        print(f"  Cross-Epic Dependencies: {len(story_map['cross_epic_dependencies'])}")
    coverage = story_map["feature_coverage"]
    if coverage["features_total"]:
        print(f"  Feature Coverage: {coverage['features_covered']}/{coverage['features_total']}")
        if coverage["missing_features"]:
            print(f"  Missing Features: {', '.join(coverage['missing_features'])}")


if __name__ == "__main__":
    main()
