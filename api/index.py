"""
Soite Feedback — self-contained demo backend for Vercel showcase.
No database or Redis required.
Demo credentials: admin@soite.fi / Demo1234!
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import FastAPI, Header, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

DEMO_SECRET = "soite-demo-2026-showcase-key"
DEMO_EMAIL = "admin@soite.fi"
DEMO_PASSWORD = "Demo1234!"

app = FastAPI(title="Soite Feedback API (demo)", docs_url="/api/docs", redoc_url=None)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

QUESTIONS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "text_fi": "Tunsitko, että sinua kuunneltiin ja sinua kohdeltiin kunnioittavasti?",
        "text_sv": "Kände du att du blev lyssnad på och behandlad med respekt?",
        "type": "face4",
        "order": 10,
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "text_fi": "Saitko tarvitsemaasi apua ja ohjausta jakson aikana?",
        "text_sv": "Fick du den hjälp och vägledning du behövde under perioden?",
        "type": "face4",
        "order": 20,
    },
    {
        "id": "33333333-3333-3333-3333-333333333333",
        "text_fi": "Koetko, että hoitoasi koskevat päätökset tehtiin yhteistyössä kanssasi?",
        "text_sv": "Fattades besluten om din vård i samarbete med dig?",
        "type": "face4",
        "order": 30,
    },
    {
        "id": "44444444-4444-4444-4444-444444444444",
        "text_fi": "Koetko, että toimintakykysi on parantunut jakson myötä?",
        "text_sv": "Upplever du att din funktionsförmåga har förbättrats under perioden?",
        "type": "face4",
        "order": 40,
    },
    {
        "id": "55555555-5555-5555-5555-555555555555",
        "text_fi": "Kuinka todennäköisesti suosittelisit palvelua vastaavassa tilanteessa olevalle?",
        "text_sv": "Hur sannolikt är det att du skulle rekommendera tjänsten till någon i en liknande situation?",
        "type": "face4",
        "order": 50,
    },
    {
        "id": "66666666-6666-6666-6666-666666666666",
        "text_fi": "Vapaa sana ja kehitysideat: Tähän voit kirjoittaa terveisiä työntekijöille tai parannusehdotuksia",
        "text_sv": "Fritt ord och utvecklingsidéer: Du kan skriva hälsningar till personalen eller förbättringsförslag",
        "type": "text",
        "order": 60,
    },
]

_submissions: list[dict[str, Any]] = []


def _make_token(email: str, minutes: int = 1440) -> str:
    exp = datetime.now(UTC) + timedelta(minutes=minutes)
    return jwt.encode({"sub": email, "role": "admin", "exp": exp}, DEMO_SECRET, algorithm="HS256")


def _verify_token(authorization: str | None) -> dict[str, Any]:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Unauthorized")
    try:
        return jwt.decode(authorization[7:], DEMO_SECRET, algorithms=["HS256"])  # type: ignore[no-any-return]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@app.get("/api/v1/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/v1/survey/questions")
async def get_questions() -> dict[str, Any]:
    return {
        "questions": QUESTIONS,
        "version": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


class FeedbackIn(BaseModel):
    submission_id: str
    answers: list[dict[str, Any]]


@app.post("/api/v1/feedback", status_code=200)
async def submit_feedback(
    payload: FeedbackIn,
    x_device_token: str | None = Header(default=None),
) -> dict[str, bool]:
    _submissions.append({
        "id": payload.submission_id,
        "ts": datetime.now(UTC).isoformat(),
        "answer_count": len(payload.answers),
    })
    return {"received": True}


class LoginIn(BaseModel):
    email: str
    password: str


@app.post("/api/v1/auth/login")
async def login(body: LoginIn) -> dict[str, Any]:
    if body.email != DEMO_EMAIL or body.password != DEMO_PASSWORD:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_CREDENTIALS", "message": "Invalid email or password"},
        )
    return {"access_token": _make_token(body.email), "token_type": "bearer", "expires_in": 86400}


@app.post("/api/v1/auth/refresh")
async def refresh(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    payload = _verify_token(authorization)
    return {"access_token": _make_token(payload["sub"]), "token_type": "bearer", "expires_in": 86400}


@app.post("/api/v1/auth/logout")
async def logout() -> dict[str, bool]:
    return {"ok": True}


_DEMO_STATS: dict[str, Any] = {
    "period": {"from_date": "2026-01-01", "to_date": "2026-05-20"},
    "total_submissions": 89,
    "by_question": [
        {
            "question_id": "11111111-1111-1111-1111-111111111111",
            "text_fi": "Miten arvioit saamasi palvelun kokonaisuudessaan?",
            "type": "face4",
            "counts": {"1": 2, "2": 5, "3": 20, "4": 62},
            "mean": 3.60,
            "total": None,
        },
        {
            "question_id": "22222222-2222-2222-2222-222222222222",
            "text_fi": "Kohteliko kotikuntoutustiimi sinua asiallisesti?",
            "type": "yesno",
            "counts": {"1": 85, "0": 4},
            "mean": None,
            "total": None,
        },
        {
            "question_id": "33333333-3333-3333-3333-333333333333",
            "text_fi": "Kuinka hyvin kotikuntoutus vastasi odotuksiasi?",
            "type": "scale5",
            "counts": {"1": 1, "2": 3, "3": 11, "4": 30, "5": 44},
            "mean": 4.27,
            "total": None,
        },
        {
            "question_id": "44444444-4444-4444-4444-444444444444",
            "text_fi": "Haluatko antaa lisäpalautetta?",
            "type": "text",
            "counts": None,
            "mean": None,
            "total": 33,
        },
    ],
}


@app.get("/api/v1/dashboard/summary")
async def dashboard_summary(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _verify_token(authorization)
    return _DEMO_STATS


@app.get("/api/v1/dashboard/freetext")
async def dashboard_freetext(authorization: str | None = Header(default=None)) -> dict[str, Any]:
    _verify_token(authorization)
    return {
        "total": 3,
        "page": 1,
        "items": [
            {"text": "Erittäin hyvää palvelua, tiimi on erittäin ammattitaitoinen!"},
            {"text": "Terapeutit olivat ystävällisiä ja kannustavia."},
            {"text": "Toivoisin hieman enemmän tietoa harjoitusohjelmasta."},
        ],
    }
