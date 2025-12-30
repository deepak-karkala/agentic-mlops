# Part 3: Architecture Deep Dive
# Agentic MLOps Platform

**Version:** 1.0
**Date:** January 2025
**Classification:** Architecture Deep Dive

---

## Table of Contents
1. [Frontend Architecture](#1-frontend-architecture)
2. [Backend Architecture](#2-backend-architecture)
3. [Project Structure](#3-project-structure)
4. [Development Workflow](#4-development-workflow)

---

## 1. Frontend Architecture

### 1.1 Next.js App Router Architecture

#### 1.1.1 Application Structure

```
frontend/
├── app/                          # Next.js 14 App Router
│   ├── layout.tsx               # Root layout with metadata
│   ├── page.tsx                 # Landing page with hero + templates
│   ├── globals.css              # Global styles and Tailwind
│   └── demo/
│       └── hitl/
│           └── page.tsx         # HITL demo page
├── components/                   # React components
│   ├── chat/                    # Chat interface components
│   │   ├── enhanced-chat-interface.tsx
│   │   └── chat-interface.tsx
│   ├── streaming/               # Real-time streaming components
│   │   ├── workflow-visualization.tsx
│   │   ├── reason-card.tsx
│   │   ├── workflow-status-panel.tsx
│   │   ├── workflow-progress.tsx
│   │   └── workflow-step.tsx
│   ├── templates/               # Template gallery components
│   │   ├── template-showcase.tsx
│   │   └── template-card.tsx
│   ├── landing/                 # Landing page components
│   │   └── hero-section.tsx
│   ├── hitl/                    # HITL components
│   │   └── question-form.tsx
│   └── ui/                      # Reusable UI primitives
│       ├── button.tsx
│       ├── card.tsx
│       ├── badge.tsx
│       ├── input.tsx
│       └── tabs.tsx
├── hooks/                       # Custom React hooks
│   └── useStreamingEvents.ts   # SSE streaming hook
├── data/                        # Static data and configurations
│   ├── mlops-templates.ts      # Curated templates
│   └── landing-themes.ts       # Theme configurations
├── lib/                         # Utility functions
│   └── utils.ts                # Tailwind class merging, etc.
└── public/                      # Static assets
    └── images/
```

#### 1.1.2 Page Architecture

**Root Layout (app/layout.tsx):**
```typescript
import type { Metadata } from "next";
import { Inter } from "next/font/google";
import localFont from "next/font/local";
import "./globals.css";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });
const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});

export const metadata: Metadata = {
  title: "Agentic MLOps Platform",
  description: "AI-powered MLOps system design and generation",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={`${inter.variable} ${geistSans.variable} antialiased`}>
        {children}
      </body>
    </html>
  );
}
```

**Landing Page (app/page.tsx):**
```typescript
"use client";

export default function Home() {
  const [mode, setMode] = useState<"idle" | "template" | "live">("idle");
  const [themeId, setThemeId] = useState<LandingThemeId>("claude");
  const [activeTemplate, setActiveTemplate] = useState<MlopsTemplate | null>(null);
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);

  // Three-section layout:
  // 1. Hero Section: Value proposition + CTA
  // 2. Template Gallery: Curated MLOps templates (2-column grid)
  // 3. Chat Interface: Interactive chat or template showcase

  return (
    <div className={cn("min-h-screen", theme.page.background)}>
      {/* Hero Section */}
      <HeroSection
        theme={theme}
        onExploreTemplates={handleExploreTemplates}
        onStartCustom={handleStartCustom}
      />

      {/* Template Gallery */}
      <section className="container mx-auto px-4 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {templates.map((template) => (
            <TemplateCard
              key={template.id}
              template={template}
              isSelected={template.id === selectedTemplateId}
              onClick={() => handleTemplateSelect(template.id)}
            />
          ))}
        </div>
      </section>

      {/* Chat Section */}
      <section ref={chatSectionRef} className="container mx-auto px-4 py-12">
        {mode === "idle" && <TemplateShowcase />}
        {mode === "template" && activeTemplate && (
          <TemplateShowcase template={activeTemplate} />
        )}
        {mode === "live" && (
          <EnhancedChatInterface
            pendingPrompt={pendingPrompt}
            onPromptConsumed={handlePromptConsumed}
          />
        )}
      </section>
    </div>
  );
}
```

#### 1.1.3 Component Architecture Patterns

**Container/Presentational Pattern:**

```typescript
// Container Component (Smart)
// frontend/components/chat/enhanced-chat-interface.tsx
export function EnhancedChatInterface({ pendingPrompt, onPromptConsumed }) {
  // State management
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [jobId, setJobId] = useState<string | null>(null);
  const [decisionSetId, setDecisionSetId] = useState<string | null>(null);

  // API integration
  const handleSendMessage = async () => {
    const response = await fetch(`${API_BASE_URL}/api/chat/async`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: [...messages, userMessage] }),
    });
    const data = await response.json();
    setJobId(data.job_id);
    setDecisionSetId(data.decision_set_id);
  };

  // Render presentational components
  return (
    <div className="chat-container">
      <MessageList messages={messages} />
      <MessageInput value={input} onChange={setInput} onSend={handleSendMessage} />
      {decisionSetId && <WorkflowVisualization decisionSetId={decisionSetId} />}
    </div>
  );
}

// Presentational Component (Dumb)
// frontend/components/chat/message-list.tsx
export function MessageList({ messages }: { messages: Message[] }) {
  return (
    <div className="space-y-4">
      {messages.map((msg, idx) => (
        <MessageBubble key={idx} message={msg} />
      ))}
    </div>
  );
}
```

**Compound Component Pattern:**

```typescript
// Compound component for reason cards
// frontend/components/streaming/reason-card.tsx
export function ReasonCard({ agent, reasoning, confidence, inputs, outputs }: ReasonCardProps) {
  return (
    <Card>
      <ReasonCard.Header agent={agent} confidence={confidence} />
      <ReasonCard.Body reasoning={reasoning} />
      <ReasonCard.Details inputs={inputs} outputs={outputs} />
    </Card>
  );
}

ReasonCard.Header = function Header({ agent, confidence }) {
  return (
    <div className="flex justify-between">
      <h4>{agent}</h4>
      <Badge variant={confidence > 0.8 ? "success" : "warning"}>
        {(confidence * 100).toFixed(0)}%
      </Badge>
    </div>
  );
};

ReasonCard.Body = function Body({ reasoning }) {
  return <p className="text-gray-600">{reasoning}</p>;
};

ReasonCard.Details = function Details({ inputs, outputs }) {
  const [isExpanded, setIsExpanded] = useState(false);
  return (
    <>
      {isExpanded && (
        <div>
          <CollapsibleSection title="Inputs" content={inputs} />
          <CollapsibleSection title="Outputs" content={outputs} />
        </div>
      )}
      <button onClick={() => setIsExpanded(!isExpanded)}>
        {isExpanded ? "Show less" : "Show more"}
      </button>
    </>
  );
};
```

### 1.2 State Management Strategy

#### 1.2.1 Component-Level State

**Local State with useState:**
```typescript
// Chat interface state
const [messages, setMessages] = useState<Message[]>([]);
const [input, setInput] = useState("");
const [isLoading, setIsLoading] = useState(false);

// Workflow visualization state
const [reasonCards, setReasonCards] = useState<ReasonCard[]>([]);
const [completedNodes, setCompletedNodes] = useState<Set<string>>(new Set());

// Template selection state
const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(null);
```

#### 1.2.2 Server State Management

**Custom Hook for SSE Streaming:**
```typescript
// frontend/hooks/useStreamingEvents.ts
export function useStreamingEvents({ decisionSetId, autoConnect = true }) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);
  const seenEventIds = useRef<Set<string>>(new Set());

  useEffect(() => {
    if (!autoConnect || !decisionSetId) return;

    const apiBaseUrl = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000";
    const eventSource = new EventSource(`${apiBaseUrl}/api/streams/${decisionSetId}`);

    eventSource.onopen = () => {
      console.log("SSE connection established");
      setIsConnected(true);
      setError(null);
    };

    eventSource.onerror = (err) => {
      console.error("SSE connection error:", err);
      setIsConnected(false);
      setError("Connection lost. Reconnecting...");
    };

    // Listen for specific event types
    const eventTypes = [
      "reason-card",
      "node-start",
      "node-complete",
      "workflow-paused",
      "workflow-resumed",
      "questions-presented",
      "workflow-complete",
      "error",
      "heartbeat",
    ];

    eventTypes.forEach((eventType) => {
      eventSource.addEventListener(eventType, (e) => {
        const event = JSON.parse(e.data);

        // Deduplication: Use event type + decision_set_id + timestamp as key
        const eventKey = `${event.type}-${event.decision_set_id}-${event.timestamp}`;

        if (!seenEventIds.current.has(eventKey)) {
          seenEventIds.current.add(eventKey);
          setEvents((prev) => [...prev, event]);
        }
      });
    });

    eventSourceRef.current = eventSource;

    return () => {
      console.log("Closing SSE connection");
      eventSource.close();
    };
  }, [decisionSetId, autoConnect]);

  return { events, isConnected, error };
}
```

**Polling for Job Status:**
```typescript
// frontend/components/chat/enhanced-chat-interface.tsx
useEffect(() => {
  if (!jobId) return;

  const pollInterval = setInterval(async () => {
    const response = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/status`);
    const data = await response.json();

    setJobStatus(data.status);

    if (data.status === "completed" || data.status === "failed") {
      clearInterval(pollInterval);
    }
  }, 2000); // Poll every 2 seconds

  return () => clearInterval(pollInterval);
}, [jobId]);
```

#### 1.2.3 URL State Management

**Next.js Router for Navigation:**
```typescript
import { useRouter, useSearchParams } from "next/navigation";

function DemoPage() {
  const router = useRouter();
  const searchParams = useSearchParams();

  const templateId = searchParams.get("template");
  const mode = searchParams.get("mode") || "idle";

  const handleTemplateSelect = (id: string) => {
    router.push(`/?template=${id}&mode=template`);
  };

  return <TemplateGallery onSelect={handleTemplateSelect} />;
}
```

### 1.3 Real-Time Communication Architecture

#### 1.3.1 Server-Sent Events (SSE) Integration

**EventSource Connection Management:**
```typescript
// frontend/hooks/useStreamingEvents.ts

// Connection lifecycle management
const eventSource = new EventSource(streamUrl);

// Connection states
eventSource.onopen = () => setIsConnected(true);
eventSource.onerror = () => {
  setIsConnected(false);
  // Automatic reconnection by browser
};

// Event handlers for different event types
eventSource.addEventListener("reason-card", (e) => {
  const reasonCard = JSON.parse(e.data);
  setReasonCards((prev) => [...prev, reasonCard.data]);
});

eventSource.addEventListener("node-complete", (e) => {
  const event = JSON.parse(e.data);
  setCompletedNodes((prev) => new Set([...prev, event.data.node]));
});

eventSource.addEventListener("workflow-complete", (e) => {
  console.log("Workflow completed!");
  setIsWorkflowComplete(true);
});

// Cleanup on unmount
return () => eventSource.close();
```

**Event Deduplication Strategy:**
```typescript
// Client-side deduplication using Map
const seenEventIds = useRef<Set<string>>(new Set());

const handleEvent = (event: StreamEvent) => {
  // Create unique key from event properties
  const eventKey = `${event.type}-${event.decision_set_id}-${event.timestamp}`;

  // Only process if not seen before
  if (!seenEventIds.current.has(eventKey)) {
    seenEventIds.current.add(eventKey);
    setEvents((prev) => [...prev, event]);

    // Cleanup old entries to prevent memory leak
    if (seenEventIds.current.size > 1000) {
      const entries = Array.from(seenEventIds.current);
      seenEventIds.current = new Set(entries.slice(-500));
    }
  }
};
```

**Reconnection Handling:**
```typescript
// Automatic reconnection with exponential backoff
const [reconnectAttempts, setReconnectAttempts] = useState(0);

eventSource.onerror = () => {
  setIsConnected(false);

  // Exponential backoff: 1s, 2s, 4s, 8s, max 30s
  const backoffTime = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);

  setTimeout(() => {
    setReconnectAttempts((prev) => prev + 1);
    // Browser automatically reconnects EventSource
  }, backoffTime);
};

eventSource.onopen = () => {
  setIsConnected(true);
  setReconnectAttempts(0); // Reset on successful connection
};
```

### 1.4 Styling Architecture

#### 1.4.1 Tailwind CSS Configuration

```typescript
// tailwind.config.ts
import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Custom color palette
        espresso: {
          DEFAULT: "#2D1B00",
          50: "#F5F0E8",
          100: "#E6D9C7",
          // ... more shades
        },
        sand: {
          DEFAULT: "#F5E6D3",
          50: "#FFFBF5",
          // ... more shades
        },
        accentOrange: {
          DEFAULT: "#E67E22",
          50: "#FDF4ED",
          // ... more shades
        },
      },
      fontFamily: {
        display: ["var(--font-geist-sans)", "sans-serif"],
        body: ["var(--font-inter)", "sans-serif"],
      },
      animation: {
        "fade-in": "fadeIn 0.3s ease-in",
        "slide-up": "slideUp 0.4s ease-out",
        pulse: "pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite",
      },
      keyframes: {
        fadeIn: {
          "0%": { opacity: "0" },
          "100%": { opacity: "1" },
        },
        slideUp: {
          "0%": { transform: "translateY(10px)", opacity: "0" },
          "100%": { transform: "translateY(0)", opacity: "1" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
```

#### 1.4.2 Theme System

```typescript
// frontend/data/landing-themes.ts
export interface LandingTheme {
  id: string;
  name: string;
  page: {
    background: string;
    text: string;
  };
  hero: {
    title: string;
    subtitle: string;
    gradient: string;
  };
  card: {
    background: string;
    border: string;
    shadow: string;
    hover: string;
  };
  button: {
    primary: string;
    secondary: string;
    text: string;
  };
}

export const LANDING_THEMES: Record<LandingThemeId, LandingTheme> = {
  claude: {
    id: "claude",
    name: "Claude",
    page: {
      background: "bg-gradient-to-br from-sand-50 via-white to-espresso-50",
      text: "text-espresso-900",
    },
    hero: {
      title: "text-espresso-900",
      subtitle: "text-espresso-700",
      gradient: "from-accentOrange-500 to-espresso-800",
    },
    card: {
      background: "bg-white/80 backdrop-blur-sm",
      border: "border-espresso-200",
      shadow: "shadow-lg shadow-espresso-200/20",
      hover: "hover:shadow-xl hover:shadow-espresso-200/30",
    },
    button: {
      primary: "bg-accentOrange-500 hover:bg-accentOrange-600 text-white",
      secondary: "bg-espresso-100 hover:bg-espresso-200 text-espresso-900",
      text: "text-accentOrange-600 hover:text-accentOrange-700",
    },
  },
  midnight: {
    id: "midnight",
    name: "Midnight",
    page: {
      background: "bg-gradient-to-br from-gray-900 via-gray-800 to-gray-900",
      text: "text-gray-100",
    },
    // ... similar structure for dark theme
  },
};
```

#### 1.4.3 CSS Utility Functions

```typescript
// frontend/lib/utils.ts
import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merge Tailwind CSS classes with proper precedence.
 * Later classes override earlier ones.
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// Usage example:
<div className={cn(
  "base-class",
  theme.card.background,
  isSelected && "border-2 border-blue-500",
  className
)}>
```

### 1.5 Performance Optimization

#### 1.5.1 React Optimization Techniques

**Memoization:**
```typescript
// Memoize expensive computations
const sortedTemplates = useMemo(() => {
  return templates.sort((a, b) => a.priority - b.priority);
}, [templates]);

// Memoize callbacks
const handleTemplateSelect = useCallback((id: string) => {
  const template = getTemplateById(id);
  setSelectedTemplate(template);
}, []);

// Memoize components
const MemoizedReasonCard = memo(ReasonCard, (prev, next) => {
  return prev.decision_id === next.decision_id;
});
```

**Code Splitting:**
```typescript
// Dynamic imports for heavy components
import dynamic from "next/dynamic";

const WorkflowVisualization = dynamic(
  () => import("@/components/streaming/workflow-visualization"),
  { ssr: false, loading: () => <div>Loading workflow...</div> }
);

const TemplateShowcase = dynamic(
  () => import("@/components/templates/template-showcase"),
  { ssr: true }
);
```

**Lazy Loading:**
```typescript
// Intersection Observer for lazy loading reason cards
const ReasonCardList = ({ reasonCards }: { reasonCards: ReasonCard[] }) => {
  const [visibleCards, setVisibleCards] = useState(reasonCards.slice(0, 10));

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          // Load more cards when scrolling near bottom
          setVisibleCards((prev) => [
            ...prev,
            ...reasonCards.slice(prev.length, prev.length + 10),
          ]);
        }
      });
    });

    const sentinel = document.getElementById("load-more-sentinel");
    if (sentinel) observer.observe(sentinel);

    return () => observer.disconnect();
  }, [reasonCards]);

  return (
    <>
      {visibleCards.map((card) => (
        <ReasonCard key={card.decision_id} {...card} />
      ))}
      <div id="load-more-sentinel" />
    </>
  );
};
```

#### 1.5.2 Next.js Optimization

**Image Optimization:**
```typescript
import Image from "next/image";

<Image
  src="/images/architecture-diagram.png"
  alt="Architecture Diagram"
  width={800}
  height={600}
  priority // Load immediately for above-fold images
  placeholder="blur" // Show blur placeholder while loading
/>
```

**Font Optimization:**
```typescript
// app/layout.tsx - Automatic font optimization
import { Inter } from "next/font/google";
import localFont from "next/font/local";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap", // Prevent invisible text while loading
});

const geistSans = localFont({
  src: "./fonts/GeistVF.woff",
  variable: "--font-geist-sans",
  weight: "100 900",
});
```

**Metadata for SEO:**
```typescript
// app/layout.tsx
export const metadata: Metadata = {
  title: "Agentic MLOps Platform",
  description: "AI-powered MLOps system design and generation",
  keywords: ["MLOps", "AI", "Machine Learning", "DevOps"],
  authors: [{ name: "Your Team" }],
  openGraph: {
    title: "Agentic MLOps Platform",
    description: "AI-powered MLOps system design",
    images: ["/og-image.png"],
  },
};
```

---

## 2. Backend Architecture

### 2.1 FastAPI Application Architecture

#### 2.1.1 Application Initialization

```python
# api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import os

# Initialize FastAPI app
app = FastAPI(
    title="Agentic MLOps API",
    description="Multi-agent system for MLOps design and generation",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure structured logging
if os.getenv("ENVIRONMENT") == "production":
    # JSON logging for CloudWatch
    logging.config.dictConfig(LOGGING_CONFIG)
else:
    # Simple logging for development
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))

logger = logging.getLogger(__name__)

# Configure CORS
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

if ENVIRONMENT == "production":
    allowed_origins = ["https://*.amazonaws.com"]
else:
    allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Content-Type", "Authorization"],
)

# Initialize graph (LangGraph workflow)
GRAPH_TYPE = os.getenv("GRAPH_TYPE", "thin").lower()

try:
    if GRAPH_TYPE == "full":
        _graph = build_full_graph()
    elif GRAPH_TYPE == "hitl_enhanced":
        _graph = build_hitl_enhanced_graph()
    else:
        _graph = build_thin_graph()
except Exception as e:
    logger.warning(f"Graph init failed; falling back to thin graph: {e}")
    _graph = build_thin_graph()

# Database setup
engine = create_database_engine()
SessionMaker = create_session_maker(engine)
```

#### 2.1.2 Integrated Worker Architecture

```python
# api/main.py
class IntegratedWorkerService:
    """
    Integrated worker that runs in the same process as the API server.

    Benefits:
    - Shared memory access (no serialization overhead)
    - Direct streaming service access (no HTTP bridge)
    - Simplified deployment (single container)
    - Job persistence with database-backed queue

    Trade-offs:
    - Single point of failure (API + Worker in one process)
    - Limited horizontal scaling (can only scale together)
    """

    def __init__(self, worker_id: str = None, poll_interval: int = 5):
        self.worker_id = worker_id or f"worker-{uuid.uuid4().hex[:8]}"
        self.poll_interval = poll_interval
        self.running = False
        self.task = None
        self.graph = _graph  # Share graph instance with API
        self.SessionMaker = SessionMaker  # Share session maker

    async def start_background_worker(self):
        """Start worker as background asyncio task."""
        self.running = True
        self.task = asyncio.create_task(self.run_worker_loop())
        logger.info(f"Background worker {self.worker_id} started")

    async def run_worker_loop(self):
        """
        Main worker loop with exponential backoff.

        Pattern:
        - Poll for jobs every 5 seconds
        - Process job if available
        - Backoff exponentially if no jobs (max 60s)
        - Reset backoff on successful job processing
        """
        consecutive_empty_polls = 0
        max_empty_polls = 12
        max_backoff = 60

        while self.running:
            try:
                job_processed = await self.process_next_job()

                if job_processed:
                    consecutive_empty_polls = 0
                    await asyncio.sleep(1)  # Short delay between jobs
                else:
                    consecutive_empty_polls += 1

                    if consecutive_empty_polls > max_empty_polls:
                        backoff_time = min(
                            self.poll_interval * (2 ** (consecutive_empty_polls - max_empty_polls)),
                            max_backoff
                        )
                        await asyncio.sleep(backoff_time)
                    else:
                        await asyncio.sleep(self.poll_interval)

            except Exception as e:
                logger.error(f"Error in worker loop: {e}")
                await asyncio.sleep(self.poll_interval)

    async def process_next_job(self) -> bool:
        """
        Claim and process next available job.

        Returns:
            True if job was processed, False if no jobs available
        """
        with self.get_job_service() as job_service:
            job = job_service.claim_job(self.worker_id, lease_duration=30)

            if not job:
                return False

            logger.info(f"Claimed job {job.id} of type {job.job_type}")

            try:
                await self.process_job(job)
                job_service.complete_job(job.id, self.worker_id)
                logger.info(f"Successfully completed job {job.id}")
                return True
            except Exception as e:
                logger.error(f"Job {job.id} failed: {e}")
                job_service.fail_job(job.id, self.worker_id, str(e))
                return True

    async def process_ml_workflow_job(self, job: Job):
        """
        Execute LangGraph workflow with multi-mode streaming.

        Streaming Modes:
        - "updates": Node state updates (reason cards, execution info)
        - "messages": LLM message streams (token-level reasoning)
        """
        thread_id = job.payload.get("thread_id")
        messages = job.payload.get("messages", [])
        decision_set_id = job.decision_set_id
        run_id = str(uuid.uuid4())

        # Convert messages to LangChain format
        lc_messages = [...]
        state = {"messages": lc_messages, "decision_set_id": decision_set_id}

        # Configure LangGraph with checkpointing
        config = {
            "configurable": {
                "thread_id": thread_id,
                "run_id": run_id,  # For LangSmith correlation
            }
        }

        # Get direct streaming service access
        streaming_service = get_streaming_service()

        # Execute with multi-mode streaming
        stream_modes = ["updates", "messages"]

        async for stream_mode, chunk in self.graph.astream(state, config, stream_mode=stream_modes):
            if stream_mode == "updates":
                await self._process_stream_chunk(chunk, decision_set_id, streaming_service)
            elif stream_mode == "messages":
                await self._process_message_chunk(chunk, decision_set_id, streaming_service)
```

### 2.2 LangGraph Agent Orchestration

#### 2.2.1 Graph Compilation and Execution

```python
# libs/graph.py
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver

def build_full_graph() -> Pregel:
    """
    Build complete 13-node workflow with dual HITL gates.

    Graph Structure:
    - Deterministic node execution order
    - Conditional edges for dynamic routing
    - Interrupt points for HITL
    - Checkpointing for persistence and resume
    """
    graph = StateGraph(MLOpsWorkflowState)

    # Add all nodes
    graph.add_node("intake_extract", intake_extract)
    graph.add_node("coverage_check", coverage_check)
    graph.add_node("adaptive_questions", adaptive_questions)
    graph.add_node("hitl_gate_input", hitl_gate_input)
    graph.add_node("planner", planner)
    graph.add_node("critic_tech", critic_tech)
    graph.add_node("critic_cost", critic_cost)
    graph.add_node("policy_eval", policy_eval)
    graph.add_node("hitl_gate_final", hitl_gate_final)
    graph.add_node("codegen", codegen)
    graph.add_node("validators", validators)
    graph.add_node("rationale_compile", rationale_compile)
    graph.add_node("diff_and_persist", diff_and_persist)

    # Define edges (simplified for clarity)
    graph.add_edge(START, "intake_extract")
    graph.add_edge("intake_extract", "coverage_check")

    # Conditional edge: Check coverage threshold
    graph.add_conditional_edge(
        "coverage_check",
        should_ask_questions,
        {
            "ask_questions": "adaptive_questions",
            "proceed": "planner"
        }
    )

    # HITL gate with loop-back capability
    graph.add_edge("adaptive_questions", "hitl_gate_input")
    graph.add_conditional_edge(
        "hitl_gate_input",
        should_loop_back,
        {
            "loop_back": "intake_extract",
            "continue": "planner"
        }
    )

    # Linear flow through planning and critics
    graph.add_edge("planner", "critic_tech")
    graph.add_edge("critic_tech", "critic_cost")
    graph.add_edge("critic_cost", "policy_eval")

    # Final HITL gate
    graph.add_edge("policy_eval", "hitl_gate_final")

    # Code generation and validation
    graph.add_edge("hitl_gate_final", "codegen")
    graph.add_edge("codegen", "validators")
    graph.add_edge("validators", "rationale_compile")
    graph.add_edge("rationale_compile", "diff_and_persist")
    graph.add_edge("diff_and_persist", END)

    # Compile with checkpointer for persistence
    checkpointer = create_appropriate_checkpointer()
    return graph.compile(checkpointer=checkpointer, interrupt_before=["hitl_gate_input", "hitl_gate_final"])
```

#### 2.2.2 Agent Node Implementation Pattern

```python
# libs/graph.py - Example agent node
def planner(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    """
    Planning agent node that composes architecture from capability patterns.

    Pattern:
    1. Get agent instance (lazy initialization)
    2. Execute agent with current state
    3. Extract reason card and state updates
    4. Update execution order
    5. Return merged state
    """
    start = time.time()
    thread_id = state.get("decision_set_id") or "unknown"
    logger.info("Node start: planner", extra={"thread_id": thread_id})

    # Get LLM-powered planner agent (lazy init)
    *_, planner_agent, *_ = _get_llm_agents()

    try:
        # Execute agent asynchronously (safe async run handles event loop)
        result = _safe_async_run(planner_agent.execute(state, TriggerType.INITIAL))

        if result.success:
            # Extract state updates and reason card
            state_updates = result.state_updates
            reason_cards = state.get("reason_cards", [])
            reason_cards.append(result.reason_card.model_dump())

            # Track execution order for debugging
            execution_order = state.get("execution_order", [])
            execution_order.append("planner")

            # Merge updates into state
            merged_state = {
                **state_updates,
                "reason_cards": reason_cards,
                "execution_order": execution_order,
            }

            logger.info(
                "Node success: planner",
                extra={
                    "thread_id": thread_id,
                    "duration_ms": int((time.time() - start) * 1000),
                    "plan_candidates": len(state_updates.get("candidates", [])),
                }
            )

            return merged_state

        # Handle agent failure
        logger.warning(
            "Node failure: planner",
            extra={"thread_id": thread_id, "error": result.error_message}
        )
        return {"plan": None, "error": result.error_message}

    except Exception as exc:
        logger.exception(
            "Node exception: planner",
            extra={"thread_id": thread_id, "error": str(exc)}
        )
        return {"plan": None, "error": f"Planner failed: {str(exc)}"}
```

#### 2.2.3 Checkpointing and State Persistence

```python
# libs/database.py
def create_appropriate_checkpointer():
    """
    Create checkpointer based on database configuration.

    Options:
    - PostgresSaver: Production (persistent, supports HITL)
    - SqliteSaver: Development (persistent, file-based)
    - MemorySaver: Fallback (non-persistent, testing only)
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///./agentic_mlops.db")

    if "postgresql" in database_url:
        from langgraph.checkpoint.postgres import PostgresSaver
        return PostgresSaver.from_conn_string(database_url)

    elif "sqlite" in database_url:
        from langgraph.checkpoint.sqlite import SqliteSaver
        return SqliteSaver.from_conn_string(database_url)

    else:
        # Fallback to memory saver (no persistence)
        from langgraph.checkpoint.memory import MemorySaver
        logger.warning("Using MemorySaver - no state persistence!")
        return MemorySaver()


# Async checkpointer for astream() operations
def create_async_checkpointer():
    """Create async-compatible checkpointer for streaming operations."""
    database_url = os.getenv("DATABASE_URL", "sqlite:///./agentic_mlops.db")

    if "postgresql" in database_url:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
        return AsyncPostgresSaver.from_conn_string(database_url)

    elif "sqlite" in database_url:
        from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
        return AsyncSqliteSaver.from_conn_string(database_url)

    else:
        from langgraph.checkpoint.memory import MemorySaver
        return MemorySaver()
```

### 2.3 Agent Framework Architecture

#### 2.3.1 Base Agent Pattern

```python
# libs/agent_framework.py
from abc import ABC, abstractmethod

class BaseMLOpsAgent(ABC):
    """
    Abstract base class for all MLOps agents.

    Provides common functionality:
    - System prompt management
    - Reason card creation
    - State management
    - Error handling
    """

    def __init__(self, agent_type: AgentType):
        self.agent_type = agent_type

    @abstractmethod
    async def execute(
        self,
        state: MLOpsWorkflowState,
        trigger: TriggerType
    ) -> AgentResult:
        """
        Execute agent logic and return result with reason card.

        Args:
            state: Current workflow state
            trigger: What triggered this execution

        Returns:
            AgentResult with success flag, state updates, and reason card
        """
        pass

    def create_reason_card(
        self,
        node_name: str,
        trigger: TriggerType,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        reasoning: str,
        confidence: float,
        **kwargs
    ) -> ReasonCard:
        """
        Helper to create structured reason cards for transparency.

        Standard fields:
        - agent: AgentType enum
        - node_name: LangGraph node identifier
        - trigger: What caused execution
        - inputs/outputs: Data in/out
        - reasoning: Decision rationale
        - confidence: 0.0-1.0 score

        Optional fields via **kwargs:
        - candidates: Alternative options considered
        - policy_results: Compliance check results
        - impact: Cost/latency/security impact
        - risks: Identified concerns
        """
        return ReasonCard(
            agent=self.agent_type,
            node_name=node_name,
            trigger=trigger,
            inputs=inputs,
            outputs=outputs,
            reasoning=reasoning,
            confidence=confidence,
            **kwargs
        )
```

#### 2.3.2 LLM Agent Implementation Pattern

```python
# libs/llm_planner_agent.py
from libs.llm_agent_base import BaseLLMAgent
from libs.agent_output_schemas import PlannerOutput

class LLMPlannerAgent(BaseLLMAgent):
    """
    LLM-powered planning agent using OpenAI structured output.

    Responsibilities:
    - Compose architecture from capability patterns
    - Evaluate multiple candidates
    - Select optimal design with justification
    - Emit reason card with decision transparency
    """

    def __init__(self):
        super().__init__(
            agent_type=AgentType.PLANNER,
            model="gpt-4",
            temperature=0.7
        )
        self.system_prompt = self._load_system_prompt("planner_instructions.md")

    async def execute(
        self,
        state: MLOpsWorkflowState,
        trigger: TriggerType
    ) -> AgentResult:
        """Execute planning logic with OpenAI structured output."""

        # Extract constraints from state
        constraints = state.get("constraints", {})

        # Build user prompt with constraints
        user_prompt = f"""
        Design an MLOps system with the following constraints:

        {json.dumps(constraints, indent=2)}

        Generate multiple architecture candidates and select the best one.
        """

        try:
            # Call OpenAI with structured output (Pydantic schema)
            completion = self.client.beta.chat.completions.parse(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format=PlannerOutput,  # Pydantic model for validation
                temperature=self.temperature
            )

            # Extract structured output
            planner_output = completion.choices[0].message.parsed

            # Create reason card for transparency
            reason_card = self.create_reason_card(
                node_name="planner",
                trigger=trigger,
                inputs={"constraints": constraints},
                outputs={
                    "selected_plan": planner_output.selected_plan.dict(),
                    "candidates": [c.dict() for c in planner_output.candidates]
                },
                reasoning=planner_output.selection_rationale,
                confidence=planner_output.confidence_score,
                candidates=[self._to_candidate_option(c) for c in planner_output.candidates],
                choice=DecisionChoice(
                    id=planner_output.selected_plan.pattern_id,
                    justification=planner_output.selection_rationale,
                    confidence=planner_output.confidence_score
                )
            )

            # Return successful result
            return AgentResult(
                success=True,
                state_updates={
                    "plan": planner_output.selected_plan.dict(),
                    "candidates": [c.dict() for c in planner_output.candidates],
                    "planning_analysis": planner_output.dict()
                },
                reason_card=reason_card,
                error_message=None
            )

        except Exception as e:
            # Handle errors gracefully
            logger.error(f"Planner agent failed: {e}")
            return AgentResult(
                success=False,
                state_updates={},
                reason_card=self._create_error_reason_card(str(e)),
                error_message=str(e)
            )
```

### 2.4 Service Layer Architecture

#### 2.4.1 Job Service

```python
# libs/job_service.py
from sqlalchemy.orm import Session
from sqlalchemy import select
from datetime import datetime, timedelta, timezone

class JobService:
    """
    Service for managing asynchronous job queue.

    Features:
    - FOR UPDATE SKIP LOCKED for distributed processing
    - Lease-based job claiming (prevents race conditions)
    - Retry logic with exponential backoff
    - Priority-based job ordering
    """

    def __init__(self, session: Session):
        self.session = session

    def create_job(
        self,
        decision_set_id: str,
        job_type: str,
        payload: Dict[str, Any],
        priority: int = 0
    ) -> Job:
        """
        Create and enqueue a new job.

        Args:
            decision_set_id: Associated decision set
            job_type: Type of job (e.g., "ml_workflow")
            payload: Job-specific data (JSON-serializable)
            priority: Higher values processed first (default: 0)

        Returns:
            Created Job instance
        """
        job = Job(
            id=str(uuid.uuid4()),
            decision_set_id=decision_set_id,
            job_type=job_type,
            payload=payload,
            priority=priority,
            status=JobStatus.QUEUED,
            created_at=datetime.now(timezone.utc)
        )
        self.session.add(job)
        self.session.commit()
        self.session.refresh(job)
        return job

    def claim_job(
        self,
        worker_id: str,
        lease_duration: int = 5
    ) -> Optional[Job]:
        """
        Atomically claim next available job using FOR UPDATE SKIP LOCKED.

        This pattern ensures:
        - No two workers claim the same job
        - No blocking/waiting for locked rows
        - Exactly-once processing semantics

        Args:
            worker_id: Unique identifier for this worker
            lease_duration: Minutes to hold lease (default: 5)

        Returns:
            Claimed Job or None if no jobs available
        """
        # Single SQL query with row-level locking
        job = self.session.execute(
            select(Job)
            .where(Job.status == JobStatus.QUEUED)
            .where(Job.created_at <= datetime.now(timezone.utc))
            .order_by(Job.priority.desc(), Job.created_at.asc())
            .with_for_update(skip_locked=True)  # Key: skip locked rows
            .limit(1)
        ).scalar_one_or_none()

        if not job:
            return None

        # Update job status and lease
        job.status = JobStatus.RUNNING
        job.worker_id = worker_id
        job.started_at = datetime.now(timezone.utc)
        job.lease_expires_at = datetime.now(timezone.utc) + timedelta(minutes=lease_duration)

        self.session.commit()
        self.session.refresh(job)
        return job

    def complete_job(self, job_id: str, worker_id: str) -> bool:
        """Mark job as completed."""
        job = self.session.get(Job, job_id)

        if not job or job.worker_id != worker_id:
            return False

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.now(timezone.utc)
        self.session.commit()
        return True

    def fail_job(
        self,
        job_id: str,
        worker_id: str,
        error_message: str
    ) -> bool:
        """
        Mark job as failed with retry logic.

        Retry Policy:
        - Max 3 retries by default
        - Exponential backoff: 1s, 2s, 4s
        - After max retries, mark as permanently failed
        """
        job = self.session.get(Job, job_id)

        if not job or job.worker_id != worker_id:
            return False

        job.retry_count += 1
        job.error_message = error_message

        if job.retry_count < job.max_retries:
            # Requeue with exponential backoff
            backoff_seconds = 2 ** job.retry_count
            job.status = JobStatus.QUEUED
            job.next_run_at = datetime.now(timezone.utc) + timedelta(seconds=backoff_seconds)
            job.worker_id = None
            job.lease_expires_at = None
            logger.info(f"Job {job_id} failed, retrying in {backoff_seconds}s")
        else:
            # Permanently failed
            job.status = JobStatus.FAILED
            job.completed_at = datetime.now(timezone.utc)
            logger.error(f"Job {job_id} permanently failed after {job.max_retries} retries")

        self.session.commit()
        return True
```

#### 2.4.2 Streaming Service

```python
# libs/streaming_service.py
from collections import defaultdict
from typing import AsyncGenerator, Dict, List
import asyncio

class StreamingService:
    """
    Service for real-time SSE event broadcasting.

    Architecture:
    - In-memory event storage (simple dict, Redis for prod)
    - Per-decision-set client queues (asyncio.Queue)
    - Automatic cleanup (1000 event limit per decision set)
    - Heartbeat mechanism for connection health
    """

    def __init__(self):
        # Event storage: decision_set_id -> list of events
        self._events: Dict[str, List[StreamEvent]] = defaultdict(list)

        # Active connections: decision_set_id -> list of client queues
        self._clients: Dict[str, List[asyncio.Queue]] = defaultdict(list)

        # Event deduplication
        self._seen_reason_cards: Dict[str, set] = defaultdict(set)

    async def emit_event(self, event: StreamEvent):
        """
        Broadcast event to all subscribed clients.

        Args:
            event: StreamEvent to broadcast
        """
        decision_set_id = event.decision_set_id

        # Store in history
        self._events[decision_set_id].append(event)

        # Cleanup old events (memory management)
        if len(self._events[decision_set_id]) > 1000:
            self._events[decision_set_id] = self._events[decision_set_id][-500:]

        # Broadcast to all connected clients
        for queue in self._clients[decision_set_id]:
            try:
                await queue.put(event)
            except Exception as e:
                logger.error(f"Failed to send event to client: {e}")

    async def emit_reason_card(self, reason_card: ReasonCard):
        """
        Emit reason card with deduplication.

        Deduplication key: agent + node + confidence + inputs hash
        """
        decision_set_id = reason_card.decision_set_id

        # Create deduplication key
        dedup_key = (
            reason_card.agent,
            reason_card.node,
            reason_card.confidence,
            hash(str(reason_card.inputs))
        )

        # Skip if already emitted
        if dedup_key in self._seen_reason_cards[decision_set_id]:
            logger.debug(f"Skipping duplicate reason card: {reason_card.agent}")
            return

        # Mark as seen
        self._seen_reason_cards[decision_set_id].add(dedup_key)

        # Emit event
        event = StreamEvent(
            event_type=StreamEventType.REASON_CARD,
            decision_set_id=decision_set_id,
            data=reason_card.dict(),
            message=f"Agent {reason_card.agent} completed"
        )
        await self.emit_event(event)

    async def subscribe(
        self,
        decision_set_id: str
    ) -> AsyncGenerator[StreamEvent, None]:
        """
        Subscribe to event stream for a decision set.

        Yields:
            StreamEvent objects as they occur

        Lifecycle:
        1. Send historical events (event replay)
        2. Register client queue
        3. Stream new events as they arrive
        4. Send heartbeats every 10s
        5. Cleanup on disconnect
        """
        # Create queue for this client
        queue = asyncio.Queue()
        self._clients[decision_set_id].append(queue)

        try:
            # Send historical events first (event replay)
            for event in self._events[decision_set_id]:
                yield event

            # Stream new events
            heartbeat_interval = 10  # seconds
            last_heartbeat = asyncio.get_event_loop().time()

            while True:
                try:
                    # Wait for next event with timeout for heartbeat
                    event = await asyncio.wait_for(
                        queue.get(),
                        timeout=heartbeat_interval
                    )
                    yield event
                    last_heartbeat = asyncio.get_event_loop().time()

                except asyncio.TimeoutError:
                    # Send heartbeat to keep connection alive
                    now = asyncio.get_event_loop().time()
                    if now - last_heartbeat >= heartbeat_interval:
                        heartbeat = StreamEvent(
                            event_type=StreamEventType.HEARTBEAT,
                            decision_set_id=decision_set_id,
                            data={}
                        )
                        yield heartbeat
                        last_heartbeat = now

        finally:
            # Cleanup: Remove client queue on disconnect
            if queue in self._clients[decision_set_id]:
                self._clients[decision_set_id].remove(queue)

            logger.info(f"Client disconnected from decision_set {decision_set_id}")


# Singleton instance
_streaming_service = None

def get_streaming_service() -> StreamingService:
    """Get singleton streaming service instance."""
    global _streaming_service
    if _streaming_service is None:
        _streaming_service = StreamingService()
    return _streaming_service
```

---

## 3. Project Structure

### 3.1 Repository Layout

```
agentic-mlops/
├── README.md                    # Project overview and quick start
├── CLAUDE.md                    # Claude Code instructions
├── AGENTS.md                    # Agent system documentation
├── .env.example                 # Environment variable template
├── .gitignore                   # Git ignore patterns
├── pyproject.toml               # Python dependencies and tool config
├── .pre-commit-config.yaml      # Pre-commit hooks configuration
│
├── api/                         # FastAPI backend
│   ├── main.py                  # Application entry point with integrated worker
│   ├── Dockerfile               # API + Worker container image
│   └── __init__.py
│
├── libs/                        # Shared Python libraries
│   ├── agent_framework.py       # Base agent classes and state models
│   ├── agent_output_schemas.py  # Pydantic schemas for agent outputs
│   ├── constraint_schema.py     # Constraint extraction schemas
│   │
│   ├── intake_extract_agent.py  # Constraint extraction agent
│   ├── coverage_check_agent.py  # Coverage analysis agent
│   ├── adaptive_questions_agent.py  # Follow-up question agent
│   ├── llm_planner_agent.py     # Architecture planning agent
│   ├── llm_tech_critic_agent.py # Technical feasibility agent
│   ├── llm_cost_critic_agent.py # Cost estimation agent
│   ├── llm_policy_engine_agent.py  # Policy compliance agent
│   ├── llm_agent_base.py        # Base class for LLM agents
│   ├── llm_client.py            # OpenAI client wrapper
│   │
│   ├── graph.py                 # LangGraph workflow definitions
│   ├── hitl_graph.py            # HITL-specific graphs
│   │
│   ├── database.py              # Database connection and checkpointers
│   ├── models.py                # SQLAlchemy ORM models
│   ├── job_service.py           # Async job queue service
│   ├── streaming_service.py     # SSE streaming service
│   ├── streaming_models.py      # Streaming event models
│   ├── codegen_service.py       # Code generation service
│   ├── validation_service.py    # Code validation service
│   │
│   ├── mock_agents.py           # Mock agents for testing
│   └── __init__.py
│
├── frontend/                    # Next.js React application
│   ├── app/                     # Next.js 14 App Router
│   │   ├── layout.tsx           # Root layout
│   │   ├── page.tsx             # Landing page
│   │   ├── globals.css          # Global styles
│   │   ├── fonts/               # Custom fonts
│   │   └── demo/                # Demo pages
│   │       └── hitl/
│   │           └── page.tsx
│   │
│   ├── components/              # React components
│   │   ├── chat/                # Chat interface
│   │   │   ├── enhanced-chat-interface.tsx
│   │   │   └── chat-interface.tsx
│   │   ├── streaming/           # Real-time components
│   │   │   ├── workflow-visualization.tsx
│   │   │   ├── reason-card.tsx
│   │   │   ├── workflow-status-panel.tsx
│   │   │   ├── workflow-progress.tsx
│   │   │   └── workflow-step.tsx
│   │   ├── templates/           # Template gallery
│   │   │   ├── template-showcase.tsx
│   │   │   └── template-card.tsx
│   │   ├── landing/             # Landing page
│   │   │   └── hero-section.tsx
│   │   ├── hitl/                # HITL components
│   │   │   └── question-form.tsx
│   │   └── ui/                  # UI primitives (Radix UI)
│   │       ├── button.tsx
│   │       ├── card.tsx
│   │       ├── badge.tsx
│   │       ├── input.tsx
│   │       └── tabs.tsx
│   │
│   ├── hooks/                   # Custom React hooks
│   │   └── useStreamingEvents.ts
│   │
│   ├── data/                    # Static data
│   │   ├── mlops-templates.ts
│   │   └── landing-themes.ts
│   │
│   ├── lib/                     # Utility functions
│   │   └── utils.ts
│   │
│   ├── public/                  # Static assets
│   │   └── images/
│   │
│   ├── e2e/                     # Playwright E2E tests
│   │   └── chat-flow.spec.ts
│   │
│   ├── package.json             # Node dependencies
│   ├── tsconfig.json            # TypeScript configuration
│   ├── tailwind.config.ts       # Tailwind CSS configuration
│   ├── next.config.js           # Next.js configuration
│   ├── postcss.config.js        # PostCSS configuration
│   ├── jest.config.js           # Jest test configuration
│   ├── playwright.config.ts     # Playwright E2E configuration
│   ├── Dockerfile               # Frontend container image
│   └── .eslintrc.json           # ESLint configuration
│
├── tests/                       # Python tests
│   ├── test_models.py           # Database model tests
│   ├── test_constraint_schema.py # Schema validation tests
│   ├── test_agent_framework.py  # Agent framework tests
│   ├── test_llm_integration.py  # LLM agent integration tests
│   ├── test_llm_workflow_integration.py  # Full workflow tests
│   ├── test_api.py              # API endpoint tests
│   ├── test_async_api.py        # Async endpoint tests
│   ├── test_job_system.py       # Job queue tests
│   ├── test_full_graph.py       # Full graph execution tests
│   ├── test_hitl_e2e.py         # HITL workflow tests
│   ├── test_hitl_gate.py        # HITL gate tests
│   ├── test_streaming_functionality.py  # SSE streaming tests
│   ├── test_checkpointing.py    # LangGraph checkpoint tests
│   ├── test_codegen_service.py  # Codegen tests
│   ├── test_validation_service.py  # Validation tests
│   └── conftest.py              # Pytest fixtures
│
├── infra/terraform/             # Infrastructure as Code
│   ├── main.tf                  # Main Terraform configuration
│   ├── apprunner.tf             # App Runner services
│   ├── rds.tf                   # RDS PostgreSQL + Proxy
│   ├── s3.tf                    # S3 artifact storage
│   ├── ecr.tf                   # ECR container registries
│   ├── iam.tf                   # IAM roles and policies
│   ├── vpc.tf                   # VPC connector
│   ├── variables.tf             # Input variables
│   ├── outputs.tf               # Output values
│   └── README.md                # Terraform documentation
│
├── scripts/                     # Automation scripts
│   ├── 1-deploy-infrastructure.sh  # Terraform apply
│   ├── 2-build-and-push.sh      # Docker build + ECR push
│   ├── 3-deploy-app-runner.sh   # App Runner deployment
│   ├── test-e2e.sh              # Basic E2E testing
│   └── test-e2e-playwright.sh   # Playwright E2E testing
│
├── docs/                        # Documentation
│   ├── IMPLEMENTATION_CHANGELOG.md
│   ├── PRODUCT_FEATURES.md
│   ├── TECHNICAL_ARCHITECTURE.md
│   ├── LANGSMITH_INTEGRATION_SUMMARY.md
│   ├── deployment_guide.md
│   ├── streaming-architecture-guide.md
│   ├── sse-streaming-debug-guide.md
│   ├── sqlalchemy-alembic-guide.md
│   └── issue-*.md               # Implementation guides
│
├── context/                     # Project context
│   ├── prd.md                   # Product requirements
│   ├── implementation_plan.md   # Implementation roadmap
│   ├── implementation_details.md # Technical details
│   └── prompts.md               # Agent system prompts
│
└── alembic/                     # Database migrations
    ├── versions/                # Migration scripts
    ├── env.py                   # Alembic environment
    └── alembic.ini              # Alembic configuration
```

### 3.2 Dependency Management

#### 3.2.1 Python Dependencies

```toml
# pyproject.toml
[project]
name = "agentic-mlops"
version = "0.1.0"
requires-python = ">=3.11"

dependencies = [
    # API Framework
    "fastapi",
    "uvicorn",
    "pydantic>=2.0",

    # Agent Orchestration
    "langgraph",
    "langchain-core",
    "langgraph-checkpoint-postgres",
    "langgraph-checkpoint-sqlite",
    "langgraph-checkpoint",

    # Database
    "sqlalchemy>=2.0",
    "alembic",
    "psycopg2-binary",  # PostgreSQL adapter for SQLAlchemy
    "psycopg[binary]",  # PostgreSQL adapter for LangGraph
    "aiosqlite>=0.21.0",  # Async SQLite

    # LLM Providers
    "openai>=1.107.1",
    "claude-code-sdk",

    # Cloud Services
    "boto3>=1.26.0",  # AWS SDK

    # Streaming
    "sse-starlette>=2.0.0",

    # Utilities
    "httpx>=0.28.1",
    "backoff>=2.2.1",
    "langsmith>=0.4.25",
    "python-json-logger>=3.3.0",
    "python-dotenv",
]

[project.optional-dependencies]
dev = [
    "pre-commit",
    "pytest",
    "pytest-asyncio",
    "pytest-cov",
    "ruff",
    "mypy",
    "httpx",  # For API testing
]

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "I", "N", "W"]
ignore = ["E501"]  # Line length handled by formatter

[tool.pytest.ini_options]
asyncio_mode = "auto"
markers = [
    "integration: marks tests as integration tests",
    "slow: marks tests as slow-running (deselect with '-m \"not slow\"')",
]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
```

#### 3.2.2 Frontend Dependencies

```json
// frontend/package.json
{
  "name": "frontend",
  "version": "0.1.0",
  "private": true,
  "scripts": {
    "dev": "next dev",
    "build": "next build",
    "start": "next start",
    "lint": "next lint",
    "test": "jest",
    "test:watch": "jest --watch",
    "test:coverage": "jest --coverage",
    "test:e2e": "playwright test",
    "test:e2e:ui": "playwright test --ui",
    "test:e2e:headed": "playwright test --headed"
  },
  "dependencies": {
    "next": "14.1.0",
    "react": "18.2.0",
    "react-dom": "18.2.0",
    "@radix-ui/react-icons": "^1.3.2",
    "@radix-ui/react-tabs": "^1.1.13",
    "class-variance-authority": "^0.7.1",
    "clsx": "^2.1.1",
    "lucide-react": "^0.542.0",
    "tailwind-merge": "^3.3.1"
  },
  "devDependencies": {
    "@playwright/test": "^1.55.0",
    "@testing-library/jest-dom": "^6.8.0",
    "@testing-library/react": "^16.3.0",
    "@testing-library/user-event": "^14.6.1",
    "@types/jest": "^30.0.0",
    "@types/node": "20.11.30",
    "@types/react": "18.2.24",
    "autoprefixer": "10.4.16",
    "eslint": "^8.57.0",
    "eslint-config-next": "^15.5.3",
    "jest": "^30.1.3",
    "jest-environment-jsdom": "^30.1.2",
    "postcss": "8.4.32",
    "tailwindcss": "3.4.1",
    "typescript": "5.3.3"
  }
}
```

---

## 4. Development Workflow

### 4.1 Local Development Setup

#### 4.1.1 Initial Setup

```bash
# 1. Clone repository
git clone <repository-url>
cd agentic-mlops

# 2. Install Python dependencies with uv
uv sync --extra dev

# 3. Install frontend dependencies
npm install --prefix frontend

# 4. Configure environment variables
cp .env.example .env

# Edit .env with your API keys:
# - OPENAI_API_KEY
# - ANTHROPIC_API_KEY

# 5. Initialize database (SQLite auto-created on first run)
# No manual database setup needed for local development
```

#### 4.1.2 Running Development Servers

```bash
# Terminal 1: Start API + Integrated Worker
PYTHONPATH=. uv run uvicorn api.main:app --reload --port 8000

# Terminal 2: Start Frontend
cd frontend && npm run dev

# Access:
# - API: http://localhost:8000
# - API Docs: http://localhost:8000/docs
# - Frontend: http://localhost:3000
```

### 4.2 Code Quality Tools

#### 4.2.1 Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.1.9
    hooks:
      # Run ruff linter
      - id: ruff
        args: [--fix]
      # Run ruff formatter
      - id: ruff-format

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-json
      - id: check-added-large-files

# Install hooks:
# pre-commit install

# Run manually:
# pre-commit run --all-files
```

#### 4.2.2 Testing Strategy

**Python Tests:**
```bash
# Run all tests
uv run pytest -v

# Run with coverage
uv run pytest --cov=libs --cov=api --cov-report=html

# Run fast tests only (skip slow integration tests)
uv run pytest -v -m "not slow"

# Run specific test file
uv run pytest tests/test_api.py -v

# Run specific test
uv run pytest tests/test_api.py::test_chat_endpoint -v
```

**Frontend Tests:**
```bash
# Unit tests with Jest
cd frontend && npm test

# Watch mode
npm run test:watch

# Coverage report
npm run test:coverage

# E2E tests with Playwright
npm run test:e2e

# E2E with UI
npm run test:e2e:ui

# E2E in headed mode (see browser)
npm run test:e2e:headed
```

### 4.3 Git Workflow

#### 4.3.1 Branch Strategy

```bash
# Main branches
main              # Production-ready code
develop           # Development branch (if using GitFlow)

# Feature branches
git checkout -b feature/agent-improvements
git checkout -b fix/streaming-bug
git checkout -b docs/api-specification

# Commit with conventional commits
git commit -m "feat(agents): add cost optimization logic"
git commit -m "fix(api): resolve SSE connection timeout"
git commit -m "docs(readme): update installation steps"
```

#### 4.3.2 Conventional Commits

```
feat: New feature
fix: Bug fix
docs: Documentation changes
style: Code style changes (formatting, etc.)
refactor: Code refactoring
test: Adding or updating tests
chore: Build process or tooling changes
perf: Performance improvements
ci: CI/CD changes
```

### 4.4 Debugging

#### 4.4.1 Backend Debugging

**Enable Debug Logging:**
```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in .env file
LOG_LEVEL=DEBUG

# Run server
PYTHONPATH=. uv run uvicorn api.main:app --reload --port 8000
```

**LangSmith Tracing:**
```bash
# Enable LangSmith in .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_PROJECT=agentic-mlops
LANGCHAIN_API_KEY=<your-key>

# View traces at https://smith.langchain.com
```

**Database Inspection:**
```bash
# SQLite (development)
sqlite3 agentic_mlops.db

# PostgreSQL (production)
psql postgresql://user:pass@localhost:5432/mlops
```

#### 4.4.2 Frontend Debugging

**React DevTools:**
```bash
# Install Chrome extension: React Developer Tools
# Inspect component tree, props, and state
```

**Network Debugging:**
```bash
# Chrome DevTools -> Network tab
# Filter: event-stream (for SSE connections)
# Monitor API requests and responses
```

**SSE Debugging:**
```bash
# Test SSE connection with curl
curl -N http://localhost:8000/api/streams/decision-set-123

# Monitor events in browser console
const eventSource = new EventSource('http://localhost:8000/api/streams/123');
eventSource.addEventListener('reason-card', (e) => console.log(e.data));
```

### 4.5 Deployment Workflow

#### 4.5.1 Development Deployment

```bash
# 1. Deploy infrastructure
./scripts/1-deploy-infrastructure.sh

# 2. Build and push containers
./scripts/2-build-and-push.sh

# 3. Deploy App Runner services
./scripts/3-deploy-app-runner.sh

# 4. Run E2E tests
./scripts/test-e2e-playwright.sh
```

#### 4.5.2 Production Deployment

```bash
# 1. Create production branch
git checkout -b release/v1.0.0

# 2. Update version numbers
# - pyproject.toml
# - frontend/package.json

# 3. Run full test suite
uv run pytest -v
cd frontend && npm test && npm run test:e2e

# 4. Deploy to production
ENVIRONMENT=production ./scripts/1-deploy-infrastructure.sh
ENVIRONMENT=production ./scripts/2-build-and-push.sh
ENVIRONMENT=production ./scripts/3-deploy-app-runner.sh

# 5. Monitor deployment
# - Check CloudWatch logs
# - Monitor LangSmith traces
# - Run smoke tests
```

---

**Document Status**: Complete
**Review Required**: Architecture Review Board
**Next Steps**: Create Part 4 - Operations & Production
