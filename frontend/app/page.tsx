"use client";

import { useState, useEffect, useRef } from "react";
import { MessageCircle, Code, GripVertical } from "lucide-react";
import ChatInterface from "../components/chat/chat-interface";
import CodeCanvas from "../components/canvas/code-canvas";

export default function Home() {
  const [leftWidth, setLeftWidth] = useState(50); // Percentage
  const [mounted, setMounted] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const handleMouseDown = () => {
    setIsDragging(true);
  };

  const handleMouseMove = (e: MouseEvent) => {
    if (!isDragging || !containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const newLeftWidth =
      ((e.clientX - containerRect.left) / containerRect.width) * 100;

    // Constrain between 20% and 80%
    const constrainedWidth = Math.max(20, Math.min(80, newLeftWidth));
    setLeftWidth(constrainedWidth);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  useEffect(() => {
    if (isDragging) {
      document.addEventListener("mousemove", handleMouseMove);
      document.addEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    } else {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    }

    return () => {
      document.removeEventListener("mousemove", handleMouseMove);
      document.removeEventListener("mouseup", handleMouseUp);
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    };
  }, [isDragging]);

  if (!mounted) {
    return null;
  }

  return (
    <main className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-background p-4">
        <h1 className="text-2xl font-bold">Agentic MLOps Platform</h1>
        <p className="text-muted-foreground text-sm">
          AI-powered MLOps infrastructure design and code generation
        </p>
      </header>

      {/* Two-Column Layout with Resizable Splitter */}
      <div className="flex-1 flex" ref={containerRef}>
        {/* Left Panel - Chat */}
        <div
          className="flex flex-col border-r bg-background"
          style={{ width: `${leftWidth}%` }}
        >
          <div className="border-b px-4 py-3">
            <div className="flex items-center gap-2">
              <MessageCircle className="h-4 w-4" />
              <span className="font-medium">Chat</span>
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            <ChatInterface />
          </div>
        </div>

        {/* Resizable Splitter */}
        <div
          className="w-1 bg-border cursor-col-resize hover:bg-primary/20 transition-colors relative group"
          onMouseDown={handleMouseDown}
        >
          <div className="absolute inset-y-0 -left-1 -right-1 flex items-center justify-center">
            <GripVertical className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors" />
          </div>
        </div>

        {/* Right Panel - Code Canvas */}
        <div
          className="flex flex-col bg-background"
          style={{ width: `${100 - leftWidth}%` }}
        >
          <div className="border-b px-4 py-3">
            <div className="flex items-center gap-2">
              <Code className="h-4 w-4" />
              <span className="font-medium">Code Repository</span>
            </div>
          </div>
          <div className="flex-1 overflow-hidden">
            <CodeCanvas />
          </div>
        </div>
      </div>
    </main>
  );
}
