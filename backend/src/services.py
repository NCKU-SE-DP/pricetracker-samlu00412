import sentry_sdk
from apscheduler.schedulers.background import BackgroundScheduler

sentry_sdk.init(
    dsn="https://dc598c98fc2a30ac872ac74fe9753121@o4508454796066816.ingest.us.sentry.io/4508454914490368",
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
)
Background_scheduler = BackgroundScheduler()
