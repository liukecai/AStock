from fastapi import APIRouter

from .graph import router as graph_router
from .events import router as events_router
from .stocks import router as stocks_router
from .validation import router as validation_router
from .jobs import router as jobs_router
from .chat import router as chat_router
from .input import router as input_router

router = APIRouter(prefix="/api/v2")

router.include_router(graph_router, prefix="/graph", tags=["V2 Graph"])
router.include_router(events_router, prefix="/events", tags=["V2 Events"])
router.include_router(stocks_router, prefix="/stocks", tags=["V2 Stocks"])
router.include_router(validation_router, prefix="/validation", tags=["V2 Validation"])
router.include_router(jobs_router, prefix="/jobs", tags=["V2 Jobs"])
router.include_router(chat_router, prefix="/chat", tags=["V2 Chat"])
router.include_router(input_router, prefix="/input", tags=["V2 Input"])
