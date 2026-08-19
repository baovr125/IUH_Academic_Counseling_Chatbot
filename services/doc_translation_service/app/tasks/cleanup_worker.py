import os
import time
from app.utils.logger import logger
from app.celery_app import celery_app

# Define the directories to clean up
TEMP_UPLOADS = "/app/temp_uploads"
TEMP_TRANSLATED = "/app/temp_translated"
# Age in seconds (48 hours = 48 * 60 * 60 = 172800)
MAX_AGE_SECONDS = 172800

@celery_app.task(name="app.tasks.cleanup_worker.cleanup_old_files")
def cleanup_old_files():
    """
    Deletes files in temp_uploads and temp_translated that are older than MAX_AGE_SECONDS.
    """
    logger.info("Starting cleanup of old files in temp directories...")
    
    current_time = time.time()
    files_deleted = 0
    
    for directory in [TEMP_UPLOADS, TEMP_TRANSLATED]:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    file_age = current_time - os.path.getmtime(file_path)
                    if file_age > MAX_AGE_SECONDS:
                        os.remove(file_path)
                        files_deleted += 1
                        logger.info(f"Deleted old file: {file_path}")
                except Exception as e:
                    logger.error(f"Error deleting file {file_path}: {e}")
                    
    logger.info(f"Cleanup completed. Total files deleted: {files_deleted}")
    return {"status": "success", "files_deleted": files_deleted}
