from app.schemas.design import DesignInputPayload, DesignOutputPayload
from app.llm.fallback import build_fallback_output
from app.llm.output_finalize import finalize_design_output


def _sample_input() -> DesignInputPayload:
    return DesignInputPayload.model_validate(
        {
            "project_title": "Demo Project Title",
            "project_type": "api",
            "problem_statement": "We need a reliable backend for our product with clear scaling path.",
            "expected_users": "75000",
            "traffic_assumptions": "steady load under 100 rps peak",
            "budget_sensitivity": "medium",
            "preferred_stack": "sqlite,python",
            "constraints": "small team",
            "deployment_scope": "single-region",
            "data_sensitivity": "medium",
            "real_time_required": False,
            "mode": "product",
        }
    )


def test_finalize_merges_diagram_and_consistency_warnings():
    inp = _sample_input()
    base = build_fallback_output(inp)
    data = base.model_dump()
    data["suggested_mermaid_diagram"] = "not_a_diagram_type\n  x --> y"
    data["consistency_warnings"] = ["Custom prior warning"]

    out = finalize_design_output(DesignOutputPayload.model_validate(data), inp)

    assert any("Custom prior warning" in w for w in out.consistency_warnings)
    assert any("[Diagram]" in w for w in out.consistency_warnings)
    assert any("SQLite" in w for w in out.consistency_warnings)
