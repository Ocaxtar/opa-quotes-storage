"""
opa-quotes-storage - Main entry point
"""
import asyncio
import logging

from shared.utils.pipeline_logger import PipelineLogger

from opa_quotes_storage.config import get_settings
from opa_quotes_storage.logging_setup import setup_logging

setup_logging()
logger = logging.getLogger(__name__)

settings = get_settings()


async def main():
    """Main pipeline execution."""
    pipeline_logger = PipelineLogger(
        pipeline_name="opa-quotes-storage", repository="opa-quotes-storage"
    )

    try:
        pipeline_logger.start(metadata={"env": settings.environment})
        logger.info(f"Starting {settings.app_name} v{settings.version}")

        # TODO: Implement pipeline logic here

        pipeline_logger.complete(status="success", metadata={"message": "Pipeline completed"})
        logger.info("Pipeline completed successfully")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        pipeline_logger.fail(error_message=str(e))
        raise

    finally:
        pipeline_logger.close()


if __name__ == "__main__":
    asyncio.run(main())
