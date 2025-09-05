const nextJest = require("next/jest");

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: "./",
});

// Add any custom config to be passed to Jest
const customJestConfig = {
  // Ensure Jest resolves paths relative to the frontend folder even
  // when invoked from the monorepo root (e.g., with npm --prefix).
  rootDir: __dirname,
  setupFilesAfterEnv: ["<rootDir>/jest.setup.js"],
  testEnvironment: "jest-environment-jsdom",
  moduleNameMapper: {
    "^@/(.*)$": "<rootDir>/$1",
  },
  testPathIgnorePatterns: ["<rootDir>/.next/", "<rootDir>/node_modules/"],
  moduleFileExtensions: ["ts", "tsx", "js", "jsx", "json", "node"],
  collectCoverageFrom: [
    "<rootDir>/components/**/*.{js,jsx,ts,tsx}",
    "!<rootDir>/components/**/*.d.ts",
    "!<rootDir>/components/**/index.{js,ts}",
  ],
};

// createJestConfig is exported this way to ensure that next/jest can load the Next.js config which is async
// Force cache invalidation
module.exports = createJestConfig(customJestConfig);
