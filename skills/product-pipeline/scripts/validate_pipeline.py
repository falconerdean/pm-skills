#!/usr/bin/env python3
"""
Validates product pipeline artifacts for consistency and completeness.
Run: python3 scripts/validate_pipeline.py --dir <output_directory>
"""

import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Tuple


def load_json(path: Path) -> dict:
    """Load a JSON file, return empty dict if not found."""
    if not path.exists():
        return {}
    with open(path) as f:
        return json.load(f)


def validate_phase1(output_dir: Path) -> Tuple[bool, List[str]]:
    """Validate Phase 1: Research output."""
    errors = []
    data = load_json(output_dir / "phase1_research.json")
    if not data:
        return False, ["phase1_research.json not found"]

    required_dims = ["market_landscape", "user_pain_points", "behavioral_patterns",
                     "technology_landscape", "regulatory"]
    for dim in required_dims:
        if dim not in data:
            errors.append(f"Missing research dimension: {dim}")
        elif not data[dim].get("findings"):
            errors.append(f"No findings in dimension: {dim}")

    if not data.get("key_insights"):
        errors.append("No key_insights found")
    elif len(data["key_insights"]) < 3:
        errors.append(f"Only {len(data['key_insights'])} key insights (need 3+)")

    source_count = sum(
        len(dim.get("findings", []))
        for dim in [data.get(d, {}) for d in required_dims]
    )
    if source_count < 10:
        errors.append(f"Only {source_count} total findings (need 10+)")

    return len(errors) == 0, errors


def validate_phase2(output_dir: Path) -> Tuple[bool, List[str]]:
    """Validate Phase 2: Problem framing output."""
    errors = []
    data = load_json(output_dir / "phase2_problem_frame.json")
    if not data:
        return False, ["phase2_problem_frame.json not found"]

    if not data.get("problem_statement"):
        errors.append("Missing problem_statement")
    if not data.get("opportunity_hypothesis"):
        errors.append("Missing opportunity_hypothesis")

    personas = data.get("personas", [])
    if len(personas) < 2:
        errors.append(f"Only {len(personas)} personas (need 2+)")
    for i, p in enumerate(personas):
        for field in ["name", "role_context", "goals", "frustrations"]:
            if not p.get(field):
                errors.append(f"Persona {i+1} missing {field}")

    metrics = data.get("success_metrics", {})
    if not metrics.get("north_star"):
        errors.append("Missing north star metric")
    if len(metrics.get("secondary", [])) < 2:
        errors.append("Need at least 2 secondary metrics")

    return len(errors) == 0, errors


def validate_phase4(output_dir: Path) -> Tuple[bool, List[str]]:
    """Validate Phase 4: Feature definition output."""
    errors = []
    data = load_json(output_dir / "phase4_features.json")
    if not data:
        return False, ["phase4_features.json not found"]

    features = data.get("features", [])
    if len(features) < 5:
        errors.append(f"Only {len(features)} features (expected 5+)")

    mvp = data.get("mvp_boundary", {})
    must_have = mvp.get("must_have", [])
    if len(must_have) < 3:
        errors.append(f"Only {len(must_have)} MVP features (expected 3+)")

    # Check all MVP features exist in feature list
    feature_ids = {f["id"] for f in features}
    for fid in must_have:
        if fid not in feature_ids:
            errors.append(f"MVP feature {fid} not in feature inventory")

    # Check RICE scores
    for f in features:
        rice = f.get("rice", {})
        if rice.get("effort_weeks", 0) <= 0:
            errors.append(f"Feature {f.get('id')} has invalid effort estimate")

    return len(errors) == 0, errors


def validate_phase5(output_dir: Path) -> Tuple[bool, List[str]]:
    """Validate Phase 5: Epic definition output."""
    errors = []
    data = load_json(output_dir / "phase5_epics.json")
    if not data:
        return False, ["phase5_epics.json not found"]

    epics = data.get("epics", [])
    if len(epics) < 2:
        errors.append(f"Only {len(epics)} epics (expected 2+)")

    for epic in epics:
        eid = epic.get("id", "unknown")
        if not epic.get("acceptance_criteria"):
            errors.append(f"Epic {eid} has no acceptance criteria")
        elif len(epic["acceptance_criteria"]) < 3:
            errors.append(f"Epic {eid} has only {len(epic['acceptance_criteria'])} AC (need 3+)")
        if not epic.get("user_story"):
            errors.append(f"Epic {eid} missing user story")

    return len(errors) == 0, errors


def validate_stories(output_dir: Path) -> Tuple[bool, List[str]]:
    """Validate Phase 6: Story files and cross-epic consistency."""
    errors = []
    story_files = list(output_dir.glob("phase6_stories_*.json"))
    if not story_files:
        return False, ["No story files found (phase6_stories_*.json)"]

    all_story_ids = set()
    total_points = 0
    for sf in story_files:
        data = load_json(sf)
        stories = data.get("stories", [])
        if not stories:
            errors.append(f"{sf.name} has no stories")
            continue

        for story in stories:
            sid = story.get("id", "unknown")
            if sid in all_story_ids:
                errors.append(f"Duplicate story ID: {sid}")
            all_story_ids.add(sid)

            if not story.get("acceptance_criteria"):
                errors.append(f"Story {sid} has no acceptance criteria")
            if not story.get("user_story"):
                errors.append(f"Story {sid} missing user story statement")
            if not story.get("story_points"):
                errors.append(f"Story {sid} missing story points")
            else:
                total_points += story["story_points"]

    # Check for circular dependencies
    dep_graph = {}
    for sf in story_files:
        data = load_json(sf)
        for story in data.get("stories", []):
            sid = story.get("id")
            blocked_by = story.get("dependencies", {}).get("blocked_by", [])
            dep_graph[sid] = blocked_by

    # Simple cycle detection
    def has_cycle(node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)
        for dep in dep_graph.get(node, []):
            if dep not in visited:
                if has_cycle(dep, visited, rec_stack):
                    return True
            elif dep in rec_stack:
                return True
        rec_stack.discard(node)
        return False

    visited = set()
    for node in dep_graph:
        if node not in visited:
            if has_cycle(node, visited, set()):
                errors.append("Circular dependency detected in story graph")
                break

    return len(errors) == 0, errors


def validate_feature_coverage(output_dir: Path) -> Tuple[bool, List[str]]:
    """Validate that all MVP features are covered by stories."""
    errors = []
    features_data = load_json(output_dir / "phase4_features.json")
    mvp_features = set(features_data.get("mvp_boundary", {}).get("must_have", []))

    if not mvp_features:
        return True, []  # Can't validate without features

    epics_data = load_json(output_dir / "phase5_epics.json")
    covered_features = set()
    for epic in epics_data.get("epics", []):
        for f in epic.get("features_included", []):
            fid = f.get("id") if isinstance(f, dict) else f
            covered_features.add(fid)

    missing = mvp_features - covered_features
    if missing:
        errors.append(f"MVP features not covered by any epic: {', '.join(missing)}")

    return len(errors) == 0, errors


def main():
    if len(sys.argv) < 3 or sys.argv[1] != "--dir":
        print("Usage: python3 validate_pipeline.py --dir <output_directory>")
        sys.exit(1)

    output_dir = Path(sys.argv[2])
    if not output_dir.exists():
        print(f"ERROR: Directory not found: {output_dir}")
        sys.exit(1)

    print(f"Validating pipeline artifacts in: {output_dir}\n")

    validators = [
        ("Phase 1: Research", validate_phase1),
        ("Phase 2: Problem Frame", validate_phase2),
        ("Phase 4: Features", validate_phase4),
        ("Phase 5: Epics", validate_phase5),
        ("Phase 6: Stories", validate_stories),
        ("Cross-Phase: Feature Coverage", validate_feature_coverage),
    ]

    total_errors = 0
    total_passed = 0
    for name, validator in validators:
        passed, errors = validator(output_dir)
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if errors:
            for err in errors:
                print(f"         - {err}")
            total_errors += len(errors)
        else:
            total_passed += 1

    print(f"\nResults: {total_passed}/{len(validators)} passed, {total_errors} total errors")
    sys.exit(0 if total_errors == 0 else 1)


if __name__ == "__main__":
    main()
