"use client";

import { Button } from "@/components/ui/button";
import { LandingThemeConfig } from "@/data/landing-themes";
import { cn } from "@/lib/utils";
import { ArrowRight, FolderKanban, Sparkles, SquareTerminal } from "lucide-react";

interface HeroSectionProps {
  onExploreTemplates: () => void;
  onStartCustom: () => void;
  theme: LandingThemeConfig;
}

export function HeroSection({ onExploreTemplates, onStartCustom, theme }: HeroSectionProps) {
  const { hero, overlays } = theme;
  const reasonClasses = hero.reasonItemClasses.length
    ? hero.reasonItemClasses
    : ["rounded-xl border border-sand bg-sand/70 px-4 py-3"];

  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-[2.5rem] px-6 py-14 sm:px-10 md:px-16 md:py-16",
        hero.base,
      )}
    >
      <div className="absolute inset-0">
        {overlays.left && <div className={overlays.left} />}
        {overlays.right && <div className={overlays.right} />}
      </div>
      <div className="relative grid gap-14 lg:grid-cols-[minmax(0,1fr)_minmax(320px,360px)] lg:items-start">
        <div className="max-w-2xl space-y-8">
          <div className={hero.badge}>
            <Sparkles className="h-4 w-4" />
            Agentic MLOps Workspace
          </div>
          <div className="space-y-4">
            <h1 className={hero.heading}>
              Ship production-grade MLOps blueprints with conversations that feel human.
            </h1>
            <p className={hero.description}>
              Design, critique, and deploy resilient ML systems in a calm workspace built for collaborative agents. Claude powers code generation, LangGraph keeps orchestration deterministic, and App Runner ships everything to production.
            </p>
          </div>
          <div className="flex flex-wrap gap-3">
            <Button size="lg" className={cn(hero.primaryButton, "rounded-full px-6 py-5 text-sm font-semibold")}
              onClick={onStartCustom}
            >
              Start a custom design
              <ArrowRight className="ml-2 h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Button>
            <Button
              size="lg"
              variant="outline"
              className={cn(hero.secondaryButton, "rounded-full px-6 py-5 text-sm font-semibold")}
              onClick={onExploreTemplates}
            >
              Explore blueprints
            </Button>
          </div>
          <dl className="grid gap-8 text-sm sm:grid-cols-2">
            <div>
              <dt className={hero.statsLabel}>Agent workflows orchestrated</dt>
              <dd className={hero.statsValue}>50+ production-ready graphs</dd>
            </div>
            <div>
              <dt className={hero.statsLabel}>Deployment options</dt>
              <dd className={hero.statsValue}>AWS App Runner &amp; beyond</dd>
            </div>
          </dl>
        </div>
        <div className="relative flex flex-col gap-6 lg:pl-8">
          <div className="hidden h-full w-px flex-shrink-0 bg-espresso/10 lg:block" aria-hidden />
          <div className={cn(hero.cardWrapper, "relative overflow-hidden")}
            data-testid="hero-template-card"
          >
            <div className="space-y-5">
              <div className="flex items-center gap-3">
                <FolderKanban className="h-4 w-4 text-espresso/70" />
                <span className="text-xs uppercase tracking-[0.32em] text-espresso/50">Featured template</span>
              </div>
              <div className="space-y-3">
                <h3 className="font-display text-2xl text-espresso">Enterprise RAG Advisor</h3>
                <p className="text-sm leading-relaxed text-espresso/70">
                  LangGraph-managed retrieval pipelines with bias guards, live audit trail, and Claude Code generated dashboards.
                </p>
              </div>
              <div className="flex items-center justify-between text-xs text-espresso/60">
                <span>Confidence 0.70</span>
                <span>10k+ docs</span>
                <span>&lt;4s response</span>
              </div>
            </div>
          </div>
          <div className="rounded-[1.5rem] border border-espresso/12 bg-sand/90 p-6 shadow-sm" data-testid="hero-progress-card">
            <div className="mb-3 flex items-center gap-3 text-sm font-semibold text-espresso">
              <SquareTerminal className="h-4 w-4 text-espresso/60" />
              <span>Agent workflow in progress</span>
            </div>
            <ul className="space-y-3 text-sm text-espresso/75">
              {["Gather product context", "Draft MLOps blueprint", "Generate infra-as-code", "Review compliance gates"].map((stage, index) => (
                <li
                  key={stage}
                  className={cn(
                    "flex items-start gap-3 rounded-2xl border border-espresso/10 bg-white/70 px-4 py-3",
                    reasonClasses[index % reasonClasses.length],
                  )}
                >
                  <span className="mt-[2px] inline-flex h-2 w-2 flex-shrink-0 rounded-full bg-espresso/30" />
                  <span className="leading-snug">{stage}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
