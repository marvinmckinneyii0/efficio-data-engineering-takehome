# Requirements and Assumptions

This document tracks the Efficio Data Engineering Technical Task requirements and the design decisions used in the implementation.

## Explicit Requirements

### General
- [x] Use Python.
- [x] Use version control.
- [x] Include relevant implementation context, decisions, and trade-offs in the README or code comments.

### Data Modelling
- [x] Design a relational database schema for the provided company data.
- [x] Minimize redundancy while enabling efficient querying.
- [x] Define appropriate primary key and foreign key relationships.
- [x] Support hierarchical company relationships such as parent-subsidiary linkages.
- [x] Provide an Entity-Relationship Diagram (ERD).

### Data Processing
- [x] Ingest `Data_blocks.json`.
- [x] Ingest `Family_tree.json`.
- [x] Perform a join/enrichment between the two sources.
- [x] Enrich the company record with hierarchy information such as `Parent_Company_ID`.
- [x] Save the processed output as a Parquet file.
- [x] Validate and appropriately handle missing or malformed fields.
- [x] Include logging.
- [x] Include error handling.
- [x] Include data checks.
- [x] Include continuous pipeline integration.
- [x] Design the implementation to handle large datasets efficiently.

### Quality Assurance
- [x] Write exactly one pytest unit test for the join/enrichment transformation logic.

### Scale
- [x] Add a clearly identified scaling section to the README.
- [x] Describe one or two concrete code changes for significantly larger JSON files and a larger number of companies.
- [x] Scaling recommendations do not require changing the underlying infrastructure.
- [x] Scaling changes are documented rather than implemented for the take-home.

## Working Assumptions and Design Decisions

### Identifier and Join Strategy
- [x] DUNS is the canonical company identifier used to join detailed company data to family-tree data.
- [x] DUNS is treated as a string to preserve leading zeroes.
- [x] Enrichment uses left-join semantics so detailed company records are preserved when hierarchy information is missing.

### Hierarchy
- [x] A company may have zero or one direct parent in the supplied hierarchy structure.
- [x] A global-ultimate/root company may legitimately have no parent.
- [x] A missing parent for a root company results in a null `Parent_Company_ID`, not an error.
- [x] Parent relationships are derived from `corporateLinkage.parent.duns`.
- [x] Child lists are not stored redundantly because child relationships can be derived from parent references.

### Output Grain
- [x] The primary Parquet output contains one row per detailed `Data_blocks.json` company record.
- [x] Family-tree data enriches the detailed record rather than expanding the output to every family-tree member.

### Missing and Invalid Data
- [x] Missing optional hierarchy values are represented as null rather than causing the detailed company record to be dropped.
- [x] Missing or malformed required identifiers are treated as validation failures.
- [x] Unresolved hierarchy references are surfaced through logging/data-quality checks.

### Data Model
- [x] The ERD represents a normalized logical relational model.
- [x] A physical relational database is not deployed because the task requires schema design and an ERD rather than database implementation.
- [x] The analytical Parquet output may be denormalized even though the proposed relational model is normalized.

### Implementation Scope
- [x] pandas is used for the supplied in-memory workload.
- [x] PyArrow is used for Parquet output.
- [x] Continuous pipeline integration is implemented with GitHub Actions.
- [x] Raw confidential JSON inputs remain outside version control.
- [x] Generated output files remain outside version control.