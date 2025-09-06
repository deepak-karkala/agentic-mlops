import { render, screen, fireEvent, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import ChatInterface from "../chat-interface";

// Mock the lucide-react icons
jest.mock("lucide-react", () => ({
  Send: () => <div data-testid="send-icon" />,
  Loader2: () => <div data-testid="loader-icon" />,
}));

describe("ChatInterface", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Mock scrollIntoView since it's not implemented in JSDOM
    Element.prototype.scrollIntoView = jest.fn();
  });

  it("renders welcome message when no messages exist", () => {
    render(<ChatInterface />);

    expect(screen.getByText("Welcome to Agentic MLOps")).toBeInTheDocument();
    expect(
      screen.getByText(
        "Start a conversation to design your MLOps infrastructure",
      ),
    ).toBeInTheDocument();
  });

  it("renders input field and send button", () => {
    render(<ChatInterface />);

    expect(
      screen.getByPlaceholderText("Describe your MLOps requirements..."),
    ).toBeInTheDocument();
    expect(screen.getByRole("button")).toBeInTheDocument();
  });

  it("updates input value when typing", async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "Describe your MLOps requirements...",
    );
    await user.type(input, "Hello world");

    expect(input).toHaveValue("Hello world");
  });

  it("disables send button when input is empty", () => {
    render(<ChatInterface />);

    const sendButton = screen.getByRole("button");
    expect(sendButton).toBeDisabled();
  });

  it("enables send button when input has content", async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "Describe your MLOps requirements...",
    );
    await user.type(input, "Hello");

    const sendButton = screen.getByRole("button");
    expect(sendButton).not.toBeDisabled();
  });

  it("sends message and shows loading state", async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "Describe your MLOps requirements...",
    );
    await user.type(input, "Test message");

    const sendButton = screen.getByRole("button");
    await user.click(sendButton);

    // Check that the user message appears
    expect(screen.getByText("Test message")).toBeInTheDocument();

    // Input should be cleared
    expect(input).toHaveValue("");
  });

  it("sends message on Enter key press", async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "Describe your MLOps requirements...",
    );
    await user.type(input, "Test message{enter}");

    expect(screen.getByText("Test message")).toBeInTheDocument();
  });

  it("shows assistant response after loading", async () => {
    const user = userEvent.setup();
    render(<ChatInterface />);

    const input = screen.getByPlaceholderText(
      "Describe your MLOps requirements...",
    );
    await user.type(input, "Test message");

    const sendButton = screen.getByRole("button");
    await user.click(sendButton);

    // Wait for the assistant response to appear
    await waitFor(() => {
      expect(
        screen.getByText(/You said: Test message. Thin slice online./),
      ).toBeInTheDocument();
    });
  });
});
