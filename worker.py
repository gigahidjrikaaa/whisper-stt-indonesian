import redis
from rq import Worker, Queue, Connection

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.models.whisper import get_model_manager
from app.services.transcription import TranscriptionService

# Setup logging and settings
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# Synchronously load the model for the worker
logger.info("Worker starting up, loading model...")
try:
    model_manager = get_model_manager()
    model_manager.load_model()
    logger.info("Model loaded successfully for worker.")
except Exception as e:
    logger.critical(f"Failed to load model in worker: {e}", exc_info=True)
    exit(1) # Exit if model fails to load

# Initialize the transcription service without a thread pool
transcription_service = TranscriptionService(use_thread_pool=False)

# Redis connection details
listen = ['default']
redis_host = settings.redis_host
redis_port = settings.redis_port

# Establish connection to Redis
conn = redis.from_url(f'redis://{redis_host}:{redis_port}')

def transcribe_job(file_path: str):
    """
    The job function that the RQ worker will execute.
    This function performs the transcription of a single audio file.
    """
    logger.info(f"Starting transcription job for: {file_path}")
    try:
        result = transcription_service.transcribe_file_from_path(file_path)
        logger.info(f"Finished transcription job for: {file_path}")
        return result
    except Exception as e:
        logger.error(f"Transcription job failed for {file_path}: {e}", exc_info=True)
        # Re-raising the exception will mark the job as failed in RQ
        raise

if __name__ == "__main__":
    with Connection(conn):
        # Create a worker that listens on the specified queues
        worker = Worker(map(Queue, listen))
        logger.info(f"RQ Worker starting... Listening on queues: {', '.join(listen)}")
        # The `work` method is blocking and will start processing jobs
        worker.work()