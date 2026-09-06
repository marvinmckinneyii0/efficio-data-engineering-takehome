# Requirements and Assumptions

This document tracks the explicit requirements from the Efficio Data Engineering Technical Task separately from working assumptions and design decisions.

## Explicit Requirements

### General
- [ ] Use Python.
- [x] Use version control.
- [ ] Include relevant implementation context, decisions, and trade-offs in the README or code comments.

### Data Modelling
- [ ] Design a relational database schema for the provided company data.
- [ ] Minimize redundancy while enabling efficient querying.
- [ ] Define appropriate primary key and foreign key relationships.
- [ ] Support hierarchical company relationships such as parent-subsidiary linkages.
- [ ] Provide an Entity-Relationship Diagram (ERD).

### Data Processing
- [ ] Ingest `Data_blocks.json`.
- [ ] Ingest `Family_tree.json`.
- [ ] Perform a join/enrichment between the two sources.
- [ ] Enrich the company record with hierarchy information such as `Parent_Company_ID`.
- [ ] Save the processed output as a Parquet file.
- [ ] Validate and appropriately handle missing or malformed fields.
- [ ] Include logging.
- [ ] Include error handling.
- [ ] Include data checks.
- [ ] Include continuous pipeline integration.
- [ ] Design the implementation to handle large datasets efficiently.

### Quality Assurance
- [ ] Write exactly one pytest unit test for the join/enrichment transformation logic.

### Scale
- [ ] Add a clearly identified scaling section to the README.
- [ ] Describe one or two concrete code changes for significantly larger JSON files and a larger number of companies.
- [ ] Scaling recommendations must not require changing the underlying infrastructure.
- [ ] The scaling changes do not need to be implemented for the take-home.

## Working Assumptions and Design Decisions

- [x] The enrichment will use a left join so every detailed company record is preserved even when hierarchy information is missing.

- [x] Parent relationships will be derived from each family-tree member's `corporateLinkage.parent.duns`.
- [x] Child lists will not be stored separately in the relational model when the same direct relationship can be derived from the parent reference.

- [x] The primary Parquet output will contain one row per detailed `Data_blocks.json` company record.
- [x] Family-tree data will enrich the detailed company record rather than expand the output to every family-tree member.

- [x] The ERD will represent a normalized logical relational model.
- [x] The take-home will not deploy a physical relational database because the brief asks for a schema design and ERD, not a database implementation.
- [x] The Parquet output may be denormalized even though the proposed relational model is normalized.

- [x] Use pandas for the in-memory transformation because it is sufficient for the supplied datasets and keeps the implementation simple.
- [x] Use PyArrow for Parquet output.
- [x] Interpret continuous pipeline integration as automated CI checks using GitHub Actions.

### Identifier and Join Strategy

- [x] DUNS is the canonical company identifier used to join the detailed company data to the family-tree data.
- [x] DUNS will be treated as a string rather than a numeric value to preserve leading zeroes.
- [ ] The enrichment will use a left join so every detailed company record is preserved even when hierarchy information is missing.

### Hierarchy

- [x] A company may have zero or one direct parent in the supplied family-tree structure.
- [x] A global-ultimate/root company may legitimately have no parent.
- [x] A missing parent for a root company is valid business data and should result in a null `Parent_Company_ID`, not an error.
- [ ] Parent relationships will be derived from each family-tree member's `corporateLinkage.parent.duns`.
- [ ] Child lists will not be stored separately in the relational model when the same direct relationship can be derived from the parent reference.

### Output Grain

- [ ] The primary Parquet output will contain one row per detailed `Data_blocks.json` company record.
- [ ] Family-tree data will enrich the detailed company record rather than expand the output to every family-tree member.

### Missing and Invalid Data

- [ ] Missing optional fields will normally be represented as null rather than causing a record to be dropped.
- [ ] Missing or malformed required identifiers will be treated as validation failures.
- [ ] Unresolved hierarchy references will be surfaced through logging/data-quality checks rather than silently discarded.

### Data Model

### Data Modelling
- [x] Design a relational database schema for the provided company data.
- [x] Minimize redundancy while enabling efficient querying.
- [x] Define appropriate primary key and foreign key relationships.
- [x] Support hierarchical company relationships such as parent-subsidiary linkages.
- [x] Provide an Entity-Relationship Diagram.

### Implementation Scope

- [ ] Use pandas for the in-memory transformation because it is sufficient for the supplied datasets and keeps the implementation simple.
- [ ] Use PyArrow for Parquet output.
- [ ] Interpret continuous pipeline integration as automated CI checks using GitHub Actions.
- [x] Raw confidential JSON inputs will remain outside version control.
- [x] Generated output files will remain outside version control.