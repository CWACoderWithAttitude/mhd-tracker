export default [
  {
    ignores: ["dist/**", "coverage/**", "node_modules/**"],
  },
  {
    files: ["src/**/*.{js,mjs,cjs}"],
    rules: {
      "no-unused-vars": "warn",
      "no-undef": "off",
    },
  },
];
