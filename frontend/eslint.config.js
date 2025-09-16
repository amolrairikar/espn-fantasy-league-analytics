// eslint.config.js
import js from '@eslint/js';
import globals from 'globals';
import tsParser from '@typescript-eslint/parser';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import prettierPlugin from 'eslint-plugin-prettier';
import { globalIgnores } from 'eslint/config';
import { fileURLToPath } from 'url';
import { dirname } from 'path';

// Get absolute path to the project root (Windows-compatible)
const __dirname = dirname(fileURLToPath(import.meta.url));

export default [
  // Ignore build folders and 3rd party UI files
  globalIgnores(['dist', 'node_modules', 'src/components/ui/**', 'src/components/themes/**']),

  // JS recommended rules
  js.configs.recommended,

  // TypeScript recommended rules
  {
    files: ['**/*.{ts,tsx}'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 2020,
        sourceType: 'module',
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: __dirname, // absolute path
      },
      globals: globals.browser,
    },
    plugins: { '@typescript-eslint': tsPlugin },
    rules: {
      // Recommended rules from typescript-eslint
      ...tsPlugin.configs.recommended.rules,
      ...tsPlugin.configs['recommended-requiring-type-checking'].rules,
    },
  },

  // React Hooks recommended rules
  reactHooks.configs['recommended-latest'],

  // React Refresh (Vite) rules
  reactRefresh.configs.vite,

  // Prettier integration
  {
    plugins: { prettier: prettierPlugin },
    rules: { ...prettierPlugin.configs.recommended.rules },
  },
];
