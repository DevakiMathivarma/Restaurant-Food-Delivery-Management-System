from celery import Celery

from app.config import settings

celery_app = Celery(
    "food_delivery_platform",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True
)

# no scheduled beat job needed for this project - unlike property/
# insurance's daily due-date checks, nothing in this task's own
# requirements needs a recurring, time-triggered job. every
# notification here fires as a direct result of a real user action
# (order placed, status changed, payment made), not a clock