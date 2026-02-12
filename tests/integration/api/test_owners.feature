Feature: Test API owners endpoint

    Scenario: Successful owners request
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        When we make a GET request to the owners endpoint
        Then the request will return a 200 status code