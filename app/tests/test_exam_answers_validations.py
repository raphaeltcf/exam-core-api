import pytest

from exam.models import Exam
from question.models import Question, Alternative


@pytest.mark.django_db
def test_submit_invalid_json_returns_400(api_client):
    resp = api_client.generic(
        "POST",
        "/api/v1/exam-answers/submit/",
        data="{",
        content_type="application/json",
    )
    assert resp.status_code == 400
    assert resp.data["detail"] == "JSON inválido."


@pytest.mark.django_db
def test_submit_exam_id_not_found_returns_404(api_client):
    resp = api_client.post(
        "/api/v1/exam-answers/submit/",
        {"email": "a@a.com", "exam_id": 99999999, "answers": {"1": "A"}},
        format="json",
    )
    assert resp.status_code == 404


@pytest.mark.django_db
def test_submit_requires_all_answers(api_client):
    q1 = Question.objects.create(content="Q1")
    Alternative.objects.create(question=q1, content="A", option=1, is_correct=True)
    q2 = Question.objects.create(content="Q2")
    Alternative.objects.create(question=q2, content="A", option=1, is_correct=True)
    exam = Exam.objects.create(name="Prova")
    exam.questions.add(q1, through_defaults={"number": 1})
    exam.questions.add(q2, through_defaults={"number": 2})

    resp = api_client.post(
        "/api/v1/exam-answers/submit/",
        {"email": "aluno@x.com", "exam_id": exam.id, "answers": {"1": "A"}},
        format="json",
    )
    assert resp.status_code == 400
    assert "missing_numbers" in resp.data


@pytest.mark.django_db
def test_submit_invalid_option(api_client):
    q1 = Question.objects.create(content="Q1")
    Alternative.objects.create(question=q1, content="A", option=1, is_correct=True)
    exam = Exam.objects.create(name="Prova")
    exam.questions.add(q1, through_defaults={"number": 1})

    resp = api_client.post(
        "/api/v1/exam-answers/submit/",
        {"email": "aluno@x.com", "exam_id": exam.id, "answers": {"1": "Z"}},
        format="json",
    )
    assert resp.status_code == 400


@pytest.mark.django_db
def test_exam_answers_crud_is_blocked(api_client):
    resp = api_client.post(
        "/api/v1/exam-answers/",
        {"email": "a@a.com", "exam_question_id": 1, "selected_alternative_id": 1},
        format="json",
    )
    assert resp.status_code == 405

    resp = api_client.patch("/api/v1/exam-answers/1/", {"selected_alternative_id": 1}, format="json")
    assert resp.status_code == 405

