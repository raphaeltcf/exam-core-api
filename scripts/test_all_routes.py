from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request


def http_request(method: str, url: str, body_json=None, body_raw: str | bytes | None = None, headers=None):
    if headers is None:
        headers = {}
    data = None
    if body_raw is not None:
        data = body_raw.encode("utf-8") if isinstance(body_raw, str) else body_raw
    elif body_json is not None:
        data = json.dumps(body_json).encode("utf-8")
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url=url, data=data, method=method.upper())
    req.add_header("Accept", "application/json")
    for k, v in headers.items():
        req.add_header(k, v)

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            raw = resp.read()
            text = raw.decode("utf-8", errors="replace")
            return resp.status, text
    except urllib.error.HTTPError as e:
        raw = e.read()
        text = raw.decode("utf-8", errors="replace")
        return e.code, text
    except Exception as e:
        return 0, str(e)


def try_json(text: str):
    try:
        return json.loads(text)
    except Exception:
        return None


def show(name: str, status: int, text: str, expect=None):
    parsed = try_json(text)
    payload = parsed if parsed is not None else text
    ok = True if expect is None else (status == expect)
    tag = "OK" if ok else "FAIL"
    line = f"[{tag}] {name} -> {status}"
    print(line)
    if not ok:
        print(payload)


def join(base: str, path: str) -> str:
    return base.rstrip("/") + "/" + path.lstrip("/")


def main() -> int:
    base = os.environ.get("BASE_URL", "http://localhost:8000/api/v1")
    ok = False
    last_status = 0
    last_text = ""
    for _ in range(20):
        last_status, last_text = http_request("GET", join(base, "/exams/"))
        if last_status != 0:
            ok = True
            break
        time.sleep(0.5)
    if not ok:
        print(f"API indisponível em {base}")
        print(last_text)
        return 2

    ts = int(time.time())
    email = f"aluno{ts}@x.com"
    email2 = f"aluno_sem_prova{ts}@x.com"

    q1 = {
        "content": f"Pergunta 1 ({ts})",
        "alternatives": [
            {"content": "Alt A", "option": 1, "is_correct": False},
            {"content": "Alt B", "option": 2, "is_correct": True},
            {"content": "Alt C", "option": 3, "is_correct": False},
        ],
    }
    q2 = {
        "content": f"Pergunta 2 ({ts})",
        "alternatives": [
            {"content": "Alt A", "option": 1, "is_correct": True},
            {"content": "Alt B", "option": 2, "is_correct": False},
            {"content": "Alt C", "option": 3, "is_correct": False},
        ],
    }

    status, text = http_request("POST", join(base, "/questions/"), body_json=q1)
    show("POST /questions (q1)", status, text, expect=201)
    q1_id = (try_json(text) or {}).get("id")

    status, text = http_request("POST", join(base, "/questions/"), body_json=q2)
    show("POST /questions (q2)", status, text, expect=201)
    q2_id = (try_json(text) or {}).get("id")

    if not q1_id or not q2_id:
        print("Falhou ao criar questões; abortando.")
        return 1

    status, text = http_request("GET", join(base, "/questions/"))
    show("GET /questions", status, text, expect=200)

    status, text = http_request("PATCH", join(base, f"/questions/{q1_id}/"), body_json={"content": f"Pergunta 1 editada ({ts})"})
    show("PATCH /questions/{id}", status, text, expect=200)

    status, text = http_request("POST", join(base, f"/questions/{q1_id}/alternatives/abc/mark-correct/"), body_json={})
    show("POST /questions/{id}/alternatives/abc/mark-correct (alt_id inválido)", status, text, expect=400)

    exam_body = {"name": f"Prova ({ts})", "question_ids": [q1_id, q2_id]}
    status, text = http_request("POST", join(base, "/exams/"), body_json=exam_body)
    show("POST /exams", status, text, expect=201)
    exam_id = (try_json(text) or {}).get("id")
    if not exam_id:
        print("Falhou ao criar exame; abortando.")
        return 1

    status, text = http_request("GET", join(base, "/exams/"))
    show("GET /exams", status, text, expect=200)

    status, text = http_request("GET", join(base, f"/exams/{exam_id}/"))
    show("GET /exams/{id}", status, text, expect=200)

    status, text = http_request("GET", join(base, "/exams/abc/"))
    show("GET /exams/abc (id inválido)", status, text, expect=404)

    status, text = http_request("PATCH", join(base, f"/exams/{exam_id}/"), body_json={"question_ids": [q1_id, 999999]})
    show("PATCH /exams/{id} (question_id inexistente)", status, text, expect=400)

    status, text = http_request("PATCH", join(base, f"/exams/{exam_id}/"), body_json={"question_ids": [q1_id, q1_id]})
    show("PATCH /exams/{id} (question_ids duplicados)", status, text, expect=400)

    status, text = http_request("DELETE", join(base, f"/exams/{exam_id}/remove-question/abc/"))
    show("DELETE /exams/{id}/remove-question/abc (question_id inválido)", status, text, expect=400)

    status, text = http_request("POST", join(base, "/exam-answers/submit/"), body_raw="{", headers={"Content-Type": "application/json"})
    show("POST /exam-answers/submit (JSON quebrado)", status, text, expect=400)

    status, text = http_request(
        "POST",
        join(base, "/exam-answers/submit/"),
        body_raw=json.dumps({"email": "email-invalido", "exam_id": exam_id, "answers": {"1": "A", "2": "A"}}),
        headers={"Content-Type": "application/json"},
    )
    show("POST /exam-answers/submit (email inválido)", status, text, expect=400)

    status, text = http_request(
        "POST",
        join(base, "/exam-answers/submit/"),
        body_json={"email": email, "exam_id": 999999999, "answers": {"1": "A", "2": "A"}},
    )
    show("POST /exam-answers/submit (exam_id inexistente)", status, text, expect=404)

    status, text = http_request(
        "POST",
        join(base, "/exam-answers/submit/"),
        body_json={"email": email, "exam_id": exam_id, "answers": {"1": "A"}},
    )
    show("POST /exam-answers/submit (faltando respostas)", status, text, expect=400)

    status, text = http_request(
        "POST",
        join(base, "/exam-answers/submit/"),
        body_json={"email": email, "exam_id": exam_id, "answers": {"1": "A", "2": "Z"}},
    )
    show("POST /exam-answers/submit (opção inválida)", status, text, expect=400)

    status, text = http_request(
        "POST",
        join(base, "/exam-answers/submit/"),
        body_json={"email": email, "exam_id": exam_id, "answers": {"1": "B", "2": "A"}},
    )
    show("POST /exam-answers/submit (sucesso)", status, text, expect=201)

    status, text = http_request(
        "POST",
        join(base, "/exam-answers/submit/"),
        body_json={"email": email, "exam_id": exam_id, "answers": {"1": "B", "2": "A"}},
    )
    show("POST /exam-answers/submit (repetido)", status, text, expect=409)

    status, text = http_request("POST", join(base, "/exam-answers/"), body_json={"email": email, "exam_question_id": 1, "selected_alternative_id": 1})
    show("POST /exam-answers (bloqueado)", status, text, expect=405)

    status, text = http_request("PATCH", join(base, "/exam-answers/1/"), body_json={"selected_alternative_id": 1})
    show("PATCH /exam-answers/1 (bloqueado)", status, text, expect=405)

    status, text = http_request("GET", join(base, f"/exam-answers/result/?exam_id={exam_id}&email={email}"))
    show("GET /exam-answers/result (sucesso)", status, text, expect=200)

    status, text = http_request("GET", join(base, f"/exam-answers/result/?exam_id={exam_id}&email={email2}"))
    show("GET /exam-answers/result (email sem prova)", status, text, expect=404)

    status, text = http_request("GET", join(base, f"/exam-answers/result/?exam_id=abc&email={email}"))
    show("GET /exam-answers/result (exam_id inválido)", status, text, expect=400)

    status, text = http_request("GET", join(base, f"/exam-answers/result/?exam_id={exam_id}&email=email-invalido"))
    show("GET /exam-answers/result (email inválido)", status, text, expect=400)

    status, text = http_request("GET", join(base, "/exam-answers/?exam_id=abc"))
    show("GET /exam-answers/?exam_id=abc (param inválido)", status, text, expect=400)

    status, text = http_request("GET", join(base, "/exam-answers/by-exam/?exam_id=abc"))
    show("GET /exam-answers/by-exam (param inválido)", status, text, expect=400)

    status, text = http_request("GET", join(base, "/exam-answers/by-student/?student_id=abc"))
    show("GET /exam-answers/by-student (param inválido)", status, text, expect=400)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

