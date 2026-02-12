Feature: Test API all time records endpoint

    Scenario: Successful all time records request for all_time_championships
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value all_time_championships
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for top_10_team_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value top_10_team_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for bottom_10_team_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value bottom_10_team_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for top_10_qb_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value top_10_qb_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for top_10_rb_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value top_10_rb_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for top_10_wr_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value top_10_wr_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for top_10_te_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value top_10_te_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for top_10_dst_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value top_10_dst_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code

    Scenario: Successful all time records request for top_10_k_scores
        Given a valid API configuration
        and query parameter league_id with value 1770206
        and query parameter platform with value ESPN
        and query parameter record_type with value top_10_k_scores
        When we make a GET request to the alltime_records endpoint
        Then the request will return a 200 status code
