Feature: Test API league standings endpoint

    Scenario: Successfully get season standings for one team across all seasons
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter standings_type with value season
        and query parameter season with value null
        and query parameter team with value "{5C607AAE-F39B-4BF7-8306-BEE68C48A53B}"
        and query parameter week with value null
        When we make a GET request to the standings endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get season standings for one season
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter standings_type with value season
        and query parameter season with value "2025"
        and query parameter team with value null
        and query parameter week with value null
        When we make a GET request to the standings endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get H2H standings
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter standings_type with value h2h
        and query parameter season with value null
        and query parameter team with value null
        and query parameter week with value null
        When we make a GET request to the standings endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get all-time standings
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter standings_type with value all_time
        and query parameter season with value null
        and query parameter team with value null
        and query parameter week with value null
        When we make a GET request to the standings endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get playoff standings
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter standings_type with value playoffs
        and query parameter season with value null
        and query parameter team with value null
        and query parameter week with value null
        When we make a GET request to the standings endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get weekly standings
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter standings_type with value weekly
        and query parameter season with value "2025"
        and query parameter team with value "{5C607AAE-F39B-4BF7-8306-BEE68C48A53B}"
        and query parameter week with value 10
        When we make a GET request to the standings endpoint
        Then the request will return a 200 status code
