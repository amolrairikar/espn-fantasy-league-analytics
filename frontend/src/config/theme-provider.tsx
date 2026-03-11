import {
  createTheme,
  ThemeProvider,
  useMediaQuery,
  CssBaseline,
} from '@mui/material';
import { useMemo } from 'react';

interface CustomThemeProviderProps {
  children: React.ReactNode;
}

/**
 * CustomThemeProvider wraps the application in the MUI ThemeProvider.
 * It automatically detects the user's system preference for dark mode.
 * * @param props - The component properties.
 */
export const CustomThemeProvider = ({ children }: CustomThemeProviderProps) => {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? 'dark' : 'light',
        },
      }),
    [prefersDarkMode],
  );

  return (
    <ThemeProvider theme={theme}>
      {/* CssBaseline resets CSS and sets the body background color based on the theme */}
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
};
