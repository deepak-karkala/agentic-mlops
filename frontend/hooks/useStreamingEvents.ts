/**
 * React hook for consuming Server-Sent Events (SSE) from the MLOps streaming API
 * 
 * This hook manages SSE connections and provides real-time updates including:
 * - Reason cards from agents
 * - Node start/completion events
 * - Workflow progress updates
 * - Error notifications
 */

import { useState, useEffect, useCallback, useRef } from 'react';

export type StreamEventType = 
  | 'reason-card'
  | 'node-start'
  | 'node-complete'
  | 'workflow-start'
  | 'workflow-complete'
  | 'error'
  | 'heartbeat'
  | 'workflow-paused';

export interface ReasonCard {
  agent: string;
  node: string;
  decision_set_id: string;
  timestamp: string;
  duration_ms?: number;
  reasoning: string;
  decision: string;
  confidence?: number;
  inputs?: Record<string, any>;
  outputs?: Record<string, any>;
  alternatives_considered?: string[];
  category: string;
  priority: string;
  references?: string[];
}

export interface StreamEvent {
  type: StreamEventType;
  decision_set_id: string;
  timestamp: string;
  data: Record<string, any>;
  message?: string;
}

export interface WorkflowProgress {
  current_node?: string;
  nodes_completed: string[];
  nodes_remaining: string[];
  progress_percentage: number;
  status: string;
  estimated_time_remaining_ms?: number;
}

export interface StreamingState {
  isConnected: boolean;
  isConnecting: boolean;
  events: StreamEvent[];
  reasonCards: ReasonCard[];
  workflowProgress: WorkflowProgress | null;
  currentNode: string | null;
  error: string | null;
  connectionError: boolean;
}

export interface UseStreamingEventsOptions {
  decisionSetId?: string;
  autoConnect?: boolean;
  reconnectAttempts?: number;
  reconnectDelay?: number; // milliseconds
}

export function useStreamingEvents(options: UseStreamingEventsOptions = {}) {
  const {
    decisionSetId,
    autoConnect = true,
    reconnectAttempts = 3,
    reconnectDelay = 2000,
  } = options;

  const [state, setState] = useState<StreamingState>({
    isConnected: false,
    isConnecting: false,
    events: [],
    reasonCards: [],
    workflowProgress: null,
    currentNode: null,
    error: null,
    connectionError: false,
  });

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectCountRef = useRef(0);


  // Get API base URL
  const getApiBaseUrl = () => {
    return typeof window !== 'undefined' 
      ? process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000'
      : 'http://localhost:8000';
  };

  // Clear reconnect timeout
  const clearReconnectTimeout = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
  }, []);

  // Process incoming stream event
  const processStreamEvent = useCallback((event: StreamEvent) => {

    setState(prevState => {
      const newState = { ...prevState };

      // Add event to history
      newState.events = [...prevState.events, event];

      // Limit event history to prevent memory issues
      if (newState.events.length > 1000) {
        newState.events = newState.events.slice(-500);
      }

      // Process specific event types
      switch (event.type) {
        case 'reason-card':
          const reasonCard = event.data as ReasonCard;
          newState.reasonCards = [...prevState.reasonCards, reasonCard];
          console.log('Added reason card:', {
            agent: reasonCard.agent,
            node: reasonCard.node,
            decision: reasonCard.decision
          });
          break;

        case 'node-start':
          newState.currentNode = event.data.node as string;

          // Create or update workflow progress
          if (!newState.workflowProgress) {
            newState.workflowProgress = {
              current_node: event.data.node as string,
              nodes_completed: [],
              nodes_remaining: [],
              progress_percentage: 10,
              status: 'running',
            };
          } else {
            newState.workflowProgress = {
              ...newState.workflowProgress,
              current_node: event.data.node as string,
              status: 'running',
            };
          }
          console.log('Node started:', event.data.node);
          break;

        case 'node-complete':
          const completedNode = event.data.node as string;

          if (newState.workflowProgress) {
            const nodesCompleted = [...newState.workflowProgress.nodes_completed];
            if (!nodesCompleted.includes(completedNode)) {
              nodesCompleted.push(completedNode);
            }

            newState.workflowProgress = {
              ...newState.workflowProgress,
              nodes_completed: nodesCompleted,
              current_node: undefined,
              progress_percentage: Math.min(90, nodesCompleted.length * 20), // More gradual progress
              status: 'running', // Keep running until workflow-complete
            };
          } else {
            // Create workflow progress if it doesn't exist
            newState.workflowProgress = {
              current_node: undefined,
              nodes_completed: [completedNode],
              nodes_remaining: [],
              progress_percentage: 20,
              status: 'running',
            };
          }

          console.log('Node completed:', completedNode, 'Progress:', newState.workflowProgress.progress_percentage + '%');
          break;

        case 'workflow-start':
          newState.workflowProgress = {
            current_node: undefined,
            nodes_completed: [],
            nodes_remaining: [],
            progress_percentage: 5,
            status: 'running',
          };
          console.log('Workflow started - initializing progress tracking');
          break;

        case 'workflow-complete':
          if (newState.workflowProgress) {
            newState.workflowProgress = {
              ...newState.workflowProgress,
              status: 'completed',
              progress_percentage: 100,
              current_node: undefined,
            };
          }
          break;

        case 'workflow-paused':
          if (newState.workflowProgress) {
            newState.workflowProgress = {
              ...newState.workflowProgress,
              status: 'paused',
            };
          }
          break;

        case 'error':
          newState.error = event.data.error as string;
          if (newState.workflowProgress) {
            newState.workflowProgress = {
              ...newState.workflowProgress,
              status: 'error',
            };
          }
          break;

        case 'heartbeat':
          // Heartbeat events just keep the connection alive
          break;
      }

      return newState;
    });
  }, []);

  // Connect to SSE endpoint
  const connect = useCallback((targetDecisionSetId?: string) => {
    const dsId = targetDecisionSetId || decisionSetId;
    if (!dsId) {
      console.warn('Cannot connect: no decision set ID provided');
      return;
    }

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    setState(prevState => ({
      ...prevState,
      isConnecting: true,
      connectionError: false,
      error: null,
    }));

    const apiBaseUrl = getApiBaseUrl();
    const url = `${apiBaseUrl}/api/streams/${dsId}`;
    
    console.log(`Connecting to SSE endpoint: ${url}`);
    
    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('SSE connection opened');
      reconnectCountRef.current = 0;
      setState(prevState => ({
        ...prevState,
        isConnected: true,
        isConnecting: false,
        connectionError: false,
      }));
    };

    // Explicitly disable onmessage to prevent duplicate processing
    eventSource.onmessage = null;

    eventSource.onerror = (error) => {
      console.error('SSE connection error:', error);
      setState(prevState => ({
        ...prevState,
        isConnected: false,
        isConnecting: false,
        connectionError: true,
      }));

      // Attempt reconnection if within limits
      if (reconnectCountRef.current < reconnectAttempts) {
        reconnectCountRef.current++;
        console.log(`Attempting to reconnect (${reconnectCountRef.current}/${reconnectAttempts})`);
        
        clearReconnectTimeout();
        reconnectTimeoutRef.current = setTimeout(() => {
          connect(dsId);
        }, reconnectDelay);
      } else {
        console.error('Max reconnection attempts reached');
        setState(prevState => ({
          ...prevState,
          error: 'Connection failed after multiple attempts',
        }));
      }
    };

    // Handle all event types
    const eventTypes = [
      'reason-card',
      'node-start', 
      'node-complete',
      'workflow-start',
      'workflow-complete',
      'workflow-paused',
      'error',
      'heartbeat'
    ];

    eventTypes.forEach(eventType => {
      eventSource.addEventListener(eventType, (event) => {
        try {
          console.log(`Received ${eventType} event:`, {
            data: event.data,
            dataType: typeof event.data,
            eventData: event.data
          });

          // Handle case where event.data might be undefined or empty
          if (!event.data) {
            console.warn(`${eventType} event has no data, skipping`);
            return;
          }

          const data = JSON.parse(event.data);
          processStreamEvent(data as StreamEvent);
        } catch (parseError) {
          console.error(`Failed to parse ${eventType} event:`, parseError, {
            data: event.data,
            dataType: typeof event.data
          });
        }
      });
    });

    // All events are handled by explicit event type listeners above

  }, [decisionSetId, reconnectAttempts, reconnectDelay, processStreamEvent, clearReconnectTimeout]);

  // Disconnect from SSE endpoint
  const disconnect = useCallback(() => {
    clearReconnectTimeout();
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setState(prevState => ({
      ...prevState,
      isConnected: false,
      isConnecting: false,
    }));
  }, [clearReconnectTimeout]);

  // Clear events and reason cards
  const clearEvents = useCallback(() => {
    setState(prevState => ({
      ...prevState,
      events: [],
      reasonCards: [],
      workflowProgress: null,
      currentNode: null,
      error: null,
    }));
  }, []);

  // Auto-connect effect
  useEffect(() => {
    if (autoConnect && decisionSetId) {
      connect(decisionSetId);
    }

    return () => {
      disconnect();
    };
  }, [autoConnect, decisionSetId, connect, disconnect]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      clearReconnectTimeout();
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, [clearReconnectTimeout]);

  return {
    // State
    ...state,
    
    // Actions
    connect,
    disconnect,
    clearEvents,
    
    // Derived values
    hasEvents: state.events.length > 0,
    hasReasonCards: state.reasonCards.length > 0,
    isWorkflowActive: state.workflowProgress?.status === 'running',
    isWorkflowPaused: state.workflowProgress?.status === 'paused',
    isWorkflowComplete: state.workflowProgress?.status === 'completed',
    
    // Latest values for easy access
    latestReasonCard: state.reasonCards[state.reasonCards.length - 1] || null,
    latestEvent: state.events[state.events.length - 1] || null,
  };
}