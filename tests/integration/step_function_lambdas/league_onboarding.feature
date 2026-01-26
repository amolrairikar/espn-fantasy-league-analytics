Feature: New league onboarding

    Scenario: New league onboarded successfully
        Given a league with valid inputs
        When we onboard the league
        Then the league should onboard successfully