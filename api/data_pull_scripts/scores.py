"""Script to fetch matchup scores within an ESPN fantasy football league."""

import os
from dotenv import load_dotenv

from api.data_pull_scripts.constants import POST_2024_BASE_URL, session

load_dotenv()


def get_raw_league_matchup_data() -> list[dict[str, str]]:
    """
    Fetch raw league matchup data for an ESPN fantasy football league.

    Returns:
        list (dict(str, str)): A list of dictionaries containing score results
            from each matchup.
    """
    try:
        league_id = os.environ["LEAGUE_ID"]
        swid_cookie = os.environ["SWID_COOKIE"]
        espn_s2_cookie = os.environ["ESPN_S2_COOKIE"]
    except KeyError as e:
        raise e

    response = session.get(
        url=POST_2024_BASE_URL + f"/ffl/leagueHistory/{league_id}",
        params={
            "seasonId": "2024",
            "view": "mMatchupScore",
        },
        cookies={
            "SWID": swid_cookie,
            "espn_s2": espn_s2_cookie,
        },
    )
    response.raise_for_status()
    matchups = response.json()[0].get("schedule", [])
    return matchups


def get_matchup_scores() -> list[dict[str, str]]:
    """
    Extracts relevant scoring data from each league matchup.

    Returns:
        list (dict(str, str)): A list of dictionaries containing processed
            score results from each matchup.
    """
    matchups = get_raw_league_matchup_data()
    matchup_results = []
    for matchup in matchups:
        matchup_result = {}
        matchup_result["away_team"] = matchup.get("away", {}).get("teamId", "")
        matchup_result["away_score"] = matchup.get("home", {}).get("totalPoints", "")
        matchup_result["home_team"] = matchup.get("home", {}).get("teamId", "")
        matchup_result["home_score"] = matchup.get("home", {}).get("totalPoints", "")
        matchup_result["matchup_type"] = matchup.get("playoffTierType", "")
        matchup_result["winner"] = matchup.get("winner", "")
        matchup_results.append(matchup_result)
    return matchup_results
