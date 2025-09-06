// Optional: configure or set up a testing framework before each test.
// If you delete this file, remove `setupFilesAfterEnv` from `jest.config.js`

// Used for __tests__/testing-library.js
// Learn more: https://github.com/testing-library/jest-dom
import "@testing-library/jest-dom";

// Mock fetch for Node.js test environment
global.fetch = jest.fn(() =>
  Promise.resolve({
    ok: true,
    status: 200,
    statusText: "OK",
    json: () =>
      Promise.resolve({
        messages: [
          { role: "user", content: "Test message" },
          {
            role: "assistant",
            content: "You said: Test message. Thin slice online.",
          },
        ],
      }),
  }),
);
