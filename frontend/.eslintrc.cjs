module.exports = {
  root: true,
  parser: "@typescript-eslint/parser", // use TypeScript parser
  parserOptions: {
    ecmaVersion: 2020,
    sourceType: "module",
    ecmaFeatures: {
      jsx: true, // enable JSX
    },
  },
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    "eslint:recommended",
    "plugin:react/recommended",
    "plugin:@typescript-eslint/recommended",
    "plugin:prettier/recommended" // integrates Prettier rules
  ],
  plugins: ["react", "@typescript-eslint", "simple-import-sort"],
  settings: {
    react: {
      version: "detect", // automatically detect React version
    },
  },
  rules: {
    // Sorting imports/exports automatically
    "simple-import-sort/imports": "error",
    "simple-import-sort/exports": "error",

    // Example common rules
    "react/react-in-jsx-scope": "off", // React 17+ doesn't need React in scope
    "@typescript-eslint/no-unused-vars": ["warn", { argsIgnorePattern: "^_" }],
    "prettier/prettier": ["error"],

    // Optional: enforce consistent quotes, semi, etc via Prettier
  },
};
