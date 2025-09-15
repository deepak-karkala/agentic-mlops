# Streaming Architecture Guide: Real-time Agent Reasoning & Workflow Progress

## Overview

This document provides a comprehensive guide to the **Streaming "Reason Cards" & SSE Resilience** implementation in the Agentic MLOps platform. This feature enables real-time visibility into AI agent decision-making processes through a Claude-style unified interface with inline workflow display, replacing the previous separate Progress/Reasoning tabs.

The implementation uses Server-Sent Events (SSE) to stream agent reasoning, workflow progress, and system events in real-time, providing users with transparent insight into AI decision-making processes.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [End-to-End Process Flow](#end-to-end-process-flow)
3. [Backend Implementation](#backend-implementation)
4. [Frontend Implementation](#frontend-implementation)
5. [Data Models & Types](#data-models--types)
6. [Testing & Quality Assurance](#testing--quality-assurance)
7. [Deployment & Configuration](#deployment--configuration)

## Architecture Overview

```mermaid
graph TB
    User[👤 User] --> ChatUI[🖥️ Enhanced Chat Interface]
    ChatUI --> AsyncAPI[🔗 /api/chat/async]
    AsyncAPI --> JobQueue[📋 Job Queue - PostgreSQL]
    JobQueue --> Worker[⚙️ Integrated Worker]
    Worker --> LangGraph[🔄 LangGraph Workflow]

    subgraph "Real-time Streaming Pipeline"
        LangGraph --> AgentNodes[🤖 Agent Nodes]
        AgentNodes --> StreamService[📡 Streaming Service]
        StreamService --> SSEEndpoint[🌊 /api/streams/{decision_id}]
        SSEEndpoint --> SSEHook[🔄 useStreamingEvents Hook]
        SSEHook --> WorkflowContainer[🎨 WorkflowContainer]
    end

    subgraph "Claude-style Unified Interface"
        WorkflowContainer --> WorkflowSteps[📋 Workflow Steps]
        WorkflowSteps --> ReasonCards[🧠 Collapsible Reason Cards]
        ReasonCards --> AgentReasoning[💭 Agent Reasoning Display]
    end

    subgraph "State Management"
        JobQueue --> PostgreSQL[(🗄️ PostgreSQL)]
        StreamService --> InMemoryEvents[💾 In-Memory Events]
        LangGraph --> Checkpoints[📝 LangGraph Checkpoints]
    end
```

## End-to-End Process Flow

### Phase 1: User Input & Job Creation

1. **User Action**: User types MLOps requirements in the enhanced chat interface
   ```
   User Input: "Design a simple ML training pipeline with model versioning"
   ```

2. **Frontend Request**: Enhanced chat interface (`enhanced-chat-interface.tsx`) calls:
   ```typescript
   POST /api/chat/async
   {
     "messages": [{"role": "user", "content": "Design a simple ML training pipeline..."}]
   }
   ```

3. **API Job Creation**: Backend (`api/main.py`) immediately:
   - Creates a new job in PostgreSQL job queue
   - Generates unique `decision_set_id` for the workflow session
   - Returns job metadata without waiting for processing
   ```json
   {
     "decision_set_id": "f1262365-7421-4b84-ba42-86e05e1a729c",
     "job_id": "e3520753-94d4-4b79-9dcf-edce0cf4773a",
     "thread_id": "8c15cebc-ee52-408f-82f3-1c8c0b03f470",
     "status": "queued"
   }
   ```

4. **Immediate Frontend Response**: Chat interface immediately shows:
   - User message in chat
   - System message with job details
   - "Waiting for workflow to start..." status

### Phase 2: SSE Connection Establishment

5. **Automatic SSE Connection**: Frontend automatically establishes SSE connection:
   ```typescript
   // useStreamingEvents hook connects to:
   GET /api/streams/{decision_set_id}
   ```

6. **Connection Initialization**: SSE endpoint (`api/main.py`):
   - Establishes EventSource connection
   - Registers client with streaming service
   - Begins sending heartbeat events every 30 seconds
   - Replays any historical events for this decision set

### Phase 3: Background Job Processing

7. **Worker Job Claiming**: Integrated worker (`api/main.py`) claims the job:
   ```python
   # Database-backed job queue with FOR UPDATE SKIP LOCKED
   job = job_service.claim_job()  # Returns the queued job
   ```

8. **LangGraph Workflow Initialization**: Worker starts LangGraph workflow:
   ```python
   # Start LangGraph multi-mode streaming for thread, decision_set
   graph.invoke(
       {"messages": messages},
       config={"thread_id": thread_id, "decision_set_id": decision_set_id}
   )
   ```

### Phase 4: Agent Node Execution with Real-time Streaming

9. **Node Start Event**: Each agent node begins with:
   ```python
   # In libs/graph.py, each node emits start event
   streaming_service.emit_node_start(
       decision_set_id=decision_set_id,
       node="intake_extract",
       description="Extracting and structuring project requirements"
   )
   ```

10. **SSE Event Transmission**: Event immediately streams to frontend:
    ```
    event: node-start
    data: {
      "type": "node-start",
      "decision_set_id": "f1262365-7421-4b84-ba42-86e05e1a729c",
      "timestamp": "2025-09-15T15:15:37Z",
      "data": {"node": "intake_extract", "description": "..."}
    }
    ```

11. **Agent LLM Processing**: Agent executes with Claude/OpenAI:
    ```python
    # Agent processes user requirements
    result = llm_agent.execute(state, context)
    # Returns structured output with reasoning
    ```

12. **Reason Card Creation**: Agent creates detailed reason card:
    ```python
    reason_card = ReasonCard(
        agent="intake.extract",
        node="intake_extract_agent",
        decision_set_id=decision_set_id,
        reasoning="The request implies a need for simple ML training...",
        decision="Extracted constraints with 0.7 confidence",
        confidence=0.7,
        category="requirement-extraction",
        priority="medium",
        alternatives_considered=["batch_training", "model_experimentation"]
    )
    ```

13. **Reason Card Streaming**: Reason card immediately streams to frontend:
    ```
    event: reason-card
    data: {
      "type": "reason-card",
      "decision_set_id": "f1262365-7421-4b84-ba42-86e05e1a729c",
      "data": {
        "agent": "intake.extract",
        "reasoning": "The request implies a need for simple ML training...",
        "decision": "Extracted constraints with 0.7 confidence",
        "confidence": 0.7,
        "category": "requirement-extraction",
        "priority": "medium"
      }
    }
    ```

14. **Node Completion**: Node finishes and emits completion event:
    ```python
    streaming_service.emit_node_complete(
        decision_set_id=decision_set_id,
        node="intake_extract",
        outputs=result.outputs
    )
    ```

### Phase 5: Frontend Real-time UI Updates

15. **SSE Event Reception**: `useStreamingEvents` hook processes events:
    ```typescript
    // Hook receives and processes events in real-time
    eventSource.addEventListener('node-start', (event) => {
      const data = JSON.parse(event.data);
      processStreamEvent(data); // Updates React state
    });
    ```

16. **React State Updates**: Hook updates component state:
    ```typescript
    // Updates trigger re-renders of workflow components
    setState(prevState => ({
      ...prevState,
      events: [...prevState.events, event],
      reasonCards: [...prevState.reasonCards, reasonCard],
      workflowProgress: updateProgress(event)
    }));
    ```

17. **UI Component Rendering**: `WorkflowContainer` displays:
    - **Workflow Progress Header**: "MLOps Workflow Progress" with 20% completion
    - **Workflow Step**: "Extracting and structuring project requirements"
    - **Collapsible Reason Card**: Expandable section with:
      - **Reasoning Section**: Detailed agent explanation
      - **Decision Section**: Key decision made
      - **Confidence Badge**: 70% confidence indicator
      - **Priority Badge**: Medium priority
      - **Agent Info**: "Agent: intake.extract, Node: intake_extract_agent"

### Phase 6: Workflow Completion

18. **Final Workflow Events**: When all nodes complete:
    ```python
    streaming_service.emit_workflow_complete(
        decision_set_id=decision_set_id,
        final_outputs=workflow_result
    )
    ```

19. **Job Status Polling**: Frontend polls job status every 3 seconds:
    ```typescript
    GET /api/jobs/{job_id}/status
    // Updates job status badge from "processing" to "completed"
    ```

20. **Completion Message**: System adds completion message:
    ```
    "✅ MLOps architecture design completed! The workflow has finished successfully."
    ```

21. **Connection Cleanup**: SSE connection closes gracefully:
    - Stops heartbeat events
    - Cleans up streaming service subscriptions
    - Maintains event history for replay

### Key Implementation Details

**Event Deduplication**: Backend prevents duplicate reason cards:
```python
# In libs/graph.py - comprehensive deduplication
seen_cards = set()
for reason_card in reason_cards:
    card_key = create_dedup_key(reason_card)
    if card_key not in seen_cards:
        emit_reason_card(reason_card)
        seen_cards.add(card_key)
```

**Single Workflow Container**: Frontend shows one container per decision set:
```typescript
// In enhanced-chat-interface.tsx
const isFirstMessageWithDecisionSetId =
  message.role === "assistant" && message.decisionSetId &&
  !chatState.messages.slice(0, index).some(m =>
    m.decisionSetId === message.decisionSetId
  );
```

**Automatic Reconnection**: Hook handles connection resilience:
```typescript
// Exponential backoff reconnection
eventSource.onerror = () => {
  if (reconnectCount < maxAttempts) {
    setTimeout(() => connect(), reconnectDelay * Math.pow(2, reconnectCount));
  }
};
```

## Backend Implementation

### Core Components

#### 1. Streaming Models (`libs/streaming_models.py`)

```python
class StreamEventType(str, Enum):
    REASON_CARD = "reason-card"
    NODE_START = "node-start"
    NODE_COMPLETE = "node-complete"
    WORKFLOW_START = "workflow-start"
    WORKFLOW_COMPLETE = "workflow-complete"
    ERROR = "error"
    HEARTBEAT = "heartbeat"
    WORKFLOW_PAUSED = "workflow-paused"

class ReasonCard(BaseModel):
    agent: str
    node: str
    decision_set_id: str
    reasoning: str
    decision: str
    confidence: Optional[float]
    inputs: Optional[Dict[str, Any]]
    outputs: Optional[Dict[str, Any]]
    alternatives_considered: Optional[list[str]]
    category: str
    priority: str
```

#### 2. Streaming Service (`libs/streaming_service.py`)

**Key Features:**
- In-memory event storage with automatic limits (1000 events → 500 after cleanup)
- Connection management with asyncio queues
- Historical event replay for new connections
- Heartbeat mechanism to keep connections alive

**Core Methods:**
```python
async def emit_event(self, event: StreamEvent) -> None:
    # Store event and broadcast to connected clients

async def subscribe(self, decision_set_id: str) -> AsyncGenerator[StreamEvent, None]:
    # Handle client subscriptions with historical replay

async def emit_reason_card(self, reason_card: ReasonCard) -> None:
    # Emit structured agent reasoning events
```

#### 3. Agent Node Integration

Each agent node in `libs/graph.py` has been updated to emit streaming events:

```python
def planner(state: MLOpsWorkflowState) -> MLOpsWorkflowState:
    streaming_service = get_streaming_service()
    thread_id = state.get("decision_set_id")
    
    # Emit node start
    asyncio.create_task(streaming_service.emit_node_start(
        thread_id, "planner", "Analyzing requirements and selecting MLOps patterns"
    ))
    
    # Execute agent logic
    result = asyncio.run(llm_planner_agent.execute(state, TriggerType.INITIAL))
    
    # Create and emit reason card
    streaming_reason_card = create_reason_card(
        agent="planner",
        node="planner",
        decision_set_id=thread_id,
        reasoning=result.reason_card.reasoning,
        decision=result.reason_card.decision,
        category="pattern-selection",
        confidence=result.reason_card.confidence,
        # ... other fields
    )
    asyncio.create_task(streaming_service.emit_reason_card(streaming_reason_card))
    
    # Emit node completion
    asyncio.create_task(streaming_service.emit_node_complete(
        thread_id, "planner", outputs=result.reason_card.outputs
    ))
```

#### 4. SSE API Endpoint (`api/main.py`)

```python
@app.get("/api/streams/{decision_set_id}")
async def stream_workflow_progress(decision_set_id: str, db: Session = Depends(get_db)):
    streaming_service = get_streaming_service()
    
    async def event_generator():
        async for event in streaming_service.subscribe(decision_set_id):
            yield event.to_sse_format()
    
    return EventSourceResponse(
        event_generator(),
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
        }
    )
```

### Event Flow in Backend

1. **Agent Execution**: Each agent node emits events during execution
2. **Streaming Service**: Central hub that stores and broadcasts events
3. **SSE Endpoint**: Provides HTTP connection for real-time event streaming
4. **Connection Management**: Handles multiple clients, cleanup, and reconnection

## Frontend Implementation

### Core Components

#### 1. SSE Hook (`hooks/useStreamingEvents.ts`)

**Key Features:**
- Manages SSE connection lifecycle with automatic reconnection
- Real-time event processing and React state management
- Connection resilience with exponential backoff
- Event deduplication and memory management

**Usage:**
```typescript
const {
  isConnected,
  events,
  reasonCards,
  workflowProgress,
  isWorkflowActive,
  isWorkflowComplete
} = useStreamingEvents({
  decisionSetId: "f1262365-7421-4b84-ba42-86e05e1a729c",
  autoConnect: true,
  reconnectAttempts: 3,
  reconnectDelay: 2000
});
```

**Event Processing:**
```typescript
// Processes incoming SSE events and updates React state
const processStreamEvent = useCallback((event: StreamEvent) => {
  switch (event.type) {
    case 'reason-card':
      setReasonCards(prev => [...prev, event.data as ReasonCard]);
      break;
    case 'node-start':
      setCurrentNode(event.data.node);
      setWorkflowProgress(prev => ({ ...prev, current_node: event.data.node }));
      break;
    case 'node-complete':
      setWorkflowProgress(prev => ({
        ...prev,
        nodes_completed: [...prev.nodes_completed, event.data.node],
        progress_percentage: Math.min(90, prev.nodes_completed.length * 20)
      }));
      break;
  }
}, []);
```

#### 2. Workflow Container (`components/streaming/workflow-container.tsx`)

**Claude-style Unified Interface:**
- Single workflow display per decision set (no duplicate containers)
- Auto-collapsing completed steps to focus on current activity
- Progress header with percentage and status badges
- Collapsible workflow steps with reasoning details

**Step Processing:**
```typescript
// Creates unified workflow steps from events and reason cards
useEffect(() => {
  const processedSteps = new Map<string, WorkflowStepData>();

  // Process node events to create reasoning steps
  events.forEach(event => {
    if (event.type === 'node-start') {
      const nodeId = event.data.node as string;
      const stepTitle = getStepTitle(nodeId); // Human-readable title

      processedSteps.set(`${nodeId}-reasoning`, {
        id: `${nodeId}-reasoning`,
        title: stepTitle,
        status: 'running',
        startTime: event.timestamp,
        stepType: 'reasoning',
      });
    }
  });

  // Attach reason cards to steps
  reasonCards.forEach(reasonCard => {
    const stepId = `${reasonCard.node}-reasoning`;
    const existing = processedSteps.get(stepId);
    if (existing) {
      processedSteps.set(stepId, { ...existing, reasonCard });
    }
  });
}, [events, reasonCards]);
```

#### 3. Workflow Step (`components/streaming/workflow-step.tsx`)

**Collapsible Reasoning Display:**
- Brain icon indicator for reasoning steps
- Expandable/collapsible with chevron indicators
- Rich reason card content when expanded
- Status-based visual styling

**Reason Card Content:**
- **Reasoning Section**: Detailed agent explanation
- **Decision Section**: Key decision made by agent
- **Confidence & Priority**: Visual badges with percentages
- **Alternatives Considered**: List of options the agent evaluated
- **Agent Metadata**: Agent name, node, and timing information

#### 4. Enhanced Chat Interface (`components/chat/enhanced-chat-interface.tsx`)

**Integrated Streaming Features:**
- Calls `/api/chat/async` for non-blocking job creation
- Automatic SSE connection establishment
- Inline workflow display (not separate panel)
- Job status polling with 3-second intervals
- Single WorkflowContainer per unique decisionSetId

**Message Flow:**
```typescript
// Sends message and establishes streaming
const handleSendMessage = async (content: string) => {
  // 1. Send async API request
  const response = await fetch(`${apiBaseUrl}/api/chat/async`, {
    method: "POST",
    body: JSON.stringify({ messages: [{ role: "user", content }] })
  });

  const { decision_set_id, job_id } = await response.json();

  // 2. Create system message with job details
  const systemMessage: EnhancedMessage = {
    role: "assistant",
    content: "🚀 Started MLOps architecture design workflow!...",
    decisionSetId: decision_set_id,
    jobId: job_id,
    isStreamingActive: true
  };

  // 3. Start job status polling
  jobPollingInterval = setInterval(() => {
    pollJobStatus(job_id, decision_set_id);
  }, 3000);
};
```

**Single Container Logic:**
```typescript
// Shows WorkflowContainer only for first message with each decisionSetId
{chatState.messages.map((message, index) => {
  const isFirstMessageWithDecisionSetId =
    message.role === "assistant" && message.decisionSetId &&
    !chatState.messages.slice(0, index).some(m =>
      m.decisionSetId === message.decisionSetId
    );

  return (
    <div key={message.id}>
      {/* Message display */}
      <MessageCard content={message.content} />

      {/* Single workflow container per decision set */}
      {isFirstMessageWithDecisionSetId && (
        <WorkflowContainer decisionSetId={message.decisionSetId} />
      )}
    </div>
  );
})}
```

### Frontend Event Processing

1. **Connection Establishment**: SSE connection to backend endpoint
2. **Event Reception**: Real-time event processing with type safety
3. **State Updates**: React state updates trigger UI re-renders
4. **Component Updates**: Specialized components display different event types
5. **Connection Resilience**: Automatic reconnection on connection loss

## Data Models & Types

### Backend Models (Python)

```python
# Event Types
StreamEventType = Literal[
    "reason-card", "node-start", "node-complete", 
    "workflow-start", "workflow-complete", 
    "error", "heartbeat", "workflow-paused"
]

# Reason Card Structure
class ReasonCard(BaseModel):
    agent: str                                    # Agent identifier
    node: str                                     # Graph node name
    decision_set_id: str                         # Workflow session ID
    timestamp: datetime                          # Creation time
    reasoning: str                               # Human-readable explanation
    decision: str                                # Key decision made
    confidence: Optional[float]                  # Confidence (0.0-1.0)
    category: str                                # Decision category
    priority: str                                # Priority level
    inputs: Optional[Dict[str, Any]]            # Input data
    outputs: Optional[Dict[str, Any]]           # Output results
    alternatives_considered: Optional[list[str]] # Alternative options
```

### Frontend Types (TypeScript)

```typescript
// Event Types
type StreamEventType = 
  | 'reason-card' | 'node-start' | 'node-complete'
  | 'workflow-start' | 'workflow-complete' 
  | 'error' | 'heartbeat' | 'workflow-paused';

// Streaming State
interface StreamingState {
  isConnected: boolean;
  events: StreamEvent[];
  reasonCards: ReasonCard[];
  workflowProgress: WorkflowProgress | null;
  currentNode: string | null;
  error: string | null;
}

// Workflow Progress
interface WorkflowProgress {
  current_node?: string;
  nodes_completed: string[];
  nodes_remaining: string[];
  progress_percentage: number;
  status: string;
}
```

## Testing & Quality Assurance

### Backend Tests (`tests/test_streaming_functionality.py`)

**Coverage:**
- 24 comprehensive test cases
- StreamingService functionality
- Event processing and storage
- Connection management
- SSE formatting
- Integration testing

**Key Test Categories:**
```python
class TestStreamingService:
    def test_emit_event()                    # Basic event emission
    def test_emit_reason_card()              # Reason card streaming
    def test_subscription_with_historical_events()  # Event replay
    def test_event_limit_enforcement()       # Memory management
    def test_connection_count_tracking()     # Connection monitoring
```

### Frontend Quality Assurance

**TypeScript Compilation:**
- ✅ Strict type checking passes
- ✅ All components type-safe
- ✅ Full IntelliSense support

**Build Verification:**
- ✅ Production build successful
- ✅ Development server starts without errors
- ✅ Component integration verified

## Deployment & Configuration

### Environment Variables

**Backend:**
- `USE_FULL_GRAPH`: Enable full workflow graph (default: false)
- `LOG_LEVEL`: Logging verbosity (default: INFO)
- `DATABASE_URL`: Database connection string
- `ANTHROPIC_API_KEY`: Claude API key for agent reasoning

**Frontend:**
- `NEXT_PUBLIC_API_BASE_URL`: Backend API URL (default: http://localhost:8000)

### Production Considerations

1. **Memory Management**: 
   - Event storage limited to 1000 events per decision set
   - Automatic cleanup to 500 events when limit reached
   - Connection cleanup on workflow completion

2. **Scalability**:
   - In-memory storage suitable for single-instance deployment
   - For multi-instance: consider Redis or database-backed event storage
   - Connection pooling and load balancing considerations

3. **Error Handling**:
   - Graceful degradation when SSE connection fails
   - Automatic reconnection with exponential backoff
   - User-friendly error messages and manual reconnection

4. **Security**:
   - CORS configuration for production domains
   - Authentication integration ready
   - Input validation on all endpoints

## Usage Examples

### Starting a Workflow with Streaming

1. **User Input**: "Design an MLOps pipeline for real-time fraud detection"

2. **Backend Response**: 
```json
{
  "decision_set_id": "ds_7a8b9c0d",
  "job_id": "job_1f2e3d4c",
  "thread_id": "thread_5b6a7d8e",
  "status": "pending"
}
```

3. **Real-time Events**:
```
event: workflow-start
data: {"type": "workflow-start", "decision_set_id": "ds_7a8b9c0d", ...}

event: node-start
data: {"type": "node-start", "data": {"node": "planner"}, ...}

event: reason-card
data: {
  "type": "reason-card",
  "data": {
    "agent": "planner",
    "decision": "Selected microservices architecture pattern",
    "reasoning": "Based on real-time requirements and scalability needs...",
    "confidence": 0.87,
    "alternatives_considered": ["Monolithic", "Serverless", "Event-driven"]
  }
}

event: node-complete
data: {"type": "node-complete", "data": {"node": "planner"}, ...}
```

### Frontend Integration

```typescript
// Component usage
function MyWorkflowComponent() {
  const [decisionSetId, setDecisionSetId] = useState<string>();
  
  return (
    <div>
      <EnhancedChatInterface 
        onWorkflowStart={(dsId) => setDecisionSetId(dsId)}
      />
      {decisionSetId && (
        <StreamingPanel 
          decisionSetId={decisionSetId}
          showProgress={true}
          showReasonCards={true}
        />
      )}
    </div>
  );
}
```

## Troubleshooting

### Common Issues

1. **SSE Connection Failed**:
   - Check CORS configuration
   - Verify API base URL in frontend
   - Ensure backend streaming service is running

2. **Events Not Appearing**:
   - Verify decision_set_id matches between frontend and backend
   - Check browser network tab for SSE connection
   - Review backend logs for streaming errors

3. **Memory Issues**:
   - Monitor event storage limits
   - Check for connection leaks
   - Verify cleanup is working properly

### Debug Tools

**Backend Debugging:**
```python
# Enable detailed logging
logging.getLogger('libs.streaming_service').setLevel(logging.DEBUG)

# Check active connections
streaming_service = get_streaming_service()
active_streams = streaming_service.get_all_active_streams()
```

**Frontend Debugging:**
```typescript
// Hook debugging
const streaming = useStreamingEvents({ decisionSetId });
console.log('Connection state:', {
  isConnected: streaming.isConnected,
  eventCount: streaming.events.length,
  reasonCardCount: streaming.reasonCards.length
});
```

## Future Enhancements

### Planned Improvements

1. **Persistence Layer**:
   - Database storage for event history
   - Event replay from database
   - Multi-instance support

2. **Advanced Features**:
   - Event filtering and search
   - Export functionality
   - Analytics and metrics

3. **Performance Optimizations**:
   - Event compression
   - Selective event subscriptions
   - Connection pooling

4. **Enhanced UI**:
   - Reason card comparison
   - Workflow visualization
   - Interactive decision trees

---

This comprehensive guide provides a complete understanding of the streaming architecture implementation. The system successfully delivers transparent, real-time visibility into AI agent reasoning while maintaining excellent performance and user experience.