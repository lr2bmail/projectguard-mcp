from projectguard_mcp.scoring import final_project_score


def test_final_score_blocks_low_security():
    result = final_project_score(code_score=90, ux_score=90, security_score=70, seo_score=90)
    assert result["approved"] is False
    assert "security_score_below_minimum" in result["blocking_issues"]


def test_final_score_approves_good_scores():
    result = final_project_score(code_score=90, ux_score=90, security_score=90, seo_score=90, paid_launch_score=90)
    assert result["approved"] is True
