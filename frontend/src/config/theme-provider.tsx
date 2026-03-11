import { useMemo } from 'react';
import { createTheme, ThemeProvider, useMediaQuery, CssBaseline } from '@mui/material';

export const CustomThemeProvider = ({ children }) => {
  const prefersDarkMode = useMediaQuery('(prefers-color-scheme: dark)');

  const theme = useMemo(
    () =>
      createTheme({
        palette: {
          mode: prefersDarkMode ? 'dark' : 'light',
        },
      }),
    [prefersDarkMode]
  );

  return (
    <ThemeProvider theme={theme}>
      {/* CssBaseline resets CSS and sets the body background color based on the theme */}
      <CssBaseline />
      {children}
    </ThemeProvider>
  );
};