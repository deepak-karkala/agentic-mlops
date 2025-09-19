import { CheckCircle2, Loader2, Clock3, Plug, SignalHigh } from "lucide-react";
import { cn } from "@/lib/utils";
import {
  getWorkflowNodeLabel,
  getWorkflowNodeDescription,
} from "@/lib/workflow";

export type TimelineStatus = "completed" | "running" | "pending";

export interface TimelineNode {
  id: string;
  status: TimelineStatus;
}

interface WorkflowStatusPanelProps {
  nodes: TimelineNode[];
  completedCount: number;
  totalCount: number;
  isConnected: boolean;
  isConnecting: boolean;
  connectionError: boolean;
  graphType?: string;
  className?: string;
}

const STATUS_STYLES: Record<TimelineStatus, { circle: string; badge: string; label: string }> = {
  completed: {
    circle: "bg-emerald-500 border-emerald-600",
    badge: "bg-emerald-100 text-emerald-700",
    label: "Completed",
  },
  running: {
    circle: "bg-yellow-400 border-yellow-500",
    badge: "bg-amber-100 text-amber-700",
    label: "In Progress",
  },
  pending: {
    circle: "bg-orange-300 border-orange-400",
    badge: "bg-orange-100 text-orange-700",
    label: "Queued",
  },
};

export function WorkflowStatusPanel({
  nodes,
  completedCount,
  totalCount,
  isConnected,
  isConnecting,
  connectionError,
  graphType,
  className,
}: WorkflowStatusPanelProps) {
  const progressPercentage = totalCount
    ? Math.min(100, Math.round((completedCount / totalCount) * 100))
    : 0;

  const connectionStatusLabel = (() => {
    if (isConnecting) return "Connecting";
    if (connectionError) return "Reconnecting";
    return isConnected ? "Live" : "Offline";
  })();

  return (
    <div
      className={cn(
        "border bg-card rounded-xl p-4 shadow-sm h-full",
        "flex flex-col",
        className,
      )}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h3 className="text-sm font-semibold text-foreground uppercase tracking-wide">
            Workflow Timeline
          </h3>
          <p className="text-xs text-muted-foreground mt-1">
            {graphType ? `${graphType.replace(/_/g, " ")}` : "Agent execution order"}
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs font-medium">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded-full border",
              connectionError
                ? "border-amber-400 text-amber-600"
                : isConnected
                ? "border-emerald-400 text-emerald-600"
                : "border-slate-300 text-slate-500",
            )}
          >
            {isConnected ? (
              <SignalHigh className="h-3 w-3" />
            ) : connectionError ? (
              <Loader2 className="h-3 w-3 animate-spin" />
            ) : (
              <Plug className="h-3 w-3" />
            )}
            {connectionStatusLabel}
          </span>
        </div>
      </div>

      <div className="mt-3">
        <div className="flex items-center justify-between text-xs text-muted-foreground">
          <span>
            {completedCount} / {totalCount} steps complete
          </span>
          <span>{progressPercentage}%</span>
        </div>
        <div className="mt-2 h-2 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full bg-emerald-500 transition-all duration-500"
            style={{ width: `${progressPercentage}%` }}
          />
        </div>
      </div>

      <div className="mt-4 flex-1 overflow-y-auto pr-1">
        {nodes.length === 0 ? (
          <div className="text-xs text-muted-foreground bg-muted/50 border border-dashed border-muted rounded-lg px-3 py-2">
            Timeline will populate as soon as the workflow emits activity.
          </div>
        ) : (
          <div className="relative">
            <div className="absolute left-[11px] top-3 bottom-3 w-px bg-border" aria-hidden />
            <div className="space-y-3">
              {nodes.map((node) => {
                const metadata = STATUS_STYLES[node.status];
                const label = getWorkflowNodeLabel(node.id);
                const description = getWorkflowNodeDescription(node.id);
                const isRunning = node.status === "running";

                const icon = node.status === "completed"
                  ? <CheckCircle2 className="h-3.5 w-3.5" />
                  : node.status === "running"
                    ? <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    : <Clock3 className="h-3.5 w-3.5" />;

                return (
                  <div key={node.id} className="pl-8 relative">
                    <div className="absolute left-0 top-1.5 h-5 w-5">
                      {isRunning && (
                        <span
                          className="absolute inset-0 rounded-full border-2 border-amber-300/70 animate-ping"
                          aria-hidden
                        />
                      )}
                      <span
                        className={cn(
                          "relative z-10 h-5 w-5 rounded-full border-2 flex items-center justify-center text-white",
                          metadata.circle,
                          isRunning && "shadow-[0_0_0_4px_rgba(253,224,71,0.25)]",
                        )}
                      >
                        {icon}
                      </span>
                    </div>
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <p className="text-sm font-medium text-foreground">
                          {label}
                        </p>
                        {description && (
                          <p className="text-xs text-muted-foreground mt-1">
                            {description}
                          </p>
                        )}
                      </div>
                      <span
                        className={cn(
                          "text-[10px] uppercase tracking-wide rounded-full px-2 py-1 font-semibold",
                          metadata.badge,
                        )}
                      >
                        {metadata.label}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
