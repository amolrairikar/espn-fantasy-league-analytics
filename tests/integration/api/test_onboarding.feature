Feature: Test API league onboarding endpoint

    Scenario: Successfully trigger onboarding
        Given a valid API configuration
        and request body field league_id with value "1770206"
        and request body field platform with value ESPN
        and secure request body field espn_s2
        and secure request body field swid
        and request body field seasons with value ["2025", "2024"]
        When we make a POST request to the onboard endpoint
        Then the request will return a 201 status code

    Scenario: Successfully monitor onboarding
        Given a valid API configuration
        When we make a GET request to the onboard/2a699734-de8b-4a24-81eb-5fc1796f85f9 endpoint
        Then the request will return a 200 status code