from playwright.sync_api import Page, expect


def test_login_form_validation_missing_league_id(page: Page):
    """
    Test that the login form shows "League ID is required" error when
    submitting without entering a league ID.
    """
    # Navigate to the login page
    page.goto("http://localhost:5173")

    # Wait for the form to be visible
    form = page.locator("form")
    expect(form).to_be_visible()

    # Find the submit button and click it without entering a league ID
    submit_button = page.locator('button[type="submit"]')
    expect(submit_button).to_be_visible()
    submit_button.click()

    # Verify the error message is associated with the League ID field
    league_id_field = page.locator('input[name="leagueId"]')
    expect(league_id_field).to_be_visible()

    # The error should appear in the FormMessage component with data-slot="form-message"
    error_message = page.locator(
        '[data-slot="form-message"]:has-text("League ID is required")'
    )
    expect(error_message).to_be_visible()


def test_login_form_valid_league_id_shows_registration_dialog(page: Page):
    """
    Test that entering a valid 5-digit league ID and submitting shows
    the "Register Your League" dialog. Waits up to 2 seconds for the dialog.
    """
    # Navigate to the login page
    page.goto("http://localhost:5173")

    # Wait for the form to be visible
    form = page.locator("form")
    expect(form).to_be_visible()

    # Fill in the league ID with a 5-digit number
    league_id_field = page.locator('input[name="leagueId"]')
    expect(league_id_field).to_be_visible()
    league_id_field.fill("12345")

    # Find and click the submit button
    submit_button = page.locator('button[type="submit"]')
    expect(submit_button).to_be_visible()
    submit_button.click()

    # Wait for the "Register Your League" dialog to appear (up to 2 seconds)
    dialog_content = page.locator('[data-slot="dialog-content"]')
    expect(dialog_content).to_be_visible(timeout=2000)

    # Verify the dialog title is "Register Your League"
    dialog_title = dialog_content.locator(
        '[data-slot="dialog-title"]:has-text("Register Your League")'
    )
    expect(dialog_title).to_be_visible()


def test_registration_dialog_form_validation_errors(page: Page):
    """
    Test that the registration dialog shows proper validation errors when
    submitted without filling in the required fields.
    """
    # Navigate to the login page
    page.goto("http://localhost:5173")

    # Wait for the form to be visible
    form = page.locator("form")
    expect(form).to_be_visible()

    # Fill in the league ID with a 5-digit number to trigger the registration dialog
    league_id_field = page.locator('input[name="leagueId"]')
    expect(league_id_field).to_be_visible()
    league_id_field.fill("12345")

    # Find and click the submit button to open the registration dialog
    submit_button = page.locator('button[type="submit"]')
    expect(submit_button).to_be_visible()
    submit_button.click()

    # Wait for the "Register Your League" dialog to appear
    dialog_content = page.locator('[data-slot="dialog-content"]')
    expect(dialog_content).to_be_visible(timeout=2000)

    # Find the registration dialog form submit button (inside the dialog)
    dialog_submit_button = dialog_content.locator('button[type="submit"]')
    expect(dialog_submit_button).to_be_visible()
    dialog_submit_button.click()

    # Verify all expected error messages appear
    # Check that we have the correct number of validation errors
    year_errors = dialog_content.locator(
        '[data-slot="form-message"]:has-text("Must be a valid year (2000 or later)")'
    )
    expect(year_errors).to_have_count(2)  # Both First Season and Last Season fields

    swid_cookie_error = dialog_content.locator(
        '[data-slot="form-message"]:has-text("Invalid SWID format (Expected {XXXXXXXX-XXXX-...})")'
    )
    expect(swid_cookie_error).to_be_visible()

    espn_s2_cookie_error = dialog_content.locator(
        '[data-slot="form-message"]:has-text("ESPN S2 cookie is too short")'
    )
    expect(espn_s2_cookie_error).to_be_visible()
