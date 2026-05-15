import pytest

from app.cache.semantic import (
    SemanticCacheUnavailable,
    SemanticEstimationCache,
    semantic_bucket,
)
from app.schemas.estimation import EstimationRequest, EstimationResult, ReferenceProject


def _request(**kwargs) -> EstimationRequest:
    data = {
        "description": "Build a web CRM with contacts, imports, roles, and dashboards.",
        "project_type": "web_saas",
        "detail_level": "medium",
        "output_format": "narrative",
    }
    data.update(kwargs)
    return EstimationRequest(**data)


def test_semantic_bucket_includes_prompt_and_options() -> None:
    base = semantic_bucket(_request(), "v1")
    v2 = semantic_bucket(_request(), "v2")
    detailed = semantic_bucket(_request(detail_level="detailed"), "v1")
    table = semantic_bucket(_request(output_format="phases_table"), "v1")
    assert base["prompt_version"] == "v1"
    assert v2 != base
    assert detailed != base
    assert table != base


def test_reference_projects_isolate_bucket() -> None:
    refs = [
        ReferenceProject(
            name="CRM Alpha",
            project_type="web_saas",
            short_description="Comparable CRM with role-based access.",
            comparable_scope="Auth, contacts, search.",
        )
    ]
    assert semantic_bucket(_request(reference_projects=refs), "v1") != semantic_bucket(
        _request(), "v1"
    )


def test_similarity_threshold_translates_to_distance(monkeypatch: pytest.MonkeyPatch) -> None:
    created = {}

    class _Vectorizer:
        def __init__(self, model):
            created["model"] = model

    class _Cache:
        def __init__(self, **kwargs):
            created.update(kwargs)

    import sys
    import types

    semantic_mod = types.ModuleType("redisvl.extensions.cache.llm.semantic")
    semantic_mod.SemanticCache = _Cache
    vectorize_mod = types.ModuleType("redisvl.utils.vectorize")
    vectorize_mod.OpenAITextVectorizer = _Vectorizer
    monkeypatch.setitem(sys.modules, "redisvl", types.ModuleType("redisvl"))
    monkeypatch.setitem(sys.modules, "redisvl.extensions", types.ModuleType("redisvl.extensions"))
    monkeypatch.setitem(
        sys.modules, "redisvl.extensions.cache", types.ModuleType("redisvl.extensions.cache")
    )
    monkeypatch.setitem(
        sys.modules,
        "redisvl.extensions.cache.llm",
        types.ModuleType("redisvl.extensions.cache.llm"),
    )
    monkeypatch.setitem(sys.modules, "redisvl.extensions.cache.llm.semantic", semantic_mod)
    monkeypatch.setitem(sys.modules, "redisvl.utils", types.ModuleType("redisvl.utils"))
    monkeypatch.setitem(sys.modules, "redisvl.utils.vectorize", vectorize_mod)

    cache = SemanticEstimationCache(
        redis_url="redis://localhost:6379",
        embedding_model="text-embedding-3-small",
        similarity_threshold=0.87,
        ttl=60,
        log_only=True,
    )
    assert cache.distance_threshold == pytest.approx(0.13)
    assert created["distance_threshold"] == pytest.approx(0.13)
    assert created["model"] == "text-embedding-3-small"


def test_semantic_cache_degrades_when_redisvl_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    import builtins

    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name.startswith("redisvl"):
            raise ImportError("no redisvl")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(SemanticCacheUnavailable):
        SemanticEstimationCache(
            redis_url="redis://localhost:6379",
            embedding_model="text-embedding-3-small",
            similarity_threshold=0.87,
            ttl=60,
            log_only=True,
        )


def test_get_uses_redisvl_filter_expression() -> None:
    calls = {}
    result = EstimationResult(
        summary="CRM MVP.",
        total_duration_weeks=2,
        total_cost_eur=4000,
        confidence_pct=80,
        phases=[
            {
                "name": "Build",
                "duration_weeks": 2,
                "cost_eur": 4000,
                "confidence_pct": 80,
                "assumptions": ["Small team."],
            },
        ],
    )

    class _Cache:
        def check(self, **kwargs):
            calls.update(kwargs)
            return [{"distance": 0.05, "response": result.model_dump_json()}]

    cache = SemanticEstimationCache.__new__(SemanticEstimationCache)
    cache.distance_threshold = 0.13
    cache.log_only = False
    cache._cache = _Cache()

    assert cache.get(request=_request(), prompt_version="v1") == result
    assert "filter_expression" in calls
    assert "filters" not in calls
    assert "@prompt_version:{v1}" in str(calls["filter_expression"])
