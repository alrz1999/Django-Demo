from content.models import Content
from celery import shared_task

import logging

logger = logging.getLogger(__name__)

HOURLY_SCORE_CHANGE_THRESHOLD = 1


@shared_task
def normalize_candidate_contents_scores():
    logger.info("Starting the normalization of candidate content scores.")
    try:
        candidates = Content.get_candidates_for_normalization(HOURLY_SCORE_CHANGE_THRESHOLD)
        logger.info(f"Found {candidates.count()} candidates for normalization.")
        for candidate in candidates:
            logger.debug(f"Normalizing scores for Content ID {candidate.id} - Title: {candidate.title}")
            candidate.update_normalized_score_mean()

        logger.info("Successfully normalized scores for all candidate contents.")
    except Exception as e:
        logger.error(f"Error occurred during normalization of candidate content scores: {str(e)}", exc_info=True)
