Feature: Test API league matchups endpoint

    Scenario: Successfully get specific matchup between two teams
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter playoff_filter with value include
        and query parameter team1_id with value {5C607AAE-F39B-4BF7-8306-BEE68C48A53B}
        and query parameter team2_id with value {D243CB28-C3AA-4CEA-9B84-CB9714AE8665}
        and query parameter week_number with value 15
        and query parameter season with value 2024
        When we make a GET request to the matchups endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get specific matchup for one team
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter playoff_filter with value include
        and query parameter team1_id with value {5C607AAE-F39B-4BF7-8306-BEE68C48A53B}
        and query parameter week_number with value 15
        and query parameter season with value 2024
        When we make a GET request to the matchups endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get all matchups between two teams
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter playoff_filter with value include
        and query parameter team1_id with value {5C607AAE-F39B-4BF7-8306-BEE68C48A53B}
        and query parameter team2_id with value {D243CB28-C3AA-4CEA-9B84-CB9714AE8665}
        When we make a GET request to the matchups endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get matchups for a week
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter playoff_filter with value include
        and query parameter week_number with value 15
        and query parameter season with value 2024
        When we make a GET request to the matchups endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get matchups for one team in a season
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter playoff_filter with value include
        and query parameter team1_id with value {5C607AAE-F39B-4BF7-8306-BEE68C48A53B}
        and query parameter season with value 2024
        When we make a GET request to the matchups endpoint
        Then the request will return a 200 status code

    Scenario: Successfully get all matchups for one team
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter playoff_filter with value include
        and query parameter team1_id with value {5C607AAE-F39B-4BF7-8306-BEE68C48A53B}
        When we make a GET request to the matchups endpoint
        Then the request will return a 200 status code
