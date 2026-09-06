import json
import logging
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "output"
OUTPUT_FILE = OUTPUT_DIR / "company_enriched.parquet"


# Keep logging simple and useful for both local execution and CI.
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)


COMPANY_FOLDERS = [
    DATA_DIR / "company_a",
    DATA_DIR / "company_b",
    DATA_DIR / "company_c",
]


def load_json(path: Path) -> dict:
    """Load a JSON file and fail clearly when the source cannot be parsed."""
    if not path.exists():
        raise FileNotFoundError(f"Required input file not found: {path}")

    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed JSON in {path}: {exc}") from exc

    if not isinstance(data, dict):
        raise ValueError(
            f"Expected top-level JSON object in {path}, "
            f"got {type(data).__name__}"
        )

    return data


def validate_required_duns(value, source_name: str) -> str:
    """
    Validate the required company identifier.

    DUNS is stored as a string because leading zeroes are significant.
    """
    if value is None:
        raise ValueError(f"Missing required DUNS in {source_name}")

    duns = str(value).strip()

    if not duns:
        raise ValueError(f"Blank required DUNS in {source_name}")

    return duns


def build_hierarchy_lookup(family_tree: dict, source_name: str) -> dict:
    """
    Build a lookup keyed by company DUNS containing direct-parent
    and hierarchy information from Family_tree.json.
    """
    members = family_tree.get("familyTreeMembers") or []

    if not isinstance(members, list):
        raise ValueError(
            f"{source_name}: familyTreeMembers must be a list"
        )

    hierarchy_lookup = {}

    for member in members:
        if not isinstance(member, dict):
            logger.warning(
                "%s: skipping malformed family-tree member",
                source_name,
            )
            continue

        raw_duns = member.get("duns")

        if raw_duns is None:
            logger.warning(
                "%s: skipping family-tree member with missing DUNS",
                source_name,
            )
            continue

        member_duns = str(raw_duns).strip()

        if member_duns in hierarchy_lookup:
            raise ValueError(
                f"{source_name}: duplicate family-tree DUNS {member_duns}"
            )

        corporate_linkage = member.get("corporateLinkage") or {}
        parent = corporate_linkage.get("parent") or {}

        parent_duns = parent.get("duns")
        if parent_duns is not None:
            parent_duns = str(parent_duns).strip()

        hierarchy_lookup[member_duns] = {
            "Parent_Company_ID": parent_duns,
            "Hierarchy_Level": corporate_linkage.get("hierarchyLevel"),
        }

    # Surface references to parents that were not returned in the response.
    returned_duns = set(hierarchy_lookup)

    unresolved_parents = {
        details["Parent_Company_ID"]
        for details in hierarchy_lookup.values()
        if details["Parent_Company_ID"] is not None
        and details["Parent_Company_ID"] not in returned_duns
    }

    if unresolved_parents:
        logger.warning(
            "%s: %d unresolved parent reference(s)",
            source_name,
            len(unresolved_parents),
        )

    return hierarchy_lookup

def enrich_company_record(
    data_blocks: dict,
    family_tree: dict,
    source_name: str,
) -> dict:
    """
    Enrich one detailed company record with hierarchy information.

    Left-join semantics preserve the detailed record when no matching
    hierarchy member is available.
    """
    company_duns = validate_required_duns(
        data_blocks.get("duns"),
        source_name,
    )

    hierarchy_lookup = build_hierarchy_lookup(
        family_tree,
        source_name,
    )

    hierarchy = hierarchy_lookup.get(
        company_duns,
        {
            "Parent_Company_ID": None,
            "Hierarchy_Level": None,
        },
    )

    global_ultimate_duns = family_tree.get("globalUltimateDuns")
    if global_ultimate_duns is not None:
        global_ultimate_duns = str(global_ultimate_duns).strip()

    return {
        "Company_ID": company_duns,
        "Company_Name": data_blocks.get("primaryName"),
        "Parent_Company_ID": hierarchy["Parent_Company_ID"],
        "Hierarchy_Level": hierarchy["Hierarchy_Level"],
        "Global_Ultimate_ID": global_ultimate_duns,
        "Source_Company": source_name,
    }


def process_company_folder(company_folder: Path) -> dict:
    """
    Load one company's detailed and hierarchy JSON files and return
    one enriched analytical record.
    """
    data_blocks_path = company_folder / "data_blocks.json"
    family_tree_path = company_folder / "family_tree.json"

    logger.info("Processing %s", company_folder.name)

    data_blocks = load_json(data_blocks_path)
    family_tree = load_json(family_tree_path)

    return enrich_company_record(
        data_blocks,
        family_tree,
        company_folder.name,
    )

    hierarchy_lookup = build_hierarchy_lookup(
        family_tree,
        str(family_tree_path),
    )

    # Left-join semantics: keep the detailed company record even if
    # no corresponding hierarchy record is available.
    hierarchy = hierarchy_lookup.get(
        company_duns,
        {
            "Parent_Company_ID": None,
            "Hierarchy_Level": None,
        },
    )

    global_ultimate_duns = family_tree.get("globalUltimateDuns")
    if global_ultimate_duns is not None:
        global_ultimate_duns = str(global_ultimate_duns).strip()

    return {
        "Company_ID": company_duns,
        "Company_Name": data_blocks.get("primaryName"),
        "Parent_Company_ID": hierarchy["Parent_Company_ID"],
        "Hierarchy_Level": hierarchy["Hierarchy_Level"],
        "Global_Ultimate_ID": global_ultimate_duns,
        "Source_Company": company_folder.name,
    }


def validate_output(df: pd.DataFrame, expected_rows: int) -> None:
    """Run simple data-quality checks before writing the Parquet output."""
    if len(df) != expected_rows:
        raise ValueError(
            f"Output row count {len(df)} does not match "
            f"expected row count {expected_rows}"
        )

    if df["Company_ID"].isna().any():
        raise ValueError("Output contains missing Company_ID values")

    if df["Company_ID"].duplicated().any():
        raise ValueError("Output contains duplicate Company_ID values")

    logger.info(
        "Data checks passed: %d rows, %d unique company IDs",
        len(df),
        df["Company_ID"].nunique(),
    )


def run_pipeline() -> pd.DataFrame:
    """Process all supplied company datasets and write enriched Parquet output."""
    records = []

    for company_folder in COMPANY_FOLDERS:
        records.append(process_company_folder(company_folder))

    df = pd.DataFrame(records)

    validate_output(df, expected_rows=len(COMPANY_FOLDERS))

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df.to_parquet(
        OUTPUT_FILE,
        engine="pyarrow",
        index=False,
    )

    logger.info("Parquet output written to %s", OUTPUT_FILE)

    return df


if __name__ == "__main__":
    try:
        result = run_pipeline()
        print("\nProcessed output:")
        print(result.to_string(index=False))
    except Exception:
        logger.exception("Pipeline failed")
        raise