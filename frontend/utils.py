"""Module containing utility functions used by the Streamlit frontend app."""

import streamlit as st


def check_league_credentials() -> bool:
    """Check if the provided league ID has valid credentials already stored in the database."""
    # Placeholder implementation
    league_id = st.session_state["league_id"]

    # This simulates the check for now, implement a function to verify credentials
    st.session_state["credentials_valid"] = bool(league_id)
