import json
from pathlib import Path


# Resolve paths relative to the repository root so the script works
# regardless of where the project is cloned.
PROJECT_ROOT = Path(__file__).resolve().parent.parent


COMPANIES = {
    "Company B": {
        "data_blocks": PROJECT_ROOT / "data" / "company_b" / "data_blocks.json",
        "family_tree": PROJECT_ROOT / "data" / "company_b" / "family_tree.json",
    },
    "Company C": {
        "data_blocks": PROJECT_ROOT / "data" / "company_c" / "data_blocks.json",
        "family_tree": PROJECT_ROOT / "data" / "company_c" / "family_tree.json",
    },
}


def load_json(path: Path) -> dict:
    """Load a JSON file into a native Python dictionary."""
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def profile_company(label: str, data_blocks_path: Path, family_tree_path: Path) -> None:
    """Profile the identifiers and hierarchy structure needed for the take-home."""

    data_blocks = load_json(data_blocks_path)
    family_tree = load_json(family_tree_path)

    # The hierarchy records are nested under familyTreeMembers.
    # Treat a missing or null collection as an empty list for profiling.
    family_tree_members = family_tree.get("familyTreeMembers") or []

    if not isinstance(family_tree_members, list):
        raise ValueError(
            f"{label}: expected familyTreeMembers to be a list, "
            f"got {type(family_tree_members).__name__}"
        )

    # DUNS is the candidate company identifier used for joining the sources.
    member_duns = [member.get("duns") for member in family_tree_members]

    missing_duns_count = sum(duns is None for duns in member_duns)
    non_null_duns = [duns for duns in member_duns if duns is not None]
    unique_duns_count = len(set(non_null_duns))
    duplicate_duns_count = len(non_null_duns) - unique_duns_count

    # Hierarchy level is nested inside corporateLinkage rather than
    # stored directly on each family-tree member.
    hierarchy_levels = [
        (member.get("corporateLinkage") or {}).get("hierarchyLevel")
        for member in family_tree_members
        if (member.get("corporateLinkage") or {}).get("hierarchyLevel") is not None
    ]

    # Extract direct parent identifiers while safely handling missing
    # or explicitly null corporateLinkage/parent objects.
    parent_duns = [
        (
            ((member.get("corporateLinkage") or {}).get("parent") or {})
            .get("duns")
        )
        for member in family_tree_members
    ]

    members_with_parent = sum(parent is not None for parent in parent_duns)
    members_without_parent = sum(parent is None for parent in parent_duns)

    # A referenced parent that is absent from the returned hierarchy
    # is useful to surface later as a data-quality condition.
    member_duns_set = set(non_null_duns)

    unresolved_parent_duns = {
        parent
        for parent in parent_duns
        if parent is not None and parent not in member_duns_set
    }

    print(f"\n{'=' * 50}")
    print(label)
    print(f"{'=' * 50}")

    print(f"Company DUNS: {data_blocks.get('duns')}")
    print(f"Company name: {data_blocks.get('primaryName')}")
    print(f"Global ultimate DUNS: {family_tree.get('globalUltimateDuns')}")

    print(
        f"Reported family members: "
        f"{family_tree.get('globalUltimateFamilyTreeMembersCount')}"
    )
    print(f"Returned family-tree members: {len(family_tree_members)}")

    print(f"Missing member DUNS: {missing_duns_count}")
    print(f"Unique member DUNS: {unique_duns_count}")
    print(f"Duplicate member DUNS: {duplicate_duns_count}")

    print(f"Hierarchy levels present: {sorted(set(hierarchy_levels))}")

    if hierarchy_levels:
        print(f"Minimum hierarchy level: {min(hierarchy_levels)}")
        print(f"Maximum hierarchy level: {max(hierarchy_levels)}")
    else:
        print("No hierarchy levels found.")

    print(f"Members with a direct parent: {members_with_parent}")
    print(f"Members without a direct parent: {members_without_parent}")
    print(f"Unresolved parent references: {len(unresolved_parent_duns)}")


for company_label, paths in COMPANIES.items():
    profile_company(
        company_label,
        paths["data_blocks"],
        paths["family_tree"],
    )