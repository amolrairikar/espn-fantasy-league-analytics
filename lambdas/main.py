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


handler(
    event={
        "name": "test-event",
        "body": {
            "leagueId": "1770206",
            "platform": "ESPN",
            "swidCookie": "{5C607AAE-F39B-4BF7-8306-BEE68C48A53B}",
            "espnS2Cookie": "AECS%2Fm2P8g7pbnggkucc8qDrpgHgQ22PkiTn8ia8%2FNpb5AaWTjiYw1fc%2FjMtPaCDzWqLEPpD1yz%2BlCZ7rbZSrCcyV5LmaeM9qYwdOz30AcZnC8ZRolRGvP2%2BfMgME0L26v41DrytOJdvXM9rwGA8Mau1DJmuHjedA55tdQlzzTm5WqPkGeZbLB35C96v8UUBEDiq6WuzDvjMaOVnZVExD1U9HjhgGZp4jsUi58BTTPIkjMYIt3nfIeiItIs4hQjyRWYfhZW9jrpEPzX%2BCtuLpqdWNhjfU4l6tP%2BYfE0S1Ih84YDtmXhFTkzKj7oXwKSAuPQ%3D",
            "seasons": [
                "2016",
                "2017",
                "2018",
                "2019",
                "2020",
                "2021",
                "2022",
                "2023",
                "2024",
                "2025",
            ],
        },
    },
    context={},
)
