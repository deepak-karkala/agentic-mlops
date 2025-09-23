"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import EnhancedChatInterface from "@/components/chat/enhanced-chat-interface";
import { HeroSection } from "@/components/landing/hero-section";
import { TemplateCard } from "@/components/templates/template-card";
import { TemplateShowcase } from "@/components/templates/template-showcase";
import { WorkflowVisualization } from "@/components/streaming/workflow-visualization";
import {
  MLOPS_TEMPLATES,
  getTemplateById,
  MlopsTemplate,
} from "@/data/mlops-templates";
import {
  LANDING_THEME_OPTIONS,
  LANDING_THEMES,
  LandingThemeId,
} from "@/data/landing-themes";
import { Button } from "@/components/ui/button";
import { ArrowRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

export default function Home() {
  const [mounted, setMounted] = useState(false);
  const [mode, setMode] = useState<"idle" | "template" | "live">("idle");
  const [themeId, setThemeId] = useState<LandingThemeId>("claude");
  const [activeTemplate, setActiveTemplate] = useState<MlopsTemplate | null>(
    null,
  );
  const [pendingPrompt, setPendingPrompt] = useState<string | null>(null);
  const chatSectionRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  const templates = useMemo(() => MLOPS_TEMPLATES, []);
  const [selectedTemplateId, setSelectedTemplateId] = useState<string | null>(
    templates[0]?.id ?? null,
  );
  const selectedTemplate = useMemo(() => {
    if (!selectedTemplateId) {
      return templates[0] ?? null;
    }
    return templates.find((t) => t.id === selectedTemplateId) ?? templates[0] ?? null;
  }, [selectedTemplateId, templates]);
  const theme = LANDING_THEMES[themeId];
  const isDark = themeId === "midnight";

  const scrollToChat = () => {
    if (!chatSectionRef.current) return;
    chatSectionRef.current.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  const resetTemplateState = () => {
    setActiveTemplate(null);
    setPendingPrompt(null);
  };

  const handleExploreTemplates = () => {
    scrollToChat();
  };

  const handleStartCustom = () => {
    resetTemplateState();
    setMode("live");
    scrollToChat();
  };

  const handleTemplateHighlight = (templateId: string) => {
    setSelectedTemplateId(templateId);
  };

  const handleTemplateSelect = (templateId: string) => {
    const template = getTemplateById(templateId);
    if (!template) return;
    setSelectedTemplateId(templateId);
    setActiveTemplate(template);
    setMode("template");
    scrollToChat();
  };

  const handleDismissTemplate = () => {
    resetTemplateState();
    setMode("idle");
  };

  const handleRunTemplateLive = (prompt: string) => {
    setPendingPrompt(prompt);
    setActiveTemplate(null);
    setMode("live");
    requestAnimationFrame(() => scrollToChat());
  };

  const handlePromptConsumed = () => {
    setPendingPrompt(null);
  };

  if (!mounted) {
    return null;
  }

  return (
    <main className={cn("relative min-h-screen pb-32 pt-12", theme.pageBackground)}>
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-20 px-4 py-12 sm:px-6 lg:px-8 xl:px-12">
        <div className="flex justify-end">
          <div
            className={cn(
              "flex items-center gap-1.5 rounded-full p-1.5 backdrop-blur",
              theme.switcher.wrapper,
            )}
          >
            {LANDING_THEME_OPTIONS.map((option) => {
              const isActive = option.id === themeId;
              return (
                <Button
                  key={option.id}
                  variant="ghost"
                  size="sm"
                  className={cn(
                    "h-9 min-w-[70px] rounded-full px-4 text-xs font-medium transition-all duration-200",
                    isActive ? theme.switcher.active : theme.switcher.inactive,
                  )}
                  onClick={() => setThemeId(option.id)}
                >
                  {option.label}
                </Button>
              );
            })}
          </div>
        </div>

        <HeroSection
          onExploreTemplates={handleExploreTemplates}
          onStartCustom={handleStartCustom}
          theme={theme}
        />

        <section className="space-y-12">
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div className="space-y-4">
              <p className={theme.gallery.badge}>
                <Sparkles className="h-3.5 w-3.5" />
                Curated blueprints
              </p>
              <h2 className={cn("mt-1 font-display", theme.gallery.heading)}>
                Jump into an agent-crafted launch plan
              </h2>
              <p className={cn("max-w-2xl text-[0.98rem] leading-7", theme.gallery.description)}>
                Explore production-ready workflows without waiting for a full run. Each template arrives with finished reasoning cards, timelines, and architecture decisions you can tweak in moments.
              </p>
            </div>
            <Button
              variant="outline"
              className={cn(theme.gallery.actionButton, "group flex items-center gap-2 rounded-full px-6 py-4 text-sm font-semibold transition")}
              onClick={handleStartCustom}
            >
              Start from scratch
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
          </div>
          <div className="grid gap-8 xl:grid-cols-[minmax(0,320px)_minmax(0,1fr)]">
            <div
              className="flex flex-col gap-4"
              role="tablist"
              aria-label="Agent-crafted MLOps templates"
            >
              {templates.map((template) => (
                <TemplateCard
                  key={template.id}
                  template={template}
                  onSelect={handleTemplateHighlight}
                  isSelected={selectedTemplate?.id === template.id}
                  theme={theme}
                  variant="compact"
                />
              ))}
            </div>

            <div
              className={cn(
                "flex min-h-[420px] flex-col gap-6 rounded-[1.75rem] border border-espresso/10 bg-white/90 p-6 shadow-floating backdrop-blur-sm",
                "xl:max-h-[120vh] xl:overflow-hidden",
                isDark &&
                "border-slate-800/80 bg-slate-900/70 text-slate-100 shadow-[0_20px_60px_rgba(15,23,42,0.45)]",
              )}
            >
              {selectedTemplate && (
                <div className="space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div
                      className={cn(
                        "flex flex-wrap items-center gap-2 text-[0.62rem] font-semibold uppercase tracking-[0.28em]",
                        isDark ? "text-slate-300" : "text-espresso/55",
                      )}
                    >
                      {selectedTemplate.tags.slice(0, 4).map((tag) => (
                        <span
                          key={tag}
                          className={cn(
                            "rounded-full border px-3 py-1 text-[0.6rem]",
                            isDark
                              ? "border-slate-700 text-slate-200"
                              : "border-espresso/15 text-espresso/65",
                          )}
                        >
                          {tag}
                        </span>
                      ))}
                    </div>
                    <Button
                      variant="ghost"
                      size="sm"
                      className={cn(
                        "rounded-full px-3 py-1.5 text-[0.78rem] font-semibold",
                        isDark
                          ? "text-cyan-200 hover:bg-slate-800"
                          : "text-espresso/70 hover:bg-sandHover",
                      )}
                      onClick={() => selectedTemplate && handleTemplateSelect(selectedTemplate.id)}
                    >
                      View full template
                    </Button>
                  </div>
                  <div className="space-y-2">
                    <h3 className={cn("font-display text-2xl leading-snug", isDark ? "text-slate-100" : "text-espresso")}
                    >
                      {selectedTemplate.name}
                    </h3>
                    <p className={cn("text-sm leading-relaxed", isDark ? "text-slate-300" : "text-espresso/75")}
                    >
                      {selectedTemplate.summary}
                    </p>
                  </div>
                  <div
                    className={cn(
                      "flex flex-wrap gap-3 text-[0.7rem] uppercase tracking-[0.24em]",
                      isDark ? "text-slate-400" : "text-espresso/55",
                    )}
                  >
                    {selectedTemplate.heroStats.slice(0, 3).map((stat) => (
                      <div
                        key={stat.label}
                        className={cn(
                          "flex items-center gap-2 rounded-full border px-3 py-1",
                          isDark ? "border-slate-700/60" : "border-espresso/12",
                        )}
                      >
                        <span
                          className={cn(
                            "text-[0.9rem] font-semibold",
                            isDark ? "text-slate-100" : "text-espresso/80",
                          )}
                        >
                          {stat.value}
                        </span>
                        <span>{stat.label}</span>
                      </div>
                    ))}
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <Button
                      onClick={() => handleTemplateSelect(selectedTemplate.id)}
                      variant="accent"
                      className="rounded-full px-5 py-3 text-sm font-semibold"
                    >
                      Open in workspace
                    </Button>
                    <Button
                      variant="outline"
                      className="rounded-full px-5 py-3 text-sm font-semibold"
                      onClick={() => handleRunTemplateLive(selectedTemplate.userPrompt)}
                    >
                      Run live
                    </Button>
                  </div>
                </div>
              )}

              <div className="flex-1 min-h-[320px] overflow-hidden">
                <div className="h-full overflow-y-auto pr-1">
                  {selectedTemplate ? (
                    <WorkflowVisualization
                      decisionSetId={selectedTemplate.id}
                      plan={selectedTemplate.planNodes}
                      graphType={selectedTemplate.graphType}
                      staticState={selectedTemplate.workflowState}
                      className="h-full"
                    />
                  ) : (
                    <div
                      className={cn(
                        "flex h-full items-center justify-center text-sm",
                        isDark ? "text-slate-400" : "text-espresso/60",
                      )}
                    >
                      Select a template to preview its workflow timeline.
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        </section>

        <section ref={chatSectionRef} className="space-y-8">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <h2
                className={cn(
                  "text-3xl font-bold",
                  isDark ? "text-slate-100" : "text-slate-900",
                )}
              >
                Design with the Agentic workspace
              </h2>
              <p className={cn("text-base leading-relaxed", isDark ? "text-slate-300" : "text-slate-700")}>
                Start a new conversation or revisit a template&apos;s reasoning flow.
              </p>
            </div>
            {mode !== "idle" && !activeTemplate && (
              <Button
                variant="ghost"
                className={cn(
                  isDark
                    ? "text-cyan-300 hover:text-cyan-200"
                    : "text-indigo-600",
                )}
                onClick={() => {
                  resetTemplateState();
                  setMode("idle");
                  scrollToChat();
                }}
              >
                View template gallery
              </Button>
            )}
          </div>

          {mode === "template" && activeTemplate ? (
            <TemplateShowcase
              template={activeTemplate}
              onDismiss={handleDismissTemplate}
              onRunLive={handleRunTemplateLive}
              theme={theme}
            />
          ) : (
            <div className={cn(theme.chat.wrapper, "transition-all duration-300 hover:shadow-super-elevated hover:-translate-y-2")}>
              <EnhancedChatInterface
                pendingPrompt={pendingPrompt}
                onPromptConsumed={handlePromptConsumed}
                theme={theme}
              />
            </div>
          )}
        </section>
      </div>
    </main>
  );
}
