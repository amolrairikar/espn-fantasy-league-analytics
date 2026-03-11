import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';

import './index.css';
import App from './app';

import { CustomThemeProvider } from '@/config/theme-provider';

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <CustomThemeProvider>
      <App />
    </CustomThemeProvider>
  </StrictMode>,
);
