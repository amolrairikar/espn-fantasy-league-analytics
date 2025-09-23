"""Script to fetch matchup scores within an ESPN fantasy football league."""

import logging
import math
import time
from typing import Optional, Any

import boto3
import botocore.exceptions
from urllib3.util.retry import Retry

import requests
from requests.adapters import HTTPAdapter

# Set up standardized logger for Lambda
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(levelname)s - %(name)s - %(filename)s -  %(lineno)d - %(message)s"
)
console_handler.setFormatter(formatter)
if not logger.hasHandlers():
    logger.addHandler(console_handler)

retry_strategy = Retry(
    total=3,
    backoff_factor=0.3,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET", "POST", "PUT", "DELETE"],
)
adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("http://", adapter)
session.mount("https://", adapter)

DYNAMODB_TABLE_NAME = "fantasy-analytics-app-db"


def get_league_scores(
    league_id: str,
    platform: str,
    season: str,
    swid_cookie: Optional[str],
    espn_s2_cookie: Optional[str],
) -> list:
    """
    Fetch league matchup scores for a fantasy football league in a given season.

    Args:
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
        swid_cookie (Optional[str]): The SWID cookie used for getting ESPN private league data.
        espn_s2_cookie (Optional[str]): The espn S2 cookie used for getting ESPN private league data.

    Returns:
        list: A list containing data for each matchup in the season.

    Raises:
        ValueError: If unsupported platform is specified, or if a required ESPN cookie is missing.
        requests.RequestException: If an error occurs while making API request.
        Exception: If uncaught exception occurs.
    """
    if platform == "ESPN":
        if not swid_cookie or not espn_s2_cookie:
            raise ValueError("Missing required SWID and/or ESPN S2 cookies")
        try:
            params = {
                "view": "mMatchupScore",
            }
            if int(season) >= 2018:
                url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/seasons/{season}/segments/0/leagues/{league_id}"
            else:
                url = f"https://lm-api-reads.fantasy.espn.com/apis/v3/games/ffl/leagueHistory/{league_id}"
                params["seasonId"] = season
            logger.info("Making request for league scores info to URL: %s", url)
            response = session.get(
                url=url,
                params=params,
                cookies={"SWID": swid_cookie, "espn_s2": espn_s2_cookie},
            )
            response.raise_for_status()
            logger.info("Successfully got league score info")
            if int(season) >= 2018:
                scores = response.json().get("schedule", [])
            else:
                scores = response.json()[0].get("schedule", [])
            logger.info(
                "Found %d matchups in league for season %s", len(scores), season
            )
            return scores
        except requests.RequestException:
            logger.exception("Request error while fetching league scores.")
            raise
        except Exception:
            logger.exception("Unexpected error while fetching league scores.")
            raise
    else:
        raise ValueError("Unsupported platform. Only ESPN is currently supported.")


def safe_int(team_id: str) -> int:
    """
    Convert team_id to int if possible, else use a very large int.

    Args:
        team_id (str): The team_id to convert to an integer. Can be a valid number or empty string "".

    Returns:
        int: The team_id converted to its integer value or a large number.
    """
    try:
        return int(team_id)
    except (ValueError, TypeError):
        return 10**12


def process_league_scores(matchups: list[dict[str, Any]]) -> list:
    """
    Extracts relevant fields from fantasy matchup scores.

    Args:
        matchups (list[dict[str, Any]]): Raw dictionary with all metadata from each matchup
            for the league that season.

    Returns:
        list: Processed dictionary with relevant data from fantasy matchup scores.
    """
    processed_matchup_results = []
    for matchup in matchups:
        home_team = matchup.get("home", {}).get("teamId", "")
        home_score = matchup.get("home", {}).get("totalPoints", "0.00")
        away_team = matchup.get("away", {}).get("teamId", "")
        away_score = matchup.get("away", {}).get("totalPoints", "0.00")

        # Canonicalize: team_a ID < team_b ID
        team_a, team_b = sorted([home_team, away_team], key=safe_int)
        if team_a == home_team:
            team_a_score = home_score
            team_b_score = away_score
        else:
            team_a_score = away_score
            team_b_score = home_score

        # Determine winner in terms of team_a/team_b
        if float(team_a_score) > float(team_b_score):
            winner: str | int = team_a
        elif float(team_b_score) > float(team_a_score):
            winner = team_b
        else:
            winner = "TIE"

        matchup_result = {
            "team_a": team_a,
            "team_b": team_b,
            "team_a_score": team_a_score,
            "team_b_score": team_b_score,
            "playoff_tier_type": matchup.get("playoffTierType", ""),
            "winner": winner,
            "matchup_week": matchup.get("matchupPeriodId", ""),
        }
        processed_matchup_results.append(matchup_result)

    return processed_matchup_results


# def compile_league_standings(matchup_data: list[dict[str, Any]]) -> list:
#     """
#     Calculates league standings based on fantasy matchup scores.

#     Args:
#         matchup_data (list[dict[str, Any]]): A list of dictionary mappings containing
#             matchup scores.

#     Returns:
#         list: A list of mappings containing standings information for each team.
#     """
#     pd.set_option('display.max_columns', None)
#     df_matchup_data = pd.DataFrame(data=matchup_data)
#     df_matchup_data["winning_team_id"] = np.where(df_matchup_data["winner"] == "AWAY", df_matchup_data["away_team"], df_matchup_data["home_team"])
#     df_matchup_data["losing_team_id"] = np.where(df_matchup_data["winner"] == "AWAY", df_matchup_data["home_team"], df_matchup_data["away_team"])
#     df_matchup_data["away_score"] = pd.to_numeric(df_matchup_data["away_score"], errors="coerce").fillna(0)
#     df_matchup_data["home_score"] = pd.to_numeric(df_matchup_data["home_score"], errors="coerce").fillna(0)

#     # Only get regular season matchups for now
#     df_matchup_data = df_matchup_data[df_matchup_data["playoff_tier_type"] == "NONE"]

#     # Step 1: Build a dataframe for "home stats"
#     home_stats = df_matchup_data[["home_team", "home_score", "away_score"]].copy()
#     home_stats.rename(columns={
#         "home_team": "team_id",
#         "home_score": "points_scored",
#         "away_score": "points_allowed"
#     }, inplace=True)

#     # Step 2: Build a dataframe for "away stats"
#     away_stats = df_matchup_data[["away_team", "away_score", "home_score"]].copy()
#     away_stats.rename(columns={
#         "away_team": "team_id",
#         "away_score": "points_scored",
#         "home_score": "points_allowed"
#     }, inplace=True)

#     # Step 3: Concatenate home and away stats
#     all_stats = pd.concat([home_stats, away_stats])

#     # Step 4: Aggregate points scored and allowed
#     team_points = all_stats.groupby("team_id").sum()[["points_scored", "points_allowed"]]

#     # Step 5: Count wins and losses
#     wins = df_matchup_data["winning_team_id"].value_counts().rename("wins")
#     losses = df_matchup_data["losing_team_id"].value_counts().rename("losses")

#     # Step 6: Combine into a standings dataframe
#     standings = team_points.join(wins).join(losses)
#     standings.fillna(0, inplace=True)  # Fill teams with 0 wins/losses if missing
#     standings = standings.astype({"wins": int, "losses": int})

#     # Step 7: Reset index to return dataframe object
#     standings = standings.reset_index()

#     return standings.to_dict(orient="records")


def batch_write_to_dynamodb(
    data_to_write: list[dict[str, str]], league_id: str, platform: str, season: str
) -> None:
    """
    Writes data in batches to DynamoDB with retries of unprocessed items using
    exponential backoff.

    Args:
        data_to_write (dict[str, str]): Output data to write to DynamoDB.
        league_id (str): The unique ID of the fantasy football league.
        platform (str): The platform the fantasy football league is on (e.g., ESPN, Sleeper).
        season (str): The NFL season to get data for.
    """
    batched_objects = []
    for item in data_to_write:
        batched_objects.append(
            {
                "PutRequest": {
                    "Item": {
                        "PK": {
                            "S": f"LEAGUE#{league_id}#PLATFORM#{platform}#SEASON#{season}"
                        },
                        "SK": {
                            "S": f"MATCHUP#{str(item['team_a'])}-vs-{str(item['team_b'])}#WEEK#{str(item['matchup_week'])}"
                        },
                        "GSI1PK": {
                            "S": f"MATCHUP#{item['team_a']}-vs-{item['team_b']}"
                        },
                        "GSI1SK": {
                            "S": f"LEAGUE#{league_id}#SEASON#{season}#WEEK#{item['matchup_week']}"
                        },
                        "team_a": {"S": str(item["team_a"])},
                        "team_a_score": {"N": str(item["team_a_score"])},
                        "team_b": {"S": str(item["team_b"])},
                        "team_b_score": {"N": str(item["team_b_score"])},
                        "week": {"S": str(item["matchup_week"])},
                        "winner": {"S": str(item["winner"])},
                        "playoff_tier_type": {"S": item["playoff_tier_type"]},
                    }
                }
            }
        )
    dynamodb = boto3.client("dynamodb")
    try:
        table_name = "fantasy-analytics-app-db"
        backoff = 1.0
        max_retries = 5

        # BatchWriteItem has max limit of 25 items
        batch_number = 0
        for i in range(0, len(batched_objects), 25):
            logger.info(
                "Processing batch %d/%d",
                batch_number + 1,
                math.ceil(len(batched_objects) / 25),
            )
            batch = batched_objects[i : i + 25]
            request_items = {table_name: batch}
            retries = 0
            while True:
                logger.info("Attempt number: %d", retries + 1)
                response = dynamodb.batch_write_item(RequestItems=request_items)
                unprocessed = response.get("UnprocessedItems", {})
                if not unprocessed.get(table_name):
                    batch_number += 1
                    break  # success, go to next batch

                if retries >= max_retries:
                    raise RuntimeError(
                        f"Max retries exceeded. Still unprocessed: {unprocessed}"
                    )

                logger.info(
                    "Failed to write %d items, retrying unprocessed items...",
                    len(unprocessed),
                )
                retries += 1
                sleep_time = backoff * (2 ** (retries - 1))
                time.sleep(sleep_time)

                # Retry only the failed items
                request_items = unprocessed

    except botocore.exceptions.ClientError:
        logger.exception("Error writing member and team data to DynamoDB")
        raise


def lambda_handler(event, context):
    """Lambda handler function to get league members and teams."""
    logger.info("Received event: %s", event)
    league_id = event["leagueId"]
    platform = event["platform"]
    swid_cookie = event["swidCookie"]
    espn_s2_cookie = event["espnS2Cookie"]
    season = event["season"]

    matchups = get_league_scores(
        league_id=league_id,
        platform=platform,
        season=season,
        swid_cookie=swid_cookie,
        espn_s2_cookie=espn_s2_cookie,
    )
    if not matchups:
        raise ValueError("'matchups' list must not be empty.")

    logger.info("Processing raw matchup data")
    output_data = process_league_scores(matchups=matchups)
    batch_write_to_dynamodb(
        data_to_write=output_data, league_id=league_id, platform=platform, season=season
    )
    logger.info("Successfully wrote data to DynamoDB.")


lambda_handler(
    event={
        "leagueId": "1770206",
        "platform": "ESPN",
        "privacy": "Private",
        "swidCookie": "{5C607AAE-F39B-4BF7-8306-BEE68C48A53B}",
        "espnS2Cookie": "AECS%2Fm2P8g7pbnggkucc8qDrpgHgQ22PkiTn8ia8%2FNpb5AaWTjiYw1fc%2FjMtPaCDzWqLEPpD1yz%2BlCZ7rbZSrCcyV5LmaeM9qYwdOz30AcZnC8ZRolRGvP2%2BfMgME0L26v41DrytOJdvXM9rwGA8Mau1DJmuHjedA55tdQlzzTm5WqPkGeZbLB35C96v8UUBEDiq6WuzDvjMaOVnZVExD1U9HjhgGZp4jsUi58BTTPIkjMYIt3nfIeiItIs4hQjyRWYfhZW9jrpEPzX%2BCtuLpqdWNhjfU4l6tP%2BYfE0S1Ih84YDtmXhFTkzKj7oXwKSAuPQ%3D",
        "season": "2024",
    },
    context="",
)
