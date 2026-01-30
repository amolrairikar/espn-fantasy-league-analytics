Feature: Batch write objects to DynamoDB

    Scenario: Successful batch write operation with single batch
        Given a DynamoDB table named integration-test-table
        When we write a single batch of data
        Then the table will contain 2 records

    Scenario: Successful batch write operation with multiple batches
        Given a DynamoDB table named integration-test-table
        When we write multiple batches of data
        Then the table will contain 35 records