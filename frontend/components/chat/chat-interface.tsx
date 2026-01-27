"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2 } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Card } from "../ui/card";
import { Message, ChatState } from "../../types/chat";
import { getApiBaseUrl } from "@/lib/runtime-config";

export default function ChatInterface() {
  const [chatState, setChatState] = useState<ChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [chatState.messages]);

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || chatState.isLoading) return;

    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: content.trim(),
      timestamp: new Date(),
    };

    setChatState((prev) => ({
      ...prev,
      messages: [...prev.messages, userMessage],
      isLoading: true,
      error: null,
    }));

    setInputValue("");

    try {
      // Call the actual API
      const apiBaseUrl = getApiBaseUrl();
      const response = await fetch(`${apiBaseUrl}/api/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [{ role: "user", content: content.trim() }],
        }),
      });

      if (!response.ok) {
        throw new Error(
          `API request failed: ${response.status} ${response.statusText}`,
        );
      }

      const data = await response.json();

      // Extract the assistant message from the response
      const assistantContent =
        data.messages?.find((msg: any) => msg.role === "assistant")?.content ||
        "No response received from the assistant.";

      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: assistantContent,
        timestamp: new Date(),
      };

      setChatState((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
        isLoading: false,
      }));
    } catch (error) {
      console.error("API call failed:", error);
      setChatState((prev) => ({
        ...prev,
        isLoading: false,
        error: `Failed to send message: ${error instanceof Error ? error.message : "Unknown error"}`,
      }));
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    handleSendMessage(inputValue);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  return (
    <div className="flex flex-col h-full max-w-4xl mx-auto">
      {/* Chat Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {chatState.messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-center">
            <div className="space-y-2">
              <h2 className="text-2xl font-semibold text-muted-foreground">
                Welcome to Agentic MLOps
              </h2>
              <p className="text-muted-foreground">
                Start a conversation to design your MLOps infrastructure
              </p>
            </div>
          </div>
        )}

        {chatState.messages.map((message) => (
          <div
            key={message.id}
            className={`flex ${
              message.role === "user" ? "justify-end" : "justify-start"
            }`}
          >
            <Card
              className={`max-w-[80%] p-4 ${
                message.role === "user"
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted"
              }`}
            >
              <p className="whitespace-pre-wrap break-words">
                {message.content}
              </p>
              <span className="text-xs opacity-60 mt-2 block">
                {message.timestamp.toLocaleTimeString()}
              </span>
            </Card>
          </div>
        ))}

        {chatState.isLoading && (
          <div className="flex justify-start">
            <Card className="bg-muted p-4 flex items-center space-x-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-muted-foreground">Thinking...</span>
            </Card>
          </div>
        )}

        {chatState.error && (
          <div className="flex justify-center">
            <Card className="bg-destructive/10 border-destructive/20 p-4">
              <p className="text-destructive text-sm">{chatState.error}</p>
            </Card>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t bg-background p-4">
        <form onSubmit={handleSubmit} className="flex space-x-2">
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your MLOps requirements..."
            disabled={chatState.isLoading}
            className="flex-1"
          />
          <Button
            type="submit"
            disabled={!inputValue.trim() || chatState.isLoading}
            size="icon"
          >
            {chatState.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
      </div>
    </div>
  );
}
