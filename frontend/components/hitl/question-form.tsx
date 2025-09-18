/**
 * QuestionForm - Interactive HITL question component with auto-approval
 *
 * Features:
 * - Displays adaptive questions with smart defaults
 * - Countdown timer for auto-approval
 * - Real-time form validation
 * - Support for different question types (choice, text, boolean, numeric)
 */

import React, { useState, useEffect } from "react";
import { CheckCircle, Clock, AlertCircle } from "lucide-react";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";

export interface Question {
  question_id: string;
  question_text: string;
  question_type: "choice" | "text" | "boolean" | "numeric";
  field_targets: string[];
  priority: "high" | "medium" | "low";
  choices?: string[];
}

export interface QuestionFormProps {
  questions: Question[];
  smartDefaults: Record<string, string>;
  timeoutSeconds: number;
  onSubmit: (responses: Record<string, string>) => void;
  onAutoApprove: () => void;
  className?: string;
}

export function QuestionForm({
  questions,
  smartDefaults,
  timeoutSeconds,
  onSubmit,
  onAutoApprove,
  className = "",
}: QuestionFormProps) {
  const [responses, setResponses] = useState<Record<string, string>>(smartDefaults);
  const [remainingTime, setRemainingTime] = useState(timeoutSeconds);
  const [isSubmitted, setIsSubmitted] = useState(false);

  // Countdown timer
  useEffect(() => {
    if (remainingTime <= 0) {
      handleAutoApprove();
      return;
    }

    const timer = setTimeout(() => {
      setRemainingTime(prev => prev - 1);
    }, 1000);

    return () => clearTimeout(timer);
  }, [remainingTime]);

  const handleResponseChange = (questionId: string, value: string) => {
    setResponses(prev => ({
      ...prev,
      [questionId]: value
    }));
  };

  const handleSubmit = () => {
    if (isSubmitted) return;
    setIsSubmitted(true);
    onSubmit(responses);
  };

  const handleAutoApprove = () => {
    if (isSubmitted) return;
    setIsSubmitted(true);
    onAutoApprove();
  };

  const handleAcceptDefaults = () => {
    if (isSubmitted) return;
    setIsSubmitted(true);
    onSubmit(smartDefaults);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case "high": return "border-red-200 bg-red-50";
      case "medium": return "border-yellow-200 bg-yellow-50";
      case "low": return "border-green-200 bg-green-50";
      default: return "border-gray-200 bg-gray-50";
    }
  };

  const getTimeColor = (seconds: number) => {
    if (seconds <= 3) return "text-red-500";
    if (seconds <= 8) return "text-yellow-500";
    return "text-green-500";
  };

  if (isSubmitted) {
    return (
      <Card className={`w-full max-w-2xl mx-auto ${className}`}>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Questions Answered</span>
            <div className="flex items-center space-x-2 text-green-600">
              <CheckCircle className="h-5 w-5" />
              <span className="font-medium text-sm">Auto-approved with defaults</span>
            </div>
          </CardTitle>
          <p className="text-sm text-gray-600">
            The following answers were automatically selected using smart defaults.
          </p>
        </CardHeader>

        <CardContent className="space-y-6">
          {questions.map((question, index) => (
            <div key={question.question_id} className={`p-4 rounded-lg border ${getPriorityColor(question.priority)} opacity-80`}>
              <div className="flex items-start space-x-3">
                <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-semibold text-blue-600">
                  {index + 1}
                </div>
                <div className="flex-1 space-y-3">
                  <div>
                    <h3 className="font-medium text-gray-900">{question.question_text}</h3>
                    <div className="flex items-center space-x-2 mt-1">
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        question.priority === "high" ? "bg-red-100 text-red-800" :
                        question.priority === "medium" ? "bg-yellow-100 text-yellow-800" :
                        "bg-green-100 text-green-800"
                      }`}>
                        {question.priority} priority
                      </span>
                      <span className="text-xs text-gray-500">
                        {question.question_type}
                      </span>
                    </div>
                  </div>

                  {/* Show selected answer */}
                  <div className="bg-blue-50 border border-blue-200 rounded-md p-3">
                    <div className="text-sm text-gray-700">
                      <strong>Selected answer:</strong> {responses[question.question_id] || smartDefaults[question.question_id] || "Not specified"}
                    </div>
                    {(responses[question.question_id] === smartDefaults[question.question_id] || !responses[question.question_id]) && (
                      <div className="text-xs text-blue-600 mt-1">
                        (Used smart default)
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className={`w-full max-w-2xl mx-auto ${className}`}>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Additional Information Needed</span>
          <div className={`flex items-center space-x-2 ${getTimeColor(remainingTime)}`}>
            <Clock className="h-4 w-4" />
            <span className="font-mono text-sm">
              Auto-approving in {remainingTime}s
            </span>
          </div>
        </CardTitle>
        <p className="text-sm text-gray-600">
          Please provide the following details to optimize your MLOps architecture.
          Defaults will be auto-approved if no response is provided.
        </p>
      </CardHeader>

      <CardContent className="space-y-6">
        {questions.map((question, index) => (
          <div key={question.question_id} className={`p-4 rounded-lg border ${getPriorityColor(question.priority)}`}>
            <div className="flex items-start space-x-3">
              <div className="flex-shrink-0 w-6 h-6 bg-blue-100 rounded-full flex items-center justify-center text-xs font-semibold text-blue-600">
                {index + 1}
              </div>
              <div className="flex-1 space-y-3">
                <div>
                  <h3 className="font-medium text-gray-900">{question.question_text}</h3>
                  <div className="flex items-center space-x-2 mt-1">
                    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                      question.priority === "high" ? "bg-red-100 text-red-800" :
                      question.priority === "medium" ? "bg-yellow-100 text-yellow-800" :
                      "bg-green-100 text-green-800"
                    }`}>
                      {question.priority} priority
                    </span>
                    <span className="text-xs text-gray-500">
                      {question.question_type}
                    </span>
                  </div>
                </div>

                {/* Question input based on type */}
                {question.question_type === "choice" && question.choices && (
                  <div className="space-y-2">
                    {question.choices.map((choice) => (
                      <label key={choice} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          name={question.question_id}
                          value={choice}
                          checked={responses[question.question_id] === choice}
                          onChange={(e) => handleResponseChange(question.question_id, e.target.value)}
                          className="text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{choice}</span>
                        {smartDefaults[question.question_id] === choice && (
                          <span className="text-xs text-blue-600 font-medium">(default)</span>
                        )}
                      </label>
                    ))}
                  </div>
                )}

                {question.question_type === "boolean" && (
                  <div className="space-y-2">
                    {["true", "false"].map((value) => (
                      <label key={value} className="flex items-center space-x-2 cursor-pointer">
                        <input
                          type="radio"
                          name={question.question_id}
                          value={value}
                          checked={responses[question.question_id] === value}
                          onChange={(e) => handleResponseChange(question.question_id, e.target.value)}
                          className="text-blue-600 focus:ring-blue-500"
                        />
                        <span className="text-sm text-gray-700">{value === "true" ? "Yes" : "No"}</span>
                        {smartDefaults[question.question_id] === value && (
                          <span className="text-xs text-blue-600 font-medium">(default)</span>
                        )}
                      </label>
                    ))}
                  </div>
                )}

                {(question.question_type === "text" || question.question_type === "numeric") && (
                  <div>
                    <input
                      type={question.question_type === "numeric" ? "number" : "text"}
                      value={responses[question.question_id] || ""}
                      onChange={(e) => handleResponseChange(question.question_id, e.target.value)}
                      placeholder={`Default: ${smartDefaults[question.question_id] || "Not specified"}`}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                    />
                  </div>
                )}

                {/* Show current default */}
                <div className="text-xs text-gray-500">
                  Default answer: <span className="font-medium">{smartDefaults[question.question_id] || "None"}</span>
                </div>
              </div>
            </div>
          </div>
        ))}

        {/* Action buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t">
          <Button
            onClick={handleSubmit}
            className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
            disabled={isSubmitted}
          >
            Submit Responses
          </Button>
          <Button
            onClick={handleAcceptDefaults}
            variant="outline"
            className="flex-1"
            disabled={isSubmitted}
          >
            Accept All Defaults
          </Button>
        </div>

        {/* Auto-approval warning */}
        {remainingTime <= 5 && (
          <div className="flex items-center space-x-2 p-3 bg-yellow-50 border border-yellow-200 rounded-md">
            <AlertCircle className="h-4 w-4 text-yellow-600" />
            <span className="text-sm text-yellow-800">
              Auto-approving defaults in {remainingTime} seconds...
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default QuestionForm;