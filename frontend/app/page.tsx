"use client";

import { useState, useEffect } from "react";
import EnhancedChatInterface from "../components/chat/enhanced-chat-interface";

export default function Home() {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return null; // Prevent hydration mismatch
  }

  return (
    <main className="h-screen bg-background">
      <div className="h-full flex flex-col">
        {/* Header */}
        <header className="border-b bg-card p-4">
          <div className="flex items-center justify-center space-x-2">
            <h1 className="text-2xl font-bold text-primary">
              Agentic MLOps Platform
            </h1>
          </div>
          <p className="text-center text-muted-foreground text-sm mt-1">
            AI-powered MLOps infrastructure design and code generation
          </p>
        </header>

        {/* Full-width Chat Interface */}
        <div className="flex-1 overflow-hidden">
          <EnhancedChatInterface />
        </div>
      </div>
    </main>
  );
}