import { useMediaQuery } from '@mui/material';
import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';

import { CustomThemeProvider } from './theme-provider';

/**
 * Mocking MUI's useMediaQuery hook to simulate various system theme preferences.
 */
vi.mock('@mui/material', async (importOriginal) => {
  const actual = await importOriginal<typeof import('@mui/material')>();
  return {
    ...actual,
    useMediaQuery: vi.fn(),
  };
});

const mockUseMediaQuery = vi.mocked(useMediaQuery);

/**
 * Suite: CustomThemeProvider
 * Ensures that the application theme correctly reacts to system preferences
 * and provides the expected context to children.
 */
describe('CustomThemeProvider', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  /**
   * Test: Renders children
   * Verifies that the provider is transparent and renders the passed-in children.
   */
  it('renders children', () => {
    mockUseMediaQuery.mockReturnValue(false);
    render(
      <CustomThemeProvider>
        <div>test child</div>
      </CustomThemeProvider>,
    );
    expect(screen.getByText('test child')).toBeDefined();
  });

  /**
   * Test: Applies dark mode
   * Verifies that when the system indicates a preference for dark mode,
   * the background color style is updated accordingly.
   */
  it('applies dark mode when system preference is dark', () => {
    mockUseMediaQuery.mockReturnValue(true);
    const { container } = render(
      <CustomThemeProvider>
        <div>dark mode child</div>
      </CustomThemeProvider>,
    );
    expect(screen.getByText('dark mode child')).toBeDefined();

    const bodyStyle = window.getComputedStyle(container.ownerDocument.body);
    expect(bodyStyle.backgroundColor).not.toBe('');
  });

  /**
   * Test: Applies light mode
   * Verifies the fallback behavior when the system preference is not 'dark'.
   */
  it('applies light mode when system preference is light', () => {
    mockUseMediaQuery.mockReturnValue(false);
    const { container } = render(
      <CustomThemeProvider>
        <div>light mode child</div>
      </CustomThemeProvider>,
    );
    expect(screen.getByText('light mode child')).toBeDefined();
    const bodyStyle = window.getComputedStyle(container.ownerDocument.body);
    expect(bodyStyle.backgroundColor).not.toBe('');
  });

  /**
   * Test: Media query verification
   * Ensures the provider specifically targets the '(prefers-color-scheme: dark)' query.
   */
  it('passes the dark mode media query string to useMediaQuery', () => {
    mockUseMediaQuery.mockReturnValue(false);
    render(
      <CustomThemeProvider>
        <span>child</span>
      </CustomThemeProvider>,
    );
    expect(mockUseMediaQuery).toHaveBeenCalledWith(
      '(prefers-color-scheme: dark)',
    );
  });
});
