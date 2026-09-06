from src.pipeline import enrich_company_record


def test_enrich_company_record():
    """
    Verify hierarchy enrichment and left-join behavior using synthetic data.

    One child company should receive its direct parent, while a company
    without a matching hierarchy record should still be preserved with
    null hierarchy values.
    """
    family_tree = {
        "globalUltimateDuns": "000000001",
        "familyTreeMembers": [
            {
                "duns": "000000001",
                "corporateLinkage": {
                    "hierarchyLevel": 1,
                },
            },
            {
                "duns": "000000002",
                "corporateLinkage": {
                    "hierarchyLevel": 2,
                    "parent": {
                        "duns": "000000001",
                    },
                },
            },
        ],
    }

    child_company = {
        "duns": "000000002",
        "primaryName": "Child Company",
    }

    enriched_child = enrich_company_record(
        child_company,
        family_tree,
        "synthetic_test",
    )

    assert enriched_child["Company_ID"] == "000000002"
    assert enriched_child["Parent_Company_ID"] == "000000001"
    assert enriched_child["Hierarchy_Level"] == 2
    assert enriched_child["Global_Ultimate_ID"] == "000000001"

    unmatched_company = {
        "duns": "000000003",
        "primaryName": "Unmatched Company",
    }

    enriched_unmatched = enrich_company_record(
        unmatched_company,
        family_tree,
        "synthetic_test",
    )

    assert enriched_unmatched["Company_ID"] == "000000003"
    assert enriched_unmatched["Parent_Company_ID"] is None
    assert enriched_unmatched["Hierarchy_Level"] is None