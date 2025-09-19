import { useMemo } from "react";
import { cn } from "@/lib/utils";
import { useStreamingEvents } from "@/hooks/useStreamingEvents";
import { WorkflowContainer } from "./workflow-container";
import {
  TimelineNode,
  WorkflowStatusPanel,
} from "./workflow-status-panel";

interface WorkflowVisualizationProps {
  decisionSetId: string;
  plan: string[];
  graphType?: string;
  className?: string;
}

function uniqueSequence(values: Array<string | undefined | null>): string[] {
  const seen = new Set<string>();
  const ordered: string[] = [];
  values.forEach((value) => {
    if (!value) return;
    if (!seen.has(value)) {
      seen.add(value);
      ordered.push(value);
    }
  });
  return ordered;
}

export function WorkflowVisualization({
  decisionSetId,
  plan,
  graphType,
  className,
}: WorkflowVisualizationProps) {
  const streaming = useStreamingEvents({
    decisionSetId,
    autoConnect: true,
    reconnectAttempts: 5,
    reconnectDelay: 2500,
  });

  const {
    events,
    reasonCards,
    workflowProgress,
    isConnected,
    isConnecting,
    connectionError,
  } = streaming;

  const basePlan = useMemo(() => uniqueSequence(plan), [plan]);

  const combinedPlan = useMemo(() => {
    const ordered = [...basePlan];
    const seen = new Set(ordered);

    const append = (candidate?: string | null) => {
      if (!candidate) return;
      if (seen.has(candidate)) return;
      seen.add(candidate);
      ordered.push(candidate);
    };

    events
      .map((event) => event.data?.node as string | undefined)
      .forEach((node) => append(node));

    (workflowProgress?.nodes_completed ?? []).forEach((node) => append(node));
    append(workflowProgress?.current_node ?? undefined);

    reasonCards.forEach((card) => append(card.node));

    return ordered;
  }, [basePlan, events, reasonCards, workflowProgress]);

  const completedSet = useMemo(() => {
    const nodes = workflowProgress?.nodes_completed ?? [];
    return new Set(nodes);
  }, [workflowProgress?.nodes_completed]);

  const currentNode = workflowProgress?.current_node ?? null;

  const timeline: TimelineNode[] = useMemo(() => {
    if (combinedPlan.length === 0) {
      return [];
    }

    return combinedPlan.map((node) => {
      let status: TimelineNode["status"] = "pending";

      if (completedSet.has(node)) {
        status = "completed";
      } else if (node === currentNode) {
        status = "running";
      }

      return { id: node, status };
    });
  }, [combinedPlan, completedSet, currentNode]);

  const completedCount = timeline.filter((node) => node.status === "completed").length;
  const totalCount = timeline.length;

  return (
    <div
      className={cn(
        "grid gap-4 md:grid-cols-1 lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]",
        className,
      )}
    >
      <WorkflowStatusPanel
        nodes={timeline}
        completedCount={completedCount}
        totalCount={totalCount}
        isConnected={isConnected}
        isConnecting={isConnecting}
        connectionError={connectionError}
        graphType={graphType}
        className="min-h-[18rem]"
      />
      <div className="min-w-0">
        <WorkflowContainer
          decisionSetId={decisionSetId}
          className="h-full"
          streamingState={streaming}
        />
      </div>
    </div>
  );
}
