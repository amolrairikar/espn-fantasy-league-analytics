Feature: Make API requests to ESPN Fantasy Football API

    Scenario: Successful API request for seasons after 2018
        Given a requests session
        When we make an authenticated ESPN Fantasy Football API request for the 2025 season
        Then a response will be returned

    Scenario: Successful API request for seasons before 2018
        Given a requests session
        When we make an authenticated ESPN Fantasy Football API request for the 2017 season
        Then a response will be returned

    Scenario: Failed API request for seasons after 2018
        Given a requests session
        When we make an unauthenticated ESPN Fantasy Football API request for the 2025 season
        Then no response will be returned

    Scenario: Failed API request for seasons before 2018
        Given a requests session
        When we make an unauthenticated ESPN Fantasy Football API request for the 2017 season
        Then no response will be returned