"use client";

import { Button } from "@/components/ui/button";
import { LandingThemeConfig } from "@/data/landing-themes";
import { cn } from "@/lib/utils";
import { ArrowRight, CheckCircle, Sparkles } from "lucide-react";

interface HeroSectionProps {
  onExploreTemplates: () => void;
  onStartCustom: () => void;
  theme: LandingThemeConfig;
}

export function HeroSection({ onExploreTemplates, onStartCustom, theme }: HeroSectionProps) {
  const { hero, overlays } = theme;

  const benefits = [
    "Multi-agent workflows with deterministic orchestration",
    "Production-ready infrastructure code generation",
    "Real-time collaboration between human experts and AI",
    "Automated compliance and governance controls"
  ];

  return (
    <section
      className={cn(
        "relative overflow-hidden rounded-[2.5rem] px-6 py-10 sm:px-10 md:px-16 md:py-12 backdrop-blur-sm transition-all duration-300 hover:shadow-super-elevated hover:-translate-y-2",
        hero.base,
      )}
    >
      <div className="absolute inset-0">
        {overlays.left && <div className={overlays.left} />}
        {overlays.right && <div className={overlays.right} />}
      </div>
      <div className="relative mx-auto max-w-4xl text-center">
        <div className="space-y-8">
          <div className={hero.badge}>
            <Sparkles className="h-4 w-4" />
            Agentic MLOps Workspace
          </div>
          <div className="space-y-6">
            <h1 className={hero.heading}>
              Ship production-grade MLOps blueprints with conversations that feel human.
            </h1>
            <p className={cn(hero.description, "mx-auto max-w-3xl")}>
              Design, critique, and deploy resilient ML systems in a calm workspace built for collaborative agents. Claude powers code generation, LangGraph keeps orchestration deterministic, and App Runner ships everything to production.
            </p>
          </div>
          <div className="flex flex-wrap justify-center gap-3">
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
          <div className="mt-12">
            <h3 className={cn("mb-6 text-lg font-semibold", hero.heading.includes("text-espresso") ? "text-espresso" : "")}>
              Why teams choose Agentic MLOps
            </h3>
            <div className="grid gap-4 md:grid-cols-2">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-start gap-3 text-left">
                  <CheckCircle className="mt-0.5 h-5 w-5 flex-shrink-0 text-accentOrange" />
                  <span className={cn("text-sm leading-relaxed", hero.description)}>
                    {benefit}
                  </span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
