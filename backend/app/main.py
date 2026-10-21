from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.session import SessionLocal, get_db
from app.db.seed import seed_default_categories
from app.api.auth import router as auth_router
from app.api.months import router as months_router
from app.api.expenses import router as expenses_router
from app.api.obligations import router as obligations_router
from app.api.reports import router as reports_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    with SessionLocal() as db:
        seed_default_categories(db)
    yield


app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(months_router)
app.include_router(expenses_router)
app.include_router(obligations_router)
app.include_router(reports_router)


@app.get("/api/health")
def health_check(db: Session = Depends(get_db)):
    db.execute(text("SELECT 1"))
    return {
        "status": "ok",
        "app": settings.PROJECT_NAME,
        "currency": settings.CURRENCY,
        "timezone": settings.TIMEZONE,
    }
