"use client";

import { MlopsTemplate } from "@/data/mlops-templates";
import { LandingThemeConfig } from "@/data/landing-themes";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight, ChevronRight, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

interface TemplateCardProps {
  template: MlopsTemplate;
  onSelect: (templateId: string) => void;
  theme: LandingThemeConfig;
  variant?: "default" | "compact";
  isSelected?: boolean;
}

const MAX_VISIBLE_TAGS = 3;

export function TemplateCard({
  template,
  onSelect,
  theme,
  variant = "default",
  isSelected = false,
}: TemplateCardProps) {
  const highlightVariants = theme.templateCard.highlightVariants.length
    ? theme.templateCard.highlightVariants
    : ["border border-indigo-100 bg-indigo-50/70"];

  const visibleTags = template.tags.slice(0, MAX_VISIBLE_TAGS);
  const remainingTagCount = Math.max(template.tags.length - MAX_VISIBLE_TAGS, 0);
  const isMidnight = theme.id === "midnight";

  const handleSelect = () => {
    onSelect(template.id);
  };

  if (variant === "compact") {
    return (
      <button
        type="button"
        onClick={handleSelect}
        role="tab"
        aria-selected={isSelected}
        className={cn(
          "group w-full rounded-2xl border px-5 py-4 text-left transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2",
          isSelected
            ? isMidnight
              ? "border-cyan-300/70 bg-slate-900/80 text-slate-100 shadow-[0_0_0_1px_rgba(125,211,252,0.35)] focus-visible:ring-cyan-300/50 focus-visible:ring-offset-slate-950"
              : "border-espresso/40 bg-white shadow-super-elevated focus-visible:ring-espresso/30 focus-visible:ring-offset-white"
            : isMidnight
            ? "border-slate-700/60 bg-slate-900/70 text-slate-200 hover:-translate-y-0.5 hover:border-slate-500 focus-visible:ring-slate-400/40 focus-visible:ring-offset-slate-950"
            : "border-espresso/10 bg-white/85 text-espresso/80 shadow-sm hover:-translate-y-0.5 hover:border-espresso/30 focus-visible:ring-espresso/20 focus-visible:ring-offset-white",
        )}
      >
        <div className="flex items-start justify-between gap-3">
          <h3
            className={cn(
              "text-base font-semibold leading-snug",
              theme.templateCard.title,
              isMidnight ? "text-slate-100" : "text-espresso",
            )}
          >
            {template.name}
          </h3>
          {isSelected ? (
            <Sparkles
              className={cn(
                "mt-1 h-4 w-4 flex-shrink-0",
                isMidnight ? "text-cyan-200" : "text-espresso/70",
              )}
            />
          ) : (
            <ChevronRight
              className={cn(
                "mt-1 h-4 w-4 flex-shrink-0 transition-colors",
                isMidnight
                  ? "text-slate-500 group-hover:text-slate-200"
                  : "text-espresso/40 group-hover:text-espresso/70",
              )}
            />
          )}
        </div>

        <p
          className={cn(
            "mt-2 text-[0.82rem] leading-relaxed",
            theme.templateCard.subtitle,
            isMidnight ? "text-slate-300/90" : "text-espresso/70",
          )}
        >
          {template.headline}
        </p>
      </button>
    );
  }

  return (
    <article
      className={cn(
        "group flex h-full flex-col justify-between rounded-[1.75rem] px-4 py-4 transition-all duration-300 hover:-translate-y-1",
        theme.templateCard.wrapper,
      )}
    >
      <div className="space-y-3">
        <div className="flex flex-wrap items-center gap-1.5 text-[11px] uppercase tracking-[0.28em] text-espresso/50">
          {visibleTags.map((tag) => (
            <span
              key={tag}
              className={cn(
                "rounded-full border px-2 py-0.5 text-[10px] font-semibold",
                theme.templateCard.tag,
              )}
            >
              {tag}
            </span>
          ))}
          {remainingTagCount > 0 && (
            <span className="rounded-full border border-espresso/15 px-2 py-0.5 text-[10px] font-semibold text-espresso/50">
              +{remainingTagCount}
            </span>
          )}
        </div>
        <div className="space-y-1.5">
          <h3 className={cn("text-[1.2rem] leading-6", theme.templateCard.title)}>
            {template.name}
          </h3>
          <p className={cn("text-[0.88rem] leading-snug", theme.templateCard.subtitle)}>
            {template.headline}
          </p>
        </div>
        <ul className={cn("space-y-1", theme.templateCard.highlightsWrapper)}>
          {template.highlights.slice(0, 3).map((highlight, index) => (
            <li
              key={highlight}
              className={cn(
                "flex items-start gap-2 rounded-lg p-2 text-[0.82rem] leading-snug",
                highlightVariants[index % highlightVariants.length],
              )}
            >
              <span className="mt-0.5 inline-flex h-1.5 w-1.5 flex-shrink-0 rounded-full bg-espresso/30" />
              <span className={theme.templateCard.text}>{highlight}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-4 space-y-3">
        <div className="flex flex-wrap gap-2">
          {template.techStack.slice(0, 4).map((tech) => (
            <Badge
              key={tech}
              variant="outline"
              className={cn(
                "text-[10px] px-1.5 py-0.5",
                theme.templateCard.techBadge,
              )}
            >
              {tech}
            </Badge>
          ))}
        </div>
        <div className={cn("space-y-2", theme.templateCard.statsBar)}>
          <div className="grid grid-cols-3 gap-3 text-[10px]">
            {template.heroStats.map((stat) => (
              <div key={stat.label} className="space-y-0.5">
                <p className={cn("text-[0.85rem]", theme.templateCard.statsValue)}>
                  {stat.value}
                </p>
                <p className={theme.templateCard.statsLabel}>{stat.label}</p>
              </div>
            ))}
          </div>
          <Button
            size="sm"
            className={cn(
              "group/button w-full justify-center gap-1.5 rounded-full py-3 text-sm font-semibold",
              theme.templateCard.cta,
            )}
            onClick={handleSelect}
          >
            Preview workflow
            <ArrowRight className="h-4 w-4 transition-transform group-hover/button:translate-x-1" />
          </Button>
        </div>
      </div>
    </article>
  );
}
