"use client";

import { MessageCircle, Code } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import ChatInterface from "@/components/chat/chat-interface";
import CodeCanvas from "@/components/canvas/code-canvas";

export default function Home() {
  return (
    <main className="h-screen flex flex-col">
      {/* Header */}
      <header className="border-b bg-background p-4">
        <h1 className="text-2xl font-bold">Agentic MLOps Platform</h1>
        <p className="text-muted-foreground text-sm">
          AI-powered MLOps infrastructure design and code generation
        </p>
      </header>

      {/* Main Content with Tabs */}
      <div className="flex-1 overflow-hidden">
        <Tabs defaultValue="chat" className="h-full">
          <div className="border-b">
            <TabsList className="h-12 w-full justify-start rounded-none bg-transparent p-0">
              <TabsTrigger
                value="chat"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                <MessageCircle className="h-4 w-4 mr-2" />
                Chat
              </TabsTrigger>
              <TabsTrigger
                value="canvas"
                className="rounded-none border-b-2 border-transparent data-[state=active]:border-primary data-[state=active]:bg-transparent"
              >
                <Code className="h-4 w-4 mr-2" />
                Code Repository
              </TabsTrigger>
            </TabsList>
          </div>

          <TabsContent value="chat" className="h-full m-0">
            <ChatInterface />
          </TabsContent>

          <TabsContent value="canvas" className="h-full m-0">
            <CodeCanvas />
          </TabsContent>
        </Tabs>
      </div>
    </main>
  );
}
