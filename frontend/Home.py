import streamlit as st

from utils import check_league_credentials

# Initialize all session state variables
if "credentials_valid" not in st.session_state:
    st.session_state["credentials_valid"] = False

st.write("# Welcome!")

st.write(
    """
    This is a companion app for ESPN fantasy football leagues that provides additional insights for
    recapping a fantasy football season. Features include:
    - Draft analysis (looking back at it, who had the best initial draft?)
    - Scoring breakdowns (who got lucky or unlucky for a certain week)
    - League history (all time records, records vs. specific owners)
    """
)

st.write(
    """
    Instructions for how to find your league ID along with the ESPN SWID and ESPN S2 cookies for
    the below form can be found [here](https://github.com/amolrairikar/espn-fantasy-league-analytics/blob/main/README.md).
    """
)

st.write("### Enter league details")

st.text_input(
    label="League ID", value="", key="league_id", on_change=check_league_credentials
)
if st.session_state["credentials_valid"]:
    st.text_input(label="ESPN SWID Cookie", value="")
    st.text_input(label="ESPN S2 Cookie", value="")
