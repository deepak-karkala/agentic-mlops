"use client";

import { MlopsTemplate } from "@/data/mlops-templates";
import { LandingThemeConfig } from "@/data/landing-themes";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { ArrowRight } from "lucide-react";
import { cn } from "@/lib/utils";

interface TemplateCardProps {
  template: MlopsTemplate;
  onSelect: (templateId: string) => void;
  theme: LandingThemeConfig;
}

const MAX_VISIBLE_TAGS = 3;

export function TemplateCard({ template, onSelect, theme }: TemplateCardProps) {
  const highlightVariants = theme.templateCard.highlightVariants.length
    ? theme.templateCard.highlightVariants
    : ["border border-indigo-100 bg-indigo-50/70"];

  const visibleTags = template.tags.slice(0, MAX_VISIBLE_TAGS);
  const remainingTagCount = Math.max(template.tags.length - MAX_VISIBLE_TAGS, 0);

  return (
    <article
      className={cn(
        "group flex h-full flex-col justify-between rounded-[1.75rem] px-6 py-7 transition-all duration-300 hover:-translate-y-1",
        theme.templateCard.wrapper,
      )}
    >
      <div className="space-y-4">
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
        <div className="space-y-2">
          <h3 className={cn("text-[1.35rem] leading-7", theme.templateCard.title)}>
            {template.name}
          </h3>
          <p className={cn("text-[0.95rem] leading-relaxed", theme.templateCard.subtitle)}>
            {template.headline}
          </p>
        </div>
        <ul className={cn("space-y-2.5", theme.templateCard.highlightsWrapper)}>
          {template.highlights.map((highlight, index) => (
            <li
              key={highlight}
              className={cn(
                "flex items-start gap-3 rounded-2xl p-3 text-[0.9rem] leading-relaxed",
                highlightVariants[index % highlightVariants.length],
              )}
            >
              <span className="mt-1 inline-flex h-2 w-2 flex-shrink-0 rounded-full bg-espresso/30" />
              <span className={theme.templateCard.text}>{highlight}</span>
            </li>
          ))}
        </ul>
      </div>
      <div className="mt-6 space-y-4">
        <div className="flex flex-wrap gap-2">
          {template.techStack.slice(0, 4).map((tech) => (
            <Badge
              key={tech}
              variant="outline"
              className={cn(
                "text-[11px]",
                theme.templateCard.techBadge,
              )}
            >
              {tech}
            </Badge>
          ))}
        </div>
        <div className={cn("space-y-3", theme.templateCard.statsBar)}>
          <div className="grid grid-cols-2 gap-4 text-[11px] sm:grid-cols-3">
            {template.heroStats.map((stat) => (
              <div key={stat.label} className="space-y-0.5">
                <p className={cn("text-[0.95rem]", theme.templateCard.statsValue)}>
                  {stat.value}
                </p>
                <p className={theme.templateCard.statsLabel}>{stat.label}</p>
              </div>
            ))}
          </div>
          <Button
            size="sm"
            className={cn(
              "group/button w-full justify-center gap-2 rounded-full py-5 text-sm font-semibold",
              theme.templateCard.cta,
            )}
            onClick={() => onSelect(template.id)}
          >
            Preview workflow
            <ArrowRight className="h-4 w-4 transition-transform group-hover/button:translate-x-1" />
          </Button>
        </div>
      </div>
    </article>
  );
}
