"""
Module for processing league data using DuckDB.
"""

import duckdb
import pandas as pd


def join_league_members_to_teams(
    members: list[dict], teams: list[dict], season: str
) -> pd.DataFrame:
    """
    Helper function to join teams and members responses into one data structure.

    Args:
        members: A list of dictionaries containing info about each member.
        teams: A list of dictionaries containing info about each team.

    Returns:
        pd.DataFrame: The resulting dataframe from joined data.

    Raises:
        ValueError: If either list of members or list of teams is empty.
    """
    df_members = pd.json_normalize(members)[
        ["displayName", "firstName", "lastName", "id"]
    ]
    df_teams = pd.json_normalize(teams)[["abbrev", "id", "name", "owners"]]

    with duckdb.connect(":memory:") as conn:
        conn.register("df_members", df_members)
        conn.register("df_teams", df_teams)

        query = f"""
        SELECT 
            '{season}' AS season,
            m.firstName AS first_name, 
            m.lastName AS last_name, 
            t.abbrev AS abbreviation, 
            t.id AS team_id, 
            t.name AS team_name,
            m.id AS member_id
        FROM df_teams t
        CROSS JOIN UNNEST(t.owners) AS _unzipped(owner_id)
        INNER JOIN df_members m ON m.id = owner_id
        """

        return conn.execute(query).df()
