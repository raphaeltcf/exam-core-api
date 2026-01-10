import pytest

from question.models import Question, Alternative


@pytest.mark.django_db
def test_e2e_create_questions_exam_submit_and_result(api_client):
    q1 = Question.objects.create(content="Q1")
    Alternative.objects.create(question=q1, content="A", option=1, is_correct=False)
    Alternative.objects.create(question=q1, content="B", option=2, is_correct=True)

    q2 = Question.objects.create(content="Q2")
    Alternative.objects.create(question=q2, content="A", option=1, is_correct=True)
    Alternative.objects.create(question=q2, content="B", option=2, is_correct=False)

    resp = api_client.post(
        "/api/v1/exams/",
        {"name": "Prova", "question_ids": [q1.id, q2.id]},
        format="json",
    )
    assert resp.status_code == 201
    exam_id = resp.data["id"]

    resp = api_client.get(f"/api/v1/exams/{exam_id}/")
    assert resp.status_code == 200
    assert "questions" in resp.data
    for eq in resp.data["questions"]:
        for alt in eq["question"]["alternatives"]:
            assert "is_correct" not in alt

    email = "aluno@x.com"
    resp = api_client.post(
        "/api/v1/exam-answers/submit/",
        {"email": email, "exam_id": exam_id, "answers": {"1": "B", "2": "A"}},
        format="json",
    )
    assert resp.status_code == 201
    assert resp.data["correct_answers"] == 2
    assert resp.data["score_percentage"] == 100.0
    for ans in resp.data["answers"]:
        assert ans["correct_alternative"] is not None
        assert "option_display" in ans["correct_alternative"]

    resp = api_client.get(f"/api/v1/exam-answers/result/?exam_id={exam_id}&email={email}")
    assert resp.status_code == 200
    assert resp.data["correct_answers"] == 2
    assert resp.data["score_percentage"] == 100.0

