"""Script to fetch members within an ESPN fantasy football league."""

import os
import pandas as pd
from dotenv import load_dotenv

from api.data_pull_scripts.constants import POST_2024_BASE_URL, session

load_dotenv()


def get_league_members() -> list[dict[str, str]]:
    """
    Fetch league members for an ESPN fantasy football league.

    Returns:
        list (dict(str, str)): A list of dictionaries containing info of league members.
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
            "view": "mTeam",
        },
        cookies={
            "SWID": swid_cookie,
            "espn_s2": espn_s2_cookie,
        },
    )
    response.raise_for_status()
    members = response.json()[0].get("members", [])
    return members


def get_league_teams() -> list[dict[str, str]]:
    """
    Fetch teams for an ESPN fantasy football league.

    Returns:
        list (dict(str, str)): A list of dictionaries containing info of league members.
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
        },
        cookies={
            "SWID": swid_cookie,
            "espn_s2": espn_s2_cookie,
        },
    )
    response.raise_for_status()
    teams = response.json()[0].get("teams", "")
    return teams


def join_league_members_to_teams() -> list[dict[str, str]]:
    """
    Helper function to join teams and members responses into one data structure.

    Returns:
        list (dict(str, str)): A list of dictionaries with each dictionary containing
            details for a league member.

    Raises:
        ValueError: If either list of members or list of teams is empty.
    """
    members = get_league_members()
    teams = get_league_teams()
    if not members or not teams:
        raise ValueError("'members' or 'teams' lists must not be empty.")
    df_members = pd.DataFrame(data=members)
    df_teams = pd.DataFrame(data=teams)
    df_teams_exploded = df_teams.explode(column="owners")
    df_members_and_teams = pd.merge(
        left=df_members,
        right=df_teams_exploded,
        how="inner",
        left_on="id",
        right_on="owners",
    )
    df_members_and_teams = df_members_and_teams.rename(
        columns={"id_x": "member_id", "id_y": "team_id"}
    )
    df_members_and_teams = df_members_and_teams.drop(columns=["owners"])
    dict_members_and_teams = df_members_and_teams.to_dict(orient="records")
    return dict_members_and_teams
