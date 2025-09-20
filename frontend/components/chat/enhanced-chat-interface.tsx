/**
 * Enhanced chat interface with real-time streaming support
 *
 * Integrates with the async API and displays streaming events in real-time
 */

"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Loader2, AlertCircle, Paperclip } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import { Badge } from "../ui/badge";
import { WorkflowVisualization } from "../streaming/workflow-visualization";
import { EnhancedChatState, EnhancedMessage } from "@/types/enhanced-chat";
import { LandingThemeConfig } from "@/data/landing-themes";
import { cn } from "@/lib/utils";

interface EnhancedChatInterfaceProps {
  pendingPrompt?: string | null;
  onPromptConsumed?: () => void;
  theme: LandingThemeConfig;
}

export default function EnhancedChatInterface({
  pendingPrompt,
  onPromptConsumed,
  theme,
}: EnhancedChatInterfaceProps) {
  const isDark = theme.id === "midnight";
  const [workflowPlan, setWorkflowPlan] = useState<string[]>([]);
  const [graphType, setGraphType] = useState<string>("");
  const [chatState, setChatState] = useState<EnhancedChatState>({
    messages: [],
    isLoading: false,
    error: null,
  });
  const [inputValue, setInputValue] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const jobPollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    let isMounted = true;

    const fetchWorkflowPlan = async () => {
      try {
        const apiBaseUrl =
          process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
        const response = await fetch(`${apiBaseUrl}/api/workflow/plan`);
        if (!response.ok) {
          throw new Error(`Failed to fetch workflow plan: ${response.status}`);
        }

        const data: { nodes?: string[]; graph_type?: string } =
          await response.json();
        if (!isMounted) return;

        setWorkflowPlan(data.nodes ?? []);
        setGraphType(data.graph_type ?? "");
      } catch (error) {
        console.error("Failed to load workflow plan", error);
      }
    };

    fetchWorkflowPlan();

    return () => {
      isMounted = false;
    };
  }, []);

  const [autoScrollEnabled, setAutoScrollEnabled] = useState(true);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    if (autoScrollEnabled) {
      scrollToBottom();
    }
  }, [chatState.messages, autoScrollEnabled]);

  // Clean up polling on unmount
  useEffect(() => {
    return () => {
      if (jobPollingIntervalRef.current) {
        clearInterval(jobPollingIntervalRef.current);
        jobPollingIntervalRef.current = null;
      }
    };
  }, []);

  useEffect(() => {
    if (pendingPrompt && pendingPrompt.trim()) {
      handleSendMessage(pendingPrompt);
      onPromptConsumed?.();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [pendingPrompt, onPromptConsumed]);

  // Poll job status
  const pollJobStatus = async (jobId: string, decisionSetId: string) => {
    const apiBaseUrl =
      process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";

    try {
      const response = await fetch(`${apiBaseUrl}/api/jobs/${jobId}/status`);
      if (!response.ok) {
        throw new Error(`Job status check failed: ${response.status}`);
      }

      const jobStatus = await response.json();

      // Update message with job status
      setChatState((prev) => ({
        ...prev,
        messages: prev.messages.map((msg) =>
          msg.jobId === jobId
            ? {
                ...msg,
                jobStatus: jobStatus.status,
                isStreamingActive: jobStatus.status === "processing",
              }
            : msg,
        ),
      }));

      // Stop polling if job is complete or failed
      if (jobStatus.status === "completed" || jobStatus.status === "failed") {
        // Clear the interval immediately to stop further polling
        if (jobPollingIntervalRef.current) {
          clearInterval(jobPollingIntervalRef.current);
          jobPollingIntervalRef.current = null;
        }

        setChatState((prev) => ({
          ...prev,
          isLoading: false,
        }));

        // If completed, add a completion message (only if not already added)
        if (jobStatus.status === "completed") {
          setChatState((prev) => {
            // Check if completion message already exists for this jobId
            const hasCompletionMessage = prev.messages.some(
              (msg) =>
                msg.content.includes("MLOps architecture design completed") &&
                msg.decisionSetId === decisionSetId,
            );

            if (!hasCompletionMessage) {
              const completionMessage: EnhancedMessage = {
                id: Date.now().toString(),
                role: "assistant",
                content:
                  "✅ MLOps architecture design completed! The workflow has finished successfully.",
                timestamp: new Date(),
                decisionSetId,
              };

              return {
                ...prev,
                messages: [...prev.messages, completionMessage],
              };
            }

            return prev;
          });
        }
      }
    } catch (error) {
      console.error("Job status polling failed:", error);
      // Stop polling on error
      if (jobPollingIntervalRef.current) {
        clearInterval(jobPollingIntervalRef.current);
        jobPollingIntervalRef.current = null;
      }

      setChatState((prev) => ({
        ...prev,
        isLoading: false,
        error: `Job tracking failed: ${error instanceof Error ? error.message : "Unknown error"}`,
      }));
    }
  };

  const handleSendMessage = async (content: string) => {
    if (!content.trim() || chatState.isLoading) return;

    const userMessage: EnhancedMessage = {
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
      // Call the async API
      const apiBaseUrl =
        process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
      const response = await fetch(`${apiBaseUrl}/api/chat/async`, {
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
      const { decision_set_id, thread_id, job_id, status } = data;

      // Create system message about job creation
      const systemMessage: EnhancedMessage = {
        id: (Date.now() + 1).toString(),
        role: "assistant",
        content: `🚀 Started MLOps architecture design workflow! You can track real-time progress in the panel below.

**Job Details:**
- Decision Set ID: ${decision_set_id}
- Job ID: ${job_id}
- Status: ${status}

Watch the Real-time Updates panel for live agent reasoning and progress updates.`,
        timestamp: new Date(),
        decisionSetId: decision_set_id,
        jobId: job_id,
        jobStatus: status,
        isStreamingActive: true,
      };

      setChatState((prev) => ({
        ...prev,
        messages: [...prev.messages, systemMessage],
        currentDecisionSetId: decision_set_id,
        isLoading: status === "completed", // Keep loading if not yet completed
      }));

      // Start job status polling
      jobPollingIntervalRef.current = setInterval(() => {
        pollJobStatus(job_id, decision_set_id);
      }, 3000); // Poll every 3 seconds
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

  // Get job status badge info
  const getJobStatusBadge = (status?: string) => {
    switch (status) {
      case "pending":
        return {
          variant: "outline" as const,
          color: "text-yellow-600",
          text: "Pending",
        };
      case "processing":
        return {
          variant: "default" as const,
          color: "text-blue-600",
          text: "Processing",
        };
      case "completed":
        return {
          variant: "outline" as const,
          color: "text-green-600",
          text: "Completed",
        };
      case "failed":
        return {
          variant: "destructive" as const,
          color: "text-red-600",
          text: "Failed",
        };
      default:
        return {
          variant: "secondary" as const,
          color: "text-gray-600",
          text: status || "Unknown",
        };
    }
  };

  return (
    <div
      className="flex h-full max-w-full flex-col"
      onWheel={() => setAutoScrollEnabled(false)}
      onTouchStart={() => setAutoScrollEnabled(false)}
    >
      {/* Chat Messages */}
      <div className="flex-1 space-y-4 overflow-y-auto p-6">
        {chatState.messages.length === 0 && (
          <div className="flex h-full items-center justify-center text-center">
            <div className={cn(theme.chat.emptyState, "max-w-md text-left")}
            >
              <h2 className="font-display text-xl text-espresso">Welcome to Agentic MLOps</h2>
              <p className="text-sm leading-relaxed text-espresso/70">
                Ask for an architecture blueprint or paste requirements to watch our agents collaborate in real time. Attach context or guardrails below before you send.
              </p>
            </div>
          </div>
        )}

        {chatState.messages.map((message, index) => {
          // Track which decisionSetIds have already rendered workflow insights
          const isFirstMessageWithDecisionSetId =
            message.role === "assistant" &&
            message.decisionSetId &&
            !chatState.messages
              .slice(0, index)
              .some((m) => m.decisionSetId === message.decisionSetId);

          return (
            <div key={message.id} className="space-y-2">
              <div
                className={cn(
                  "flex",
                  message.role === "user" ? "justify-end" : "justify-start",
                )}
              >
                <div
                  className={cn(
                    "max-w-[78%] rounded-[1.75rem] px-5 py-4 leading-relaxed shadow-sm",
                    message.role === "user"
                      ? cn(theme.chat.userBubble, "text-sm text-espresso")
                      : cn(
                          theme.chat.assistantBubble,
                          "text-sm text-espresso/80",
                        ),
                  )}
                >
                  <p className="whitespace-pre-wrap break-words">
                    {message.content}
                  </p>
                  <div className="mt-3 flex items-center justify-between text-[0.7rem] uppercase tracking-[0.2em] text-espresso/45">
                    <span>
                      {message.timestamp.toLocaleTimeString()}
                    </span>
                    {message.jobStatus && (
                      <Badge
                        variant={getJobStatusBadge(message.jobStatus).variant}
                        className="flex items-center gap-1 rounded-full border-espresso/20 bg-white/80 px-3 py-1 text-[0.62rem] font-semibold uppercase tracking-[0.2em]"
                      >
                        {message.isStreamingActive && (
                          <span className="h-2 w-2 rounded-full bg-current animate-pulse" />
                        )}
                        {getJobStatusBadge(message.jobStatus).text}
                      </Badge>
                    )}
                  </div>
                </div>
              </div>

              {/* Show workflow container only for the first assistant message with each decisionSetId */}
              {isFirstMessageWithDecisionSetId && (
                <div className="ml-4">
                  <WorkflowVisualization
                    decisionSetId={message.decisionSetId!}
                    plan={workflowPlan}
                    graphType={graphType}
                    className="mt-3"
                  />
                </div>
              )}
            </div>
          );
        })}

        {chatState.isLoading && (
          <div className="flex justify-start">
            <div className={cn("flex items-center gap-3 rounded-2xl px-5 py-3", theme.chat.loader)}>
              <Loader2 className="h-4 w-4 animate-spin" />
              <span className="text-sm text-espresso/60">Processing workflow...</span>
            </div>
          </div>
        )}

        {chatState.error && (
          <div className="flex justify-center">
            <div className="flex items-center gap-2 rounded-2xl border border-red-200 bg-red-50/80 px-4 py-3 text-sm text-red-600">
              <AlertCircle className="h-4 w-4" />
              <p>{chatState.error}</p>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Form */}
      <div className="border-t border-espresso/10 bg-white/80 p-5">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 rounded-full border border-espresso/15 bg-sand/80 px-4 py-2 text-xs text-espresso/60">
              <Paperclip className="h-4 w-4" />
              Add context or guardrails (drag & drop coming soon)
            </div>
          </div>
          <Input
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Describe your MLOps requirements..."
            disabled={chatState.isLoading}
            className={cn(
              "flex-1 rounded-[1.75rem] border border-espresso/12 bg-white/90 px-5 py-5 text-sm text-espresso shadow-sm placeholder:text-espresso/40 focus-visible:ring-2 focus-visible:ring-accentOrange/60",
            )}
          />
          <Button
            type="submit"
            variant="accent"
            disabled={!inputValue.trim() || chatState.isLoading}
            className="flex w-full items-center justify-center gap-2 rounded-full px-6 py-4 text-sm font-semibold transition hover:-translate-y-0.5"
          >
            {chatState.isLoading ? (
              <Loader2 className="h-4 w-4 animate-spin" />
            ) : (
              <Send className="h-4 w-4" />
            )}
          </Button>
        </form>
        <p className="mt-3 text-xs uppercase tracking-[0.28em] text-espresso/40">
          Track nodes, reason cards, and streaming status in the workflow timeline above.
        </p>
      </div>
    </div>
  );
}
