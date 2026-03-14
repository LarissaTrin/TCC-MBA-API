import pytest

from schemas.dashboard_schema import (
    DashboardCardSchema,
    ListDistribution,
    MyDayResponse,
    PendingApprovalsResponse,
    PriorityDistribution,
    ProjectStatsResponse,
    TagDistribution,
)


# ── ListDistribution ──────────────────────────────────────────────────────────


def test_list_distribution_schema():
    schema = ListDistribution(list_name="Backlog", is_final=False, count=10)
    assert schema.dict() == {
        "list_name": "Backlog",
        "is_final": False,
        "count": 10,
    }


def test_list_distribution_final_column():
    schema = ListDistribution(list_name="Concluído", is_final=True, count=5)
    assert schema.dict()["is_final"] is True
    assert schema.dict()["count"] == 5


# ── PriorityDistribution ──────────────────────────────────────────────────────


def test_priority_distribution_with_priority():
    schema = PriorityDistribution(priority=3, count=8)
    assert schema.dict() == {"priority": 3, "count": 8}


def test_priority_distribution_without_priority():
    schema = PriorityDistribution(count=5)
    result = schema.dict()
    # priority é None → filtrado pelo CustomBaseModel.dict()
    assert "priority" not in result
    assert result["count"] == 5


# ── TagDistribution ───────────────────────────────────────────────────────────


def test_tag_distribution_schema():
    schema = TagDistribution(tag_name="Bug", count=12)
    assert schema.dict() == {"tag_name": "Bug", "count": 12}


# ── ProjectStatsResponse ──────────────────────────────────────────────────────


def test_project_stats_response_full():
    schema = ProjectStatsResponse(
        total_cards=10,
        by_list=[ListDistribution(list_name="Backlog", is_final=False, count=10)],
        by_priority=[PriorityDistribution(priority=1, count=4)],
        by_tag=[TagDistribution(tag_name="Bug", count=2)],
        avg_completion_days=3.8,
    )
    result = schema.dict()
    assert result["total_cards"] == 10
    assert result["avg_completion_days"] == 3.8
    assert len(result["by_list"]) == 1
    assert len(result["by_priority"]) == 1
    assert len(result["by_tag"]) == 1


def test_project_stats_response_avg_completion_none():
    schema = ProjectStatsResponse(
        total_cards=0,
        by_list=[],
        by_priority=[],
        by_tag=[],
    )
    result = schema.dict()
    assert result["total_cards"] == 0
    # avg_completion_days é None → filtrado pelo CustomBaseModel.dict()
    assert "avg_completion_days" not in result


def test_project_stats_response_empty_lists():
    schema = ProjectStatsResponse(
        total_cards=0,
        by_list=[],
        by_priority=[],
        by_tag=[],
        avg_completion_days=None,
    )
    result = schema.dict()
    assert result["by_list"] == []
    assert result["by_priority"] == []
    assert result["by_tag"] == []


# ── DashboardCardSchema ───────────────────────────────────────────────────────


def test_dashboard_card_schema_required_fields():
    schema = DashboardCardSchema(
        id=1,
        card_number=1,
        title="Fix login bug",
        list_id=2,
        list_name="Em andamento",
        project_id=3,
        project_title="Meu Projeto",
    )
    result = schema.dict()
    assert result["id"] == 1
    assert result["card_number"] == 1
    assert result["title"] == "Fix login bug"
    assert result["list_id"] == 2
    assert result["list_name"] == "Em andamento"
    assert result["project_id"] == 3
    assert result["project_title"] == "Meu Projeto"
    # campos opcionais ausentes → filtrados
    assert "priority" not in result
    assert "date" not in result
    assert "completed_at" not in result
    assert "user" not in result


def test_dashboard_card_schema_with_priority():
    schema = DashboardCardSchema(
        id=2,
        card_number=5,
        title="Deploy release",
        list_id=3,
        list_name="A fazer",
        project_id=1,
        project_title="Release v2",
        priority=4,
    )
    result = schema.dict()
    assert result["priority"] == 4


# ── MyDayResponse ─────────────────────────────────────────────────────────────


def test_my_day_response_empty():
    schema = MyDayResponse(due_today=[], overdue=[])
    assert schema.dict() == {"due_today": [], "overdue": []}


# ── PendingApprovalsResponse ──────────────────────────────────────────────────


def test_pending_approvals_response_empty():
    schema = PendingApprovalsResponse(pending=[])
    assert schema.dict() == {"pending": []}
