from unittest.mock import patch

from backend.agents.orchestrator import summarize_with_agents


class DummyRequest:
    def __init__(
        self,
        *,
        text="hello",
        model="google/gemma-3-27b-it:free",
        chunk_size_1=100,
        chunk_overlap_1=0,
        chunk_size_2=0,
        chunk_overlap_2=0,
        token_max=4000,
        use_map=True,
        test_mode=False,
        map_temple=None,
        reduce_temple=None,
        reduce_temperature=0.0,
    ):
        self.text = text
        self.model = model
        self.chunk_size_1 = chunk_size_1
        self.chunk_overlap_1 = chunk_overlap_1
        self.chunk_size_2 = chunk_size_2
        self.chunk_overlap_2 = chunk_overlap_2
        self.token_max = token_max
        self.use_map = use_map
        self.test_mode = test_mode
        self.map_temple = map_temple
        self.reduce_temple = reduce_temple
        self.reduce_temperature = reduce_temperature


def test_orchestrator_test_mode_short_circuit():
    req = DummyRequest(test_mode=True)

    with patch("backend.agents.orchestrator.generate_summary") as mock_gen:
        mock_gen.return_value = "TEST_SUMMARY"
        summary, meta = summarize_with_agents(
            request=req,
            agent_mode="on",
            quality_check=True,
            max_iters=1,
        )

    assert summary == "TEST_SUMMARY"
    assert meta["mode"] == "test_mode"
    mock_gen.assert_called_once()


def test_orchestrator_applies_plan_overrides_params():
    req = DummyRequest(text="some long text", chunk_size_1=100, chunk_size_2=100)

    with patch("backend.agents.orchestrator.plan_parameters") as mock_plan, patch(
        "backend.agents.orchestrator.generate_summary"
    ) as mock_gen:
        mock_plan.return_value = type(
            "Plan",
            (),
            {
                "use_map": False,
                "chunk_size_1": 1234,
                "chunk_overlap_1": 12,
                "chunk_size_2": 0,
                "chunk_overlap_2": 0,
                "token_max": 9999,
                "reduce_temperature": 0.1,
                "model": None,
                "map_template": None,
                "reduce_template": None,
                "notes": "ok",
                "to_dict": lambda self: {},
            },
        )()
        mock_gen.return_value = "DRAFT"

        summary, meta = summarize_with_agents(
            request=req,
            agent_mode="on",
            quality_check=False,
            max_iters=0,
        )

    assert summary == "DRAFT"
    assert meta["effective_params"]["use_map"] is False
    assert meta["effective_params"]["chunk_size_1"] == 1234
    assert meta["effective_params"]["chunk_overlap_1"] == 12
    assert meta["effective_params"]["chunk_size_2"] == 0
    assert meta["effective_params"]["token_max"] == 9999


def test_orchestrator_review_revises_summary():
    req = DummyRequest(text="t", chunk_size_2=0)

    with patch("backend.agents.orchestrator.plan_parameters") as mock_plan, patch(
        "backend.agents.orchestrator.generate_summary"
    ) as mock_gen, patch("backend.agents.orchestrator.review_summary") as mock_review:
        mock_plan.return_value = type(
            "Plan",
            (),
            {
                "use_map": None,
                "chunk_size_1": None,
                "chunk_overlap_1": None,
                "chunk_size_2": None,
                "chunk_overlap_2": None,
                "token_max": None,
                "reduce_temperature": None,
                "model": None,
                "map_template": None,
                "reduce_template": None,
                "notes": None,
                "to_dict": lambda self: {},
            },
        )()
        mock_gen.return_value = "DRAFT"
        mock_review.return_value = type(
            "Review",
            (),
            {
                "verdict": "revise",
                "revised_summary": "REVISED",
                "issues": ["x"],
                "notes": "n",
                "to_dict": lambda self: {},
            },
        )()

        summary, meta = summarize_with_agents(
            request=req,
            agent_mode="on",
            quality_check=True,
            max_iters=1,
        )

    assert summary == "REVISED"
    assert meta["review"] is not None
