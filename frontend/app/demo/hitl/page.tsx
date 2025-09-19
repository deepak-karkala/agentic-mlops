/**
 * HITL Demo Page - Showcase the Human-in-the-Loop functionality
 *
 * This page demonstrates the enhanced HITL features:
 * - Interactive question forms
 * - Smart defaults
 * - Auto-approval mechanism
 * - Real-time countdown
 */

"use client";

import React, { useState } from "react";
import { RefreshCw, PlayCircle, CheckCircle } from "lucide-react";
import { Button } from "../../../components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../../../components/ui/card";
import QuestionForm, { Question } from "../../../components/hitl/question-form";

// Demo data from our mock infrastructure
const demoQuestions: Question[] = [
  {
    question_id: "demo_q1_budget",
    question_text: "What's your monthly budget range for this MLOps platform?",
    field_targets: ["budget_band", "monthly_budget_limit"],
    priority: "high",
    question_type: "choice",
    choices: [
      "Startup budget (under $500/month)",
      "Growth budget ($500-1500/month)",
      "Enterprise budget ($1500+/month)"
    ]
  },
  {
    question_id: "demo_q2_scale",
    question_text: "What's your expected daily request volume?",
    field_targets: ["expected_requests_per_day", "scale_requirements"],
    priority: "high",
    question_type: "choice",
    choices: [
      "Light usage (under 1,000 requests/day)",
      "Moderate usage (1,000-10,000 requests/day)",
      "Heavy usage (10,000+ requests/day)"
    ]
  },
  {
    question_id: "demo_q3_compliance",
    question_text: "Do you handle any regulated or sensitive data (GDPR, HIPAA, financial)?",
    field_targets: ["data_classification", "compliance_requirements"],
    priority: "high",
    question_type: "boolean"
  }
];

const demoSmartDefaults = {
  "demo_q1_budget": "Growth budget ($500-1500/month)",
  "demo_q2_scale": "Moderate usage (1,000-10,000 requests/day)",
  "demo_q3_compliance": "false"
};

export default function HITLDemoPage() {
  const [demoState, setDemoState] = useState<"idle" | "questions" | "completed">("idle");
  const [responses, setResponses] = useState<Record<string, string>>({});
  const [approvalMethod, setApprovalMethod] = useState<"user" | "auto" | "defaults">("");
  const [timeoutSeconds, setTimeoutSeconds] = useState(8);

  const startDemo = () => {
    setDemoState("questions");
    setResponses({});
    setApprovalMethod("");
  };

  const handleSubmit = (userResponses: Record<string, string>) => {
    setResponses(userResponses);
    setApprovalMethod("user");
    setDemoState("completed");
  };

  const handleAutoApprove = () => {
    setResponses(demoSmartDefaults);
    setApprovalMethod("auto");
    setDemoState("completed");
  };

  const resetDemo = () => {
    setDemoState("idle");
    setResponses({});
    setApprovalMethod("");
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Human-in-the-Loop Demo
          </h1>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            Experience the enhanced HITL functionality with smart defaults,
            auto-approval, and real-time interaction. This demo showcases how
            the system presents questions and handles user responses.
          </p>
        </div>

        {/* Demo Controls */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Demo Configuration</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center space-x-4">
              <label className="text-sm font-medium text-gray-700">
                Auto-approval timeout:
              </label>
              <select
                value={timeoutSeconds}
                onChange={(e) => setTimeoutSeconds(Number(e.target.value))}
                className="px-3 py-1 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                disabled={demoState === "questions"}
              >
                <option value={3}>3 seconds (Demo mode)</option>
                <option value={8}>8 seconds (Default)</option>
                <option value={15}>15 seconds (Interactive)</option>
                <option value={0}>Disabled (Immediate)</option>
              </select>
            </div>

            <div className="flex space-x-3">
              <Button
                onClick={startDemo}
                disabled={demoState === "questions"}
                className="flex items-center space-x-2"
              >
                <PlayCircle className="h-4 w-4" />
                <span>Start HITL Demo</span>
              </Button>

              {demoState !== "idle" && (
                <Button
                  onClick={resetDemo}
                  variant="outline"
                  className="flex items-center space-x-2"
                >
                  <RefreshCw className="h-4 w-4" />
                  <span>Reset Demo</span>
                </Button>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Demo Content */}
        {demoState === "idle" && (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center py-12">
                <PlayCircle className="h-16 w-16 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  Ready to Start Demo
                </h3>
                <p className="text-gray-600 mb-6">
                  Click "Start HITL Demo" to see the enhanced Human-in-the-Loop functionality in action.
                </p>
                <div className="bg-blue-50 p-4 rounded-lg text-left max-w-md mx-auto">
                  <h4 className="font-medium text-blue-900 mb-2">What you'll see:</h4>
                  <ul className="text-sm text-blue-800 space-y-1">
                    <li>• 3 adaptive questions with smart defaults</li>
                    <li>• Real-time countdown timer</li>
                    <li>• Auto-approval mechanism</li>
                    <li>• Response collection and processing</li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {demoState === "questions" && (
          <QuestionForm
            questions={demoQuestions}
            smartDefaults={demoSmartDefaults}
            timeoutSeconds={timeoutSeconds}
            onSubmit={handleSubmit}
            onAutoApprove={handleAutoApprove}
          />
        )}

        {demoState === "completed" && (
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center space-x-2 text-green-600">
                <CheckCircle className="h-5 w-5" />
                <span>Demo Completed Successfully</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Approval Method */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Approval Method</h3>
                  <div className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                    approvalMethod === "user" ? "bg-green-100 text-green-800" :
                    approvalMethod === "auto" ? "bg-blue-100 text-blue-800" :
                    "bg-gray-100 text-gray-800"
                  }`}>
                    {approvalMethod === "user" ? "User Submitted" :
                     approvalMethod === "auto" ? "Auto-Approved" :
                     "Defaults Accepted"}
                  </div>
                </div>

                {/* Response Count */}
                <div className="p-4 bg-gray-50 rounded-lg">
                  <h3 className="font-medium text-gray-900 mb-2">Responses Collected</h3>
                  <div className="text-2xl font-bold text-blue-600">
                    {Object.keys(responses).length}
                  </div>
                </div>
              </div>

              {/* Collected Responses */}
              <div>
                <h3 className="font-medium text-gray-900 mb-4">Collected Responses</h3>
                <div className="space-y-3">
                  {demoQuestions.map((question) => {
                    const response = responses[question.question_id];
                    const isDefault = response === demoSmartDefaults[question.question_id];

                    return (
                      <div key={question.question_id} className="p-3 border border-gray-200 rounded-lg">
                        <div className="font-medium text-gray-900 text-sm mb-1">
                          {question.question_text}
                        </div>
                        <div className="flex items-center space-x-2">
                          <span className="text-gray-700">{response || "No response"}</span>
                          {isDefault && (
                            <span className="text-xs text-blue-600 bg-blue-100 px-2 py-0.5 rounded">
                              Default
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Next Steps */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">Next Steps in Real Workflow</h3>
                <p className="text-blue-800 text-sm">
                  In the actual MLOps workflow, these responses would be integrated back into the
                  intake_extract agent, improving the constraint coverage and enabling the system
                  to generate a more accurate architecture plan.
                </p>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Technical Details */}
        <Card className="mt-8">
          <CardHeader>
            <CardTitle>Technical Implementation</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm">
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Backend Features</h3>
                <ul className="space-y-1 text-gray-600">
                  <li>• Enhanced HITL graph with loop-back flow</li>
                  <li>• Smart defaults generation based on context</li>
                  <li>• Configurable auto-approval timeouts</li>
                  <li>• In-place state updates (no duplicates)</li>
                  <li>• Context preservation across agent re-execution</li>
                  <li>• Real-time SSE events for UI updates</li>
                </ul>
              </div>
              <div>
                <h3 className="font-medium text-gray-900 mb-2">Frontend Features</h3>
                <ul className="space-y-1 text-gray-600">
                  <li>• Interactive question forms with validation</li>
                  <li>• Real-time countdown timer</li>
                  <li>• Support for multiple question types</li>
                  <li>• Visual priority indicators</li>
                  <li>• Responsive design for mobile/desktop</li>
                  <li>• Accessibility-compliant UI components</li>
                </ul>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}