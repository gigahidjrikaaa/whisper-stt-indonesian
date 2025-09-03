import time
import os
from typing import List

from rq.job import Job
from rq import Queue

from app.core.config import get_settings
from app.core.logging import get_logger, setup_logging
from app.core.queue import get_queue, get_redis_connection
from app.models.whisper import get_model_manager
from app.services.transcription import TranscriptionService

# Setup
setup_logging()
logger = get_logger(__name__)
settings = get_settings()

# Load model and service
logger.info("Batch worker starting up, loading model...")
try:
    model_manager = get_model_manager()
    model_manager.load_model()
    logger.info("Model loaded successfully for batch worker.")
except Exception as e:
    logger.critical(f"Failed to load model in batch worker: {e}", exc_info=True)
    exit(1)

transcription_service = TranscriptionService(use_thread_pool=False)

def process_batch(jobs: List[Job]):
    """
    Process a batch of transcription jobs.
    """
    if not jobs:
        return

    batch_size = len(jobs)
    job_ids = [job.id for job in jobs]
    logger.info(f"Processing batch of {batch_size} jobs: {job_ids}")

    # Update job statuses to 'started'
    for job in jobs:
        job.set_status('started')
        job.save_meta()

    try:
        file_paths = [job.args[0] for job in jobs]
        transcription_results = transcription_service.transcribe_batch(file_paths)

        # Save results for each job
        for i, job in enumerate(jobs):
            result = transcription_results[i]
            job.result = result
            job.set_status('finished')
            job.save()
            logger.info(f"Job {job.id} finished successfully.")

            # Clean up the audio file
            try:
                if os.path.exists(file_paths[i]):
                    os.unlink(file_paths[i])
                    logger.debug(f"Cleaned up audio file: {file_paths[i]}")
            except OSError as e:
                logger.warning(f"Failed to clean up audio file {file_paths[i]}: {e}")

    except Exception as e:
        logger.error(f"Batch processing failed: {e}", exc_info=True)
        for job in jobs:
            job.set_status('failed')
            job.exc_info = str(e)
            job.save()

def main():
    """
    Main loop for the batch worker.
    """
    logger.info("Batch worker started. Listening for jobs...")
    queue = get_queue()

    while True:
        try:
            # Get a batch of jobs from the queue
            # This pulls up to BATCH_SIZE jobs that are currently queued
            job_ids = queue.get_job_ids()
            if not job_ids:
                time.sleep(settings.batch_timeout)
                continue

            num_jobs_to_pull = min(len(job_ids), settings.batch_size)
            jobs_to_process = [Job.fetch(job_id, connection=get_redis_connection()) for job_id in job_ids[:num_jobs_to_pull]]
            
            # We need to dequeue the jobs we are about to process
            # This is a simplification. A more robust solution would handle
            # potential race conditions if multiple workers are running.
            for job in jobs_to_process:
                queue.connection.lrem(queue.key, 1, job.id)

            process_batch(jobs_to_process)

        except Exception as e:
            logger.error(f"An error occurred in the main worker loop: {e}", exc_info=True)
            time.sleep(settings.batch_timeout)

if __name__ == "__main__":
    main()
