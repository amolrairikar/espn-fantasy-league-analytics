Feature: Test API health check endpoint

    Scenario: Successful health check
        Given a valid API configuration
        When we make a GET request to the health endpoint
        Then the request will return a 200 status code
