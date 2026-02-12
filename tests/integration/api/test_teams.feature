Feature: Test API teams endpoint

    Scenario: Successful teams request for a specific team
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter season with value 2025
        and query parameter team_id with value 1
        When we make a GET request to the teams endpoint
        Then the request will return a 200 status code

    Scenario: Successful teams request for all teams
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter season with value 2025
        and query parameter team_id with value null
        When we make a GET request to the teams endpoint
        Then the request will return a 200 status code
