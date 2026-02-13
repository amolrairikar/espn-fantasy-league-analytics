from playwright.sync_api import Page, expect


def test_full_stack_connection(page: Page):
    # Test React server running
    page.goto("http://localhost:5173")
    expect(page.locator("#root")).to_be_attached()

    # Test API server running
    page.goto("http://localhost:8000/docs")
    expect(page).to_have_title("FastAPI - Swagger UI")
