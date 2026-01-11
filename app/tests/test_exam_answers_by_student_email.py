import pytest

from exam.models import Exam
from question.models import Question, Alternative


@pytest.mark.django_db
def test_by_student_email_returns_grouped_exams(api_client):
    # Exam 1
    q1 = Question.objects.create(content="Q1")
    Alternative.objects.create(question=q1, content="A", option=1, is_correct=False)
    Alternative.objects.create(question=q1, content="B", option=2, is_correct=True)

    q2 = Question.objects.create(content="Q2")
    Alternative.objects.create(question=q2, content="A", option=1, is_correct=True)
    Alternative.objects.create(question=q2, content="B", option=2, is_correct=False)

    exam1 = Exam.objects.create(name="Prova 1")
    exam1.questions.add(q1, through_defaults={"number": 1})
    exam1.questions.add(q2, through_defaults={"number": 2})

    # Exam 2
    q3 = Question.objects.create(content="Q3")
    Alternative.objects.create(question=q3, content="A", option=1, is_correct=True)
    Alternative.objects.create(question=q3, content="B", option=2, is_correct=False)

    exam2 = Exam.objects.create(name="Prova 2")
    exam2.questions.add(q3, through_defaults={"number": 1})

    email = "aluno@x.com"

    # Submit both exams
    resp = api_client.post(
        "/api/v1/exam-answers/submit/",
        {"email": email, "exam_id": exam1.id, "answers": {"1": "B", "2": "A"}},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["score_percentage"] == 100.0

    resp = api_client.post(
        "/api/v1/exam-answers/submit/",
        {"email": email, "exam_id": exam2.id, "answers": {"1": "A"}},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["score_percentage"] == 100.0

    # Fetch grouped list
    resp = api_client.get(f"/api/v1/exam-answers/by-student/?email={email}")
    assert resp.status_code == 200
    assert isinstance(resp.data, list)
    assert len(resp.data) == 2

    got_exam_ids = {row["exam_id"] for row in resp.data}
    assert got_exam_ids == {exam1.id, exam2.id}

    for row in resp.data:
        assert "score_percentage" in row
        assert "answers" in row
        assert isinstance(row["answers"], list)


@pytest.mark.django_db
def test_by_student_email_and_exam_id_returns_detailed(api_client):
    q1 = Question.objects.create(content="Q1")
    Alternative.objects.create(question=q1, content="A", option=1, is_correct=True)
    Alternative.objects.create(question=q1, content="B", option=2, is_correct=False)
    exam = Exam.objects.create(name="Prova")
    exam.questions.add(q1, through_defaults={"number": 1})

    email = "aluno@x.com"
    resp = api_client.post(
        "/api/v1/exam-answers/submit/",
        {"email": email, "exam_id": exam.id, "answers": {"1": "A"}},
        format="json",
    )
    assert resp.status_code == 201

    resp = api_client.get(f"/api/v1/exam-answers/by-student/?email={email}&exam_id={exam.id}")
    assert resp.status_code == 200
    assert isinstance(resp.data, dict)
    assert resp.data["exam_id"] == exam.id
    assert resp.data["student_email"] == email
    assert resp.data["score_percentage"] == 100.0


@pytest.mark.django_db
def test_by_student_invalid_email_returns_400(api_client):
    resp = api_client.get("/api/v1/exam-answers/by-student/?email=not-an-email")
    assert resp.status_code == 400


@pytest.mark.django_db
def test_by_student_nonexistent_email_returns_404(api_client):
    resp = api_client.get("/api/v1/exam-answers/by-student/?email=missing@email.com")
    assert resp.status_code == 404

