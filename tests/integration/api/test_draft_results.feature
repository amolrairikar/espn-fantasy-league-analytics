Feature: Test API draft results endpoint

    Scenario: Successful draft results request
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter season with value 2025
        When we make a GET request to the draft-results endpoint
        Then the request will return a 200 status code
