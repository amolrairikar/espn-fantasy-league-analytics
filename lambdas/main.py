"""
Main handler module for league data onboarding.
"""

from onboarding.league_onboarder import LeagueOnboarder
from utils.logging_config import logger


def handler(event, context) -> dict[str, str]:
    """
    Lambda handler function to fetch GTFS data and store it in S3.

    Args:
        event: The event data that triggered the Lambda function.
        context: The context in which the Lambda function is running.

    Returns:
        dict: A response indicating the success of the operation.
    """
    logger.info("Starting league onboarding process execution.")
    logger.info("Event data: %s", event)
    logger.info("Context data: %s", context)

    onboarder = LeagueOnboarder(
        league_id=event["body"]["leagueId"],
        platform=event["body"]["platform"],
        swid_cookie=event["body"]["swidCookie"],
        espn_s2_cookie=event["body"]["espnS2Cookie"],
        seasons=event["body"]["seasons"],
    )

    try:
        onboarder.run_onboarding_process()
        return {
            "status": "success",
            "message": f"Successfully onboarded league {event['body']['leagueId']}",
        }
    except Exception as e:
        logger.error(f"Onboarding failed: {str(e)}")
        return {"status": "error", "message": str(e)}
