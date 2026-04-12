from app.schemas.design import DesignInputPayload
from app.llm.consistency import analyze_input_consistency


def _base_input(**kwargs) -> DesignInputPayload:
    data = {
        "project_title": "Demo Project Title",
        "project_type": "api",
        "problem_statement": "We need a reliable backend for our product with clear scaling path.",
        "expected_users": "1000",
        "traffic_assumptions": "steady load under 100 rps peak",
        "budget_sensitivity": "medium",
        "preferred_stack": None,
        "constraints": "small team",
        "deployment_scope": "single-region",
        "data_sensitivity": "medium",
        "real_time_required": False,
        "mode": "product",
    }
    data.update(kwargs)
    return DesignInputPayload.model_validate(data)


def test_sqlite_large_scale_warning():
    inp = _base_input(
        preferred_stack="sqlite,fastapi",
        expected_users="100000 registered users worldwide",
        problem_statement="We will use SQLite for everything and serve 100000 users.",
    )
    w = analyze_input_consistency(inp)
    joined = " ".join(w)
    assert "SQLite" in joined
    assert "large" in joined.lower() or "50" in joined or "migration" in joined.lower()


def test_sqlite_multi_region_warning():
    inp = _base_input(
        deployment_scope="global",
        constraints="we rely on sqlite for primary storage",
        problem_statement="Global deployment with sqlite as primary store for all regions.",
    )
    w = analyze_input_consistency(inp)
    joined = " ".join(w).lower()
    assert "sqlite" in joined and ("global" in joined or "multi-region" in joined or "region" in joined)


def test_budget_vs_data_sensitivity():
    inp = _base_input(budget_sensitivity="high", data_sensitivity="critical")
    w = analyze_input_consistency(inp)
    assert any("budget" in x.lower() and "sensitivity" in x.lower() for x in w)
