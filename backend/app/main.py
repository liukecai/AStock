from __future__ import annotations

from contextlib import asynccontextmanager
from threading import Thread

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import db
from .api import router
from .config import settings
from .services.announcements import update_cninfo_announcements
from .services.demo import seed_demo_data
from .services.market import update_market_data
from .services.pipeline import run_signal_pipeline
from .services.rss_news import update_rss_news

from apscheduler.events import EVENT_JOB_ERROR
from .services.backup import backup_db

scheduler = BackgroundScheduler(timezone="Asia/Shanghai")


def job_error_listener(event):
    if event.exception:
        try:
            from .services.notifications import send_failure_notification
            send_failure_notification(
                job_name=event.job_id or "unknown_scheduler_job",
                error_message=str(event.exception)
            )
        except Exception as e:
            import sys
            print(f"Error in scheduler error listener: {e}", file=sys.stderr)


scheduler.add_listener(job_error_listener, EVENT_JOB_ERROR)


def refresh_all() -> None:
    update_market_data()
    update_cninfo_announcements()
    update_rss_news()
    run_signal_pipeline()


@asynccontextmanager
async def lifespan(_: FastAPI):
    db.init_db()
    if settings.demo_data:
        seed_demo_data()
        run_signal_pipeline()
    elif not db.latest_trade_date():
        Thread(target=refresh_all, name="initial-market-bootstrap", daemon=True).start()
    if settings.enable_scheduler:
        scheduler.add_job(
            update_market_data,
            "cron",
            hour=settings.market_update_hour,
            minute=settings.market_update_minute,
            id="daily-market-update",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            run_signal_pipeline,
            "cron",
            hour=settings.signal_update_hour,
            minute=settings.signal_update_minute,
            id="daily-signals",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            update_rss_news,
            "cron",
            hour="*",
            minute=settings.rss_update_minute,
            id="hourly-rss-news",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            run_signal_pipeline,
            "cron",
            hour="*",
            minute=min(settings.rss_update_minute + 10, 59),
            id="hourly-rss-signals",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            update_cninfo_announcements,
            "cron",
            hour=settings.news_update_hour,
            minute=settings.news_update_minute,
            id="daily-cninfo-update",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            run_signal_pipeline,
            "cron",
            hour=settings.news_update_hour,
            minute=min(settings.news_update_minute + 15, 59),
            id="nightly-news-signals",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.add_job(
            backup_db,
            "cron",
            hour="22",
            minute="0",
            id="daily-db-backup",
            replace_existing=True,
            max_instances=1,
        )
        scheduler.start()
    yield
    if scheduler.running:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="A股趋势与舆情融合量化选股 API",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
from .api_candidates import router as candidates_router
app.include_router(candidates_router)


@app.get("/")
def root() -> dict:
    return {"name": settings.app_name, "docs": "/docs", "health": "/api/health"}
