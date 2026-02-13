Feature: Test API league metadata endpoint

    Scenario: Successfully validate league metadata
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter season with value 2025
        and secure query parameter swid_cookie
        and secure query parameter espn_s2_cookie
        When we make a GET request to the leagues/validate endpoint
        Then the request will return a 200 status code

    Scenario: Validate league metadata for unsupported platform
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value Sleeper
        and query parameter season with value 2025
        and secure query parameter swid_cookie
        and secure query parameter espn_s2_cookie
        When we make a GET request to the leagues/validate endpoint
        Then the request will return a 400 status code

    Scenario: Successfully get league metadata
        Given a valid API configuration
        and query parameter platform with value ESPN
        When we make a GET request to the leagues/1770206 endpoint
        Then the request will return a 200 status code

    Scenario: Get league metadata for league that does not exist
        Given a valid API configuration
        and query parameter platform with value ESPN
        When we make a GET request to the leagues/12345 endpoint
        Then the request will return a 404 status code

    Scenario: Successfully create league metadata
        Given a valid API configuration
        and request body field league_id with value "12345"
        and request body field platform with value ESPN
        and secure request body field espn_s2
        and secure request body field swid
        and request body field seasons with value ["2025", "2024"]
        When we make a POST request to the leagues endpoint
        Then the request will return a 201 status code

    Scenario: Successfully update league metadata
        Given a valid API configuration
        and request body field league_id with value "1770206"
        and request body field platform with value ESPN
        and secure request body field espn_s2
        and secure request body field swid
        and request body field seasons with value ["2025", "2024"]
        and request body field onboarded_status with value "true"
        and request body field onboarded_date with value "2026-02-09T22:50:34.572Z"
        When we make a PUT request to the leagues/1770206 endpoint
        Then the request will return a 200 status code
