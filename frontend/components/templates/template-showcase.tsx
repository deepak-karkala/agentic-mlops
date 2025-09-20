"use client";

import { MlopsTemplate } from "@/data/mlops-templates";
import { WorkflowVisualization } from "@/components/streaming/workflow-visualization";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LandingThemeConfig } from "@/data/landing-themes";
import { cn } from "@/lib/utils";
import { ArrowLeft, CalendarClock, Download, RefreshCw } from "lucide-react";

interface TemplateShowcaseProps {
  template: MlopsTemplate;
  onDismiss: () => void;
  onRunLive: (prompt: string) => void;
  theme: LandingThemeConfig;
}

export function TemplateShowcase({ template, onDismiss, onRunLive, theme }: TemplateShowcaseProps) {
  const isDark = theme.id === "midnight";

  return (
    <section className="space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-6">
        <div className="space-y-3">
          <div
            className={cn(
              "flex flex-wrap items-center gap-2 text-[0.68rem] uppercase tracking-[0.28em]",
              isDark ? "text-slate-400" : "text-espresso/60",
            )}
          >
            {template.tags.map((tag) => (
              <span key={tag} className={theme.templateShowcase.tag}>
                {tag}
              </span>
            ))}
          </div>
          <h2
            className={cn(
              "font-display text-3xl leading-tight",
              isDark ? "text-slate-100" : "text-espresso",
            )}
          >
            {template.name}
          </h2>
          <p
            className={cn(
              "max-w-3xl text-base leading-relaxed",
              isDark ? "text-slate-400" : "text-espresso/70",
            )}
          >
            {template.summary}
          </p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Button
            variant="ghost"
            onClick={onDismiss}
            className="gap-2 rounded-full bg-transparent px-4 py-2 text-sm text-espresso/70 hover:bg-sandHover"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to templates
          </Button>
          <Button
            onClick={() => onRunLive(template.userPrompt)}
            variant="accent"
            className="gap-2 rounded-full px-6 py-4 text-sm font-semibold transition hover:-translate-y-0.5"
          >
            <RefreshCw className="h-4 w-4" />
            Run live with these requirements
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
        <div className="space-y-4">
          <div
            className={cn(
              "space-y-5 rounded-[1.75rem] p-6 shadow-sm",
              theme.templateShowcase.infoCard,
            )}
          >
            <div className="space-y-3">
              <h3 className="text-xs font-semibold uppercase tracking-[0.32em] text-espresso/60">
                Template overview
              </h3>
              <p className={cn("text-sm leading-relaxed", theme.templateShowcase.summaryText)}>
                {template.systemIntro}
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {template.techStack.map((tech) => (
                <Badge
                  key={tech}
                  variant="outline"
                  className="rounded-full border border-espresso/20 bg-white/80 px-3 py-1 text-[11px] uppercase tracking-[0.2em] text-espresso/70"
                >
                  {tech}
                </Badge>
              ))}
            </div>
            <div className="grid gap-3 text-sm">
              {template.heroStats.map((stat) => (
                <div
                  key={stat.label}
                  className="flex items-center justify-between rounded-2xl border border-espresso/12 bg-sand/70 px-4 py-3"
                >
                  <span className={theme.templateShowcase.stat}>{stat.label}</span>
                  <span
                    className={cn(
                      "font-semibold",
                      isDark ? "text-slate-100" : "text-espresso",
                    )}
                  >
                    {stat.value}
                  </span>
                </div>
              ))}
            </div>
          </div>
          <div
            className={cn(
              "space-y-4 rounded-[1.75rem] p-6 shadow-sm",
              theme.templateShowcase.conversationCard,
            )}
          >
            <h3 className="text-xs font-semibold uppercase tracking-[0.32em] text-espresso/60">
              Conversation snapshot
            </h3>
            <ul className="space-y-3 text-sm">
              {template.messages.map((message) => {
                const messageTime =
                  message.timestamp instanceof Date
                    ? message.timestamp
                    : new Date(message.timestamp);
                return (
                  <li
                    key={message.id}
                    className="rounded-2xl border border-espresso/10 bg-white/90 px-4 py-3"
                  >
                    <div className="flex items-center justify-between text-[0.7rem] uppercase tracking-[0.2em] text-espresso/45">
                      <span>{message.role === "user" ? "User" : "Agent"}</span>
                      <span className="flex items-center gap-1">
                        <CalendarClock className="h-3.5 w-3.5" />
                        {messageTime.toLocaleTimeString([], {
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    <p className="mt-2 text-sm leading-relaxed text-espresso/80 whitespace-pre-line">
                      {message.content}
                    </p>
                  </li>
                );
              })}
            </ul>
          </div>
          <div
            className={cn(
              "space-y-4 rounded-[1.75rem] p-6 shadow-sm",
              theme.templateShowcase.documentCard,
            )}
          >
            <div className="space-y-2">
              <h3 className="text-xs font-semibold uppercase tracking-[0.32em] text-espresso/60">
                Deliverable preview
              </h3>
              <p className="text-sm leading-relaxed text-espresso/75">
                Food truck consulting report — DOCX export with analysis, insights, and executive summary ready for stakeholders.
              </p>
            </div>
            <div className="flex flex-wrap items-center gap-3 rounded-2xl border border-espresso/12 bg-sand/70 px-4 py-3 text-sm text-espresso/70">
              <span className="font-semibold">food_truck_consulting_report.docx</span>
              <span className="text-xs uppercase tracking-[0.28em]">Document</span>
            </div>
            <Button
              variant="accent"
              className="w-full justify-center gap-2 rounded-full px-6 py-4 text-sm font-semibold transition hover:-translate-y-0.5"
            >
              <Download className="h-4 w-4" />
              Download preview
            </Button>
          </div>
        </div>
        <WorkflowVisualization
          decisionSetId={template.id}
          plan={template.planNodes}
          graphType={template.graphType}
          staticState={template.workflowState}
          className={theme.templateShowcase.vizContainer}
        />
      </div>
    </section>
  );
}
