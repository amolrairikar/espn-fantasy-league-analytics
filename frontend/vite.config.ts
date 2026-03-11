import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import tsconfigPaths from 'vite-tsconfig-paths';
import { defineConfig } from 'vitest/config';

export default defineConfig({
  plugins: [react(), tailwindcss(), tsconfigPaths()],
  test: {
    environment: 'jsdom',
    coverage: {
      provider: 'v8',
    },
  },
});
