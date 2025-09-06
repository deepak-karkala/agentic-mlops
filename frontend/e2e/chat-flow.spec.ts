import { test, expect } from "@playwright/test";

test.describe("End-to-End Chat Flow", () => {
  test("user can send message and receive response from deployed backend", async ({
    page,
  }) => {
    // Navigate to the deployed frontend URL
    await page.goto("/");

    // Wait for the page to load and verify we're on the right page
    await expect(page).toHaveTitle(/Agentic MLOps/);

    // Verify the welcome message is displayed
    await expect(page.getByText("Welcome to Agentic MLOps")).toBeVisible();
    await expect(
      page.getByText(
        "Start a conversation to design your MLOps infrastructure",
      ),
    ).toBeVisible();

    // Find the input field and send button
    const messageInput = page.getByPlaceholder(
      "Describe your MLOps requirements...",
    );
    const sendButton = page.getByRole("button", { name: /send/i });

    // Verify initial state: send button should be disabled
    await expect(sendButton).toBeDisabled();

    // Type a test message
    const testMessage =
      "Hello, I need help setting up an ML pipeline for my project";
    await messageInput.fill(testMessage);

    // Verify send button is now enabled
    await expect(sendButton).toBeEnabled();

    // Send the message
    await sendButton.click();

    // Verify the user message appears in the chat
    await expect(page.getByText(testMessage)).toBeVisible();

    // Verify input field is cleared after sending
    await expect(messageInput).toHaveValue("");

    // Wait for the assistant response to appear
    // The response should contain the echoed message from the thin slice backend
    const expectedResponse = `You said: ${testMessage}. Thin slice online.`;

    // Wait for the response with a reasonable timeout (30 seconds for network calls)
    await expect(page.getByText(expectedResponse)).toBeVisible({
      timeout: 30000,
    });

    // Verify we can send another message (test multiple interactions)
    const secondMessage = "Can you help with model deployment?";
    await messageInput.fill(secondMessage);
    await sendButton.click();

    // Verify second message appears
    await expect(page.getByText(secondMessage)).toBeVisible();

    // Verify second response appears
    const secondExpectedResponse = `You said: ${secondMessage}. Thin slice online.`;
    await expect(page.getByText(secondExpectedResponse)).toBeVisible({
      timeout: 30000,
    });

    // Verify we have both messages and responses visible
    await expect(page.getByText(testMessage)).toBeVisible();
    await expect(page.getByText(expectedResponse)).toBeVisible();
    await expect(page.getByText(secondMessage)).toBeVisible();
    await expect(page.getByText(secondExpectedResponse)).toBeVisible();
  });

  test("handles API errors gracefully", async ({ page }) => {
    // Mock a failed API response to test error handling
    await page.route("**/api/chat", (route) => {
      route.fulfill({
        status: 500,
        contentType: "application/json",
        body: JSON.stringify({ error: "Internal server error" }),
      });
    });

    await page.goto("/");

    // Send a message that should trigger the error
    const messageInput = page.getByPlaceholder(
      "Describe your MLOps requirements...",
    );
    const sendButton = page.getByRole("button", { name: /send/i });

    await messageInput.fill("Test error handling");
    await sendButton.click();

    // Verify error message appears
    await expect(page.getByText(/Failed to send message/)).toBeVisible({
      timeout: 10000,
    });
  });

  test("UI responsiveness on different screen sizes", async ({ page }) => {
    // Test mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");

    // Verify main elements are still visible and functional on mobile
    await expect(page.getByText("Welcome to Agentic MLOps")).toBeVisible();

    const messageInput = page.getByPlaceholder(
      "Describe your MLOps requirements...",
    );
    const sendButton = page.getByRole("button", { name: /send/i });

    await expect(messageInput).toBeVisible();
    await expect(sendButton).toBeVisible();

    // Test that we can still interact with the UI
    await messageInput.fill("Mobile test message");
    await expect(sendButton).toBeEnabled();

    // Test desktop viewport
    await page.setViewportSize({ width: 1920, height: 1080 });

    // Elements should still be visible and functional
    await expect(messageInput).toBeVisible();
    await expect(sendButton).toBeVisible();
  });

  test("keyboard navigation and accessibility", async ({ page }) => {
    await page.goto("/");

    const messageInput = page.getByPlaceholder(
      "Describe your MLOps requirements...",
    );

    // Test that we can focus the input field
    await messageInput.focus();
    await expect(messageInput).toBeFocused();

    // Test sending message with Enter key
    await messageInput.fill("Test keyboard interaction");
    await messageInput.press("Enter");

    // Verify message was sent
    await expect(page.getByText("Test keyboard interaction")).toBeVisible();

    // Wait for response
    await expect(
      page.getByText(/You said: Test keyboard interaction/),
    ).toBeVisible({ timeout: 30000 });
  });
});
