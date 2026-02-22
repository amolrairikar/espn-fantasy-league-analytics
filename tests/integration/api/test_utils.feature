Feature: Test API utils endpoint

    Scenario: Successful deletion request for a valid league
        Given a valid API configuration
        and query parameter league_id with value 1770206
        When we make a DELETE request to the delete_league endpoint
        Then the request will return a 200 status code
