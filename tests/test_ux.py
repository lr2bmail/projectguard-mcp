from projectguard_mcp.reviewers.ux import review_ux_checklist


def test_all_states_missing_fails():
    result = review_ux_checklist(
        has_mobile_layout=False,
        has_clear_primary_action=False,
        has_empty_states=False,
        has_error_states=False,
        has_loading_states=False,
        has_accessible_labels=False,
    )
    assert result["approved"] is False
    codes = {f["code"] for f in result["findings"]}
    assert "MOBILE_LAYOUT_MISSING" in codes
    assert "ERROR_STATES_MISSING" in codes
    assert len(result["findings"]) == 6


def test_all_states_present_passes():
    result = review_ux_checklist(
        has_mobile_layout=True,
        has_clear_primary_action=True,
        has_empty_states=True,
        has_error_states=True,
        has_loading_states=True,
        has_accessible_labels=True,
    )
    assert result["approved"] is True
    assert result["score"] == 100


def test_partial_states_scores_between():
    result = review_ux_checklist(
        has_mobile_layout=True,
        has_clear_primary_action=True,
        has_empty_states=False,
        has_error_states=True,
        has_loading_states=True,
        has_accessible_labels=False,
    )
    assert result["approved"] is False
    assert 0 < result["score"] < 100


def test_notes_in_metadata():
    result = review_ux_checklist(
        has_mobile_layout=True,
        has_clear_primary_action=True,
        has_empty_states=True,
        has_error_states=True,
        has_loading_states=True,
        has_accessible_labels=True,
        notes="Using CSS Grid for mobile layout",
    )
    assert result["metadata"]["notes"] == "Using CSS Grid for mobile layout"
