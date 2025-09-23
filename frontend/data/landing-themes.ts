export type LandingThemeId = "claude" | "pastel" | "midnight";

export interface LandingThemeConfig {
  id: LandingThemeId;
  label: string;
  pageBackground: string;
  hero: {
    base: string;
    badge: string;
    heading: string;
    description: string;
    primaryButton: string;
    secondaryButton: string;
    statsLabel: string;
    statsValue: string;
    cardWrapper: string;
    cardTitle: string;
    reasonList: string;
    reasonItemClasses: string[];
  };
  overlays: {
    left?: string;
    right?: string;
  };
  gallery: {
    badge: string;
    heading: string;
    description: string;
    actionButton: string;
  };
  templateCard: {
    wrapper: string;
    tag: string;
    title: string;
    subtitle: string;
    highlightsWrapper: string;
    highlightVariants: string[];
    techBadge: string;
    statsBar: string;
    statsLabel: string;
    statsValue: string;
    text: string;
    icon: string;
    cta: string;
  };
  chat: {
    wrapper: string;
    emptyState: string;
    userBubble: string;
    assistantBubble: string;
    loader: string;
  };
  templateShowcase: {
    infoCard: string;
    conversationCard: string;
    vizContainer: string;
    tag: string;
    stat: string;
    summaryText: string;
    documentCard: string;
  };
  switcher: {
    wrapper: string;
    active: string;
    inactive: string;
  };
}

export const LANDING_THEMES: Record<LandingThemeId, LandingThemeConfig> = {
  claude: {
    id: "claude",
    label: "Claude",
    pageBackground:
      "relative min-h-screen bg-sand bg-claude-fade-enhanced",
    hero: {
      base:
        "border border-espresso/10 bg-parchment/95 text-espresso shadow-elevated",
      badge:
        "inline-flex items-center gap-2 rounded-full border border-espresso/10 bg-accentOrangeLight px-4 py-1 text-[0.68rem] font-semibold tracking-[0.28em] uppercase text-espresso",
      heading:
        "font-display text-4xl leading-tight text-espresso sm:text-5xl lg:text-[3.4rem]",
      description:
        "max-w-xl text-[1.02rem] leading-7 text-espresso/80",
      primaryButton:
        "group bg-accentOrange text-white shadow-none transition-transform hover:-translate-y-0.5 hover:bg-[#d15c32]",
      secondaryButton:
        "border border-espresso/20 bg-transparent text-espresso transition hover:-translate-y-0.5 hover:bg-sandHover",
      statsLabel: "text-xs uppercase tracking-[0.28em] text-espresso/60",
      statsValue: "mt-1 text-lg font-semibold text-espresso",
      cardWrapper:
        "w-full max-w-sm rounded-[1.5rem] border border-espresso/10 bg-white/95 p-6 shadow-floating",
      cardTitle:
        "text-[0.7rem] font-semibold uppercase tracking-[0.35em] text-espresso/70",
      reasonList: "space-y-3 text-sm text-espresso/80",
      reasonItemClasses: [
        "rounded-2xl border border-espresso/8 bg-sand/80 px-4 py-3",
        "rounded-2xl border border-sage/50 bg-sage/30 px-4 py-3",
        "rounded-2xl border border-dustyRose/50 bg-dustyRose/25 px-4 py-3",
      ],
    },
    overlays: {
      left: "pointer-events-none absolute -left-12 top-16 h-72 w-72 rounded-full bg-[radial-gradient(circle,rgba(213,226,208,0.4)_0%,transparent_70%)] blur-3xl",
      right: "pointer-events-none absolute -bottom-10 right-4 h-80 w-80 rounded-full bg-[radial-gradient(circle,rgba(230,107,61,0.18)_0%,transparent_75%)] blur-[110px]",
    },
    gallery: {
      badge:
        "inline-flex items-center gap-2 rounded-full border border-espresso/20 bg-sand/60 px-4 py-1 text-[0.68rem] font-semibold uppercase tracking-[0.28em] text-espresso/70",
      heading:
        "font-display text-3xl font-semibold text-espresso",
      description:
        "mt-2 text-base leading-relaxed text-espresso/80",
      actionButton:
        "border border-espresso/20 bg-transparent text-espresso transition hover:border-espresso/40 hover:bg-sandHover",
    },
    templateCard: {
      wrapper:
        "border border-espresso/12 bg-white/95 text-espresso shadow-floating backdrop-blur-sm transition-all duration-300 hover:-translate-y-3 hover:border-espresso/20 hover:shadow-super-elevated",
      tag: "border border-espresso/20 bg-sand/70 text-espresso/80",
      title: "font-display text-xl text-espresso",
      subtitle: "text-[0.95rem] leading-relaxed text-espresso/70",
      highlightsWrapper: "text-espresso/80",
      highlightVariants: [
        "border border-espresso/15 bg-sand/70",
        "border border-sage/50 bg-sage/30",
        "border border-dustyRose/50 bg-dustyRose/25",
      ],
      techBadge: "border border-espresso/15 bg-white/70 text-espresso/70",
      statsBar:
        "rounded-xl border border-espresso/10 bg-sand/80 px-3 py-2 text-espresso/70",
      statsLabel: "text-[0.6rem] uppercase tracking-[0.32em] text-espresso/50",
      statsValue: "text-sm font-semibold text-espresso",
      text: "text-espresso/75",
      icon: "text-espresso/60",
      cta:
        "bg-accentOrange text-white transition hover:bg-[#d15c32]",
    },
    chat: {
      wrapper:
        "rounded-[2.25rem] border border-espresso/12 bg-white/95 shadow-elevated backdrop-blur-sm",
      emptyState:
        "space-y-2 rounded-2xl border border-espresso/10 bg-sand/80 px-4 py-5 text-espresso/70",
      userBubble:
        "bg-sand text-espresso shadow-sm",
      assistantBubble:
        "border border-espresso/10 bg-white text-espresso/85 shadow-none",
      loader: "border border-espresso/12 bg-sand/60 text-espresso/60",
    },
    templateShowcase: {
      infoCard:
        "border border-espresso/12 bg-white/90 text-espresso",
      conversationCard:
        "border border-espresso/10 bg-sand/85 text-espresso",
      vizContainer:
        "rounded-[2rem] border border-espresso/10 bg-white/96 shadow-claude-soft",
      tag: "rounded-full border border-espresso/20 bg-sand/70 px-2 py-1 text-[0.6rem] font-semibold uppercase tracking-[0.32em] text-espresso/70",
      stat: "text-xs text-espresso/60",
      summaryText: "text-sm leading-relaxed text-espresso/80",
      documentCard:
        "border border-espresso/12 bg-white/94 text-espresso",
    },
    switcher: {
      wrapper:
        "hidden border border-espresso/10 bg-white/40 text-espresso/70",
      active: "text-espresso",
      inactive: "text-espresso/60",
    },
  },
  pastel: {
    id: "pastel",
    label: "Pastel",
    pageBackground: "bg-gradient-to-br from-slate-600 via-slate-500 to-slate-400",
    hero: {
      base:
        "border border-white/95 bg-gradient-to-br from-white via-blue-50/95 to-pink-50/90 text-slate-900 shadow-[0_60px_160px_-10px_rgba(15,23,42,0.4)] shadow-indigo-500/30",
      badge:
        "inline-flex items-center gap-2 rounded-full border border-indigo-200/60 bg-indigo-50/80 px-3 py-1 text-xs uppercase tracking-wide text-indigo-600",
      heading:
        "bg-gradient-to-tr from-slate-900 via-indigo-900 to-sky-700 bg-clip-text text-3xl font-bold leading-tight text-transparent sm:text-4xl lg:text-5xl",
      description: "text-base text-slate-800 sm:text-lg leading-relaxed",
      primaryButton:
        "group bg-gradient-to-r from-indigo-600 via-indigo-500 to-violet-500 text-white shadow-xl shadow-indigo-500/40 hover:shadow-indigo-500/50 transition-all duration-200 font-semibold",
      secondaryButton:
        "border-2 border-indigo-200 bg-white/50 text-indigo-700 hover:border-indigo-300 hover:bg-white/80 backdrop-blur-sm transition-all duration-200 font-medium",
      statsLabel: "text-sm uppercase tracking-wide text-indigo-500",
      statsValue: "text-xl font-bold text-slate-900",
      cardWrapper:
        "w-full max-w-md rounded-2xl border border-white/90 bg-white/95 p-6 backdrop-blur-sm shadow-[0_50px_120px_-20px_rgba(99,102,241,0.45)] shadow-indigo-500/35",
      cardTitle: "text-xs font-bold uppercase tracking-[0.2em] text-indigo-600",
      reasonList: "space-y-3 text-sm text-slate-800 leading-relaxed",
      reasonItemClasses: [
        "rounded-xl border border-indigo-100 bg-indigo-50/80 p-3",
        "rounded-xl border border-rose-100 bg-rose-50/80 p-3",
        "rounded-xl border border-sky-100 bg-sky-50/80 p-3",
      ],
    },
    overlays: {
      left: "pointer-events-none absolute -left-10 top-10 h-64 w-64 rounded-full bg-[radial-gradient(circle,rgba(96,165,250,0.5)_0%,transparent_70%)] blur-xl",
      right: "pointer-events-none absolute bottom-0 right-0 h-72 w-72 translate-y-1/3 rounded-full bg-[radial-gradient(circle,rgba(244,114,182,0.45)_0%,transparent_70%)] blur-3xl",
    },
    gallery: {
      badge:
        "inline-flex items-center gap-2 rounded-full border border-indigo-200 bg-indigo-50 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-indigo-600",
      heading: "text-3xl font-bold text-slate-900",
      description: "text-base text-slate-700 leading-relaxed",
      actionButton:
        "border-indigo-200 bg-white/80 text-indigo-600 transition hover:border-indigo-300 hover:bg-white",
    },
    templateCard: {
      wrapper:
        "border border-white/90 bg-white/98 shadow-floating backdrop-blur-sm hover:border-indigo-100 hover:shadow-super-elevated hover:-translate-y-3 transition-all duration-300",
      tag: "border-indigo-200 bg-indigo-50/80 text-indigo-600",
      title: "font-bold text-slate-900",
      subtitle: "text-slate-700 leading-relaxed",
      highlightsWrapper: "text-slate-700",
      highlightVariants: [
        "border border-indigo-100 bg-indigo-50/80",
        "border border-rose-100 bg-rose-50/75",
        "border border-emerald-100 bg-emerald-50/75",
      ],
      techBadge: "border-indigo-100 bg-white text-indigo-600",
      statsBar: "rounded-lg border border-indigo-100/70 bg-indigo-50/60 px-3 py-2 text-slate-600",
      statsLabel: "text-[10px] uppercase tracking-wide text-slate-500",
      statsValue: "text-sm font-semibold text-slate-900",
      text: "text-slate-800",
      icon: "text-indigo-500",
      cta:
        "bg-gradient-to-r from-indigo-600 to-violet-600 text-white shadow-lg shadow-indigo-300/50 hover:shadow-xl hover:shadow-indigo-400/60 transition-all duration-200 font-semibold py-2.5",
    },
    chat: {
      wrapper:
        "rounded-3xl border border-white/90 bg-white/98 shadow-elevated backdrop-blur-sm",
      emptyState:
        "space-y-2 rounded-xl border border-indigo-100 bg-indigo-50/70 px-4 py-5 text-indigo-700 shadow-sm",
      userBubble:
        "bg-gradient-to-r from-indigo-500 to-violet-500 text-white shadow-lg",
      assistantBubble: "border border-indigo-50 bg-white text-slate-700 shadow-sm",
      loader: "border border-indigo-50 bg-white text-slate-500",
    },
    templateShowcase: {
      infoCard: "border-indigo-100 bg-white/90",
      conversationCard: "border-rose-100 bg-rose-50/60 text-slate-700",
      vizContainer:
        "rounded-3xl border border-indigo-100 bg-white/95 shadow-[0_30px_80px_-45px_rgba(129,140,248,0.65)]",
      tag: "rounded-full border border-dashed border-indigo-200 bg-indigo-50 px-2 py-1 text-[10px] font-semibold text-indigo-600",
      stat: "text-xs text-slate-500",
      summaryText: "text-sm text-slate-600",
      documentCard: "border-indigo-100 bg-white/95",
    },
    switcher: {
      wrapper: "border-2 border-white/60 bg-white/95 shadow-[0_16px_40px_-12px_rgba(15,23,42,0.3)] backdrop-blur-md",
      active: "bg-indigo-600/10 text-indigo-600 shadow-inner",
      inactive: "text-slate-500 hover:text-indigo-600",
    },
  },
  midnight: {
    id: "midnight",
    label: "Midnight",
    pageBackground: "bg-gradient-to-br from-slate-950 via-slate-950 to-black",
    hero: {
      base:
        "border border-slate-600/80 bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-slate-100 shadow-[0_60px_140px_-30px_rgba(2,132,199,0.7)] shadow-cyan-500/20",
      badge:
        "inline-flex items-center gap-2 rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs uppercase tracking-wide text-cyan-300",
      heading:
        "bg-gradient-to-tr from-white via-cyan-200 to-sky-400 bg-clip-text text-3xl font-semibold leading-tight text-transparent sm:text-4xl lg:text-5xl",
      description: "text-base text-slate-300 sm:text-lg",
      primaryButton:
        "group bg-gradient-to-r from-cyan-500 to-indigo-500 text-white shadow-lg shadow-cyan-900/40 transition hover:shadow-cyan-400/30",
      secondaryButton:
        "border border-slate-600/60 bg-transparent text-slate-300 hover:border-cyan-400/60 hover:bg-slate-800/40",
      statsLabel: "text-sm uppercase tracking-wide text-slate-400",
      statsValue: "text-xl font-semibold text-white",
      cardWrapper:
        "w-full max-w-md rounded-2xl border border-slate-600/80 bg-slate-800/90 p-6 backdrop-blur shadow-[0_50px_120px_-40px_rgba(2,132,199,0.75)] shadow-cyan-500/25",
      cardTitle: "text-xs font-semibold uppercase tracking-[0.22em] text-cyan-300",
      reasonList: "space-y-3 text-sm text-slate-200",
      reasonItemClasses: [
        "rounded-xl border border-cyan-500/30 bg-cyan-500/10 p-3",
        "rounded-xl border border-fuchsia-500/30 bg-fuchsia-500/10 p-3",
        "rounded-xl border border-emerald-500/30 bg-emerald-500/10 p-3",
      ],
    },
    overlays: {
      left: "pointer-events-none absolute -left-16 top-16 h-72 w-72 rounded-full bg-[radial-gradient(circle,rgba(14,165,233,0.25)_0%,transparent_70%)] blur-3xl",
      right: "pointer-events-none absolute bottom-0 right-0 h-96 w-96 translate-y-1/3 rounded-full bg-[radial-gradient(circle,rgba(139,92,246,0.3)_0%,transparent_70%)] blur-3xl",
    },
    gallery: {
      badge:
        "inline-flex items-center gap-2 rounded-full border border-cyan-500/40 bg-cyan-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-wide text-cyan-300",
      heading: "text-3xl font-semibold text-slate-100",
      description: "text-base text-slate-400",
      actionButton:
        "border-slate-700 bg-slate-900/40 text-slate-200 hover:border-slate-500 hover:bg-slate-800/40",
    },
    templateCard: {
      wrapper:
        "border border-slate-700/80 bg-slate-800/80 text-slate-200 shadow-floating backdrop-blur-sm hover:border-cyan-500/70 hover:shadow-super-elevated hover:-translate-y-3 transition-all duration-300",
      tag: "border-cyan-500/50 bg-cyan-500/15 text-cyan-200",
      title: "font-semibold text-white",
      subtitle: "text-slate-300",
      highlightsWrapper: "text-slate-200",
      highlightVariants: [
        "border border-cyan-500/40 bg-cyan-500/15",
        "border border-fuchsia-500/40 bg-fuchsia-500/15",
        "border border-emerald-500/40 bg-emerald-500/15",
      ],
      techBadge: "border-slate-700 bg-slate-800/70 text-slate-200",
      statsBar:
        "rounded-lg border border-slate-800 bg-slate-900/60 px-3 py-2 text-slate-300",
      statsLabel: "text-[10px] uppercase tracking-wide text-slate-400",
      statsValue: "text-sm font-semibold text-slate-100",
      text: "text-slate-200",
      icon: "text-cyan-300",
      cta:
        "bg-gradient-to-r from-cyan-500 to-indigo-500 text-white shadow-cyan-900/40 hover:shadow-cyan-400/30",
    },
    chat: {
      wrapper:
        "rounded-3xl border border-slate-700/80 bg-slate-800/90 shadow-elevated backdrop-blur-sm",
      emptyState:
        "space-y-2 rounded-xl border border-slate-700 bg-slate-900/70 px-4 py-5 text-slate-200 shadow-sm",
      userBubble:
        "bg-gradient-to-r from-cyan-500 to-indigo-500 text-white shadow-lg shadow-cyan-900/40",
      assistantBubble:
        "border border-slate-700 bg-slate-900/70 text-slate-200 shadow-sm",
      loader: "border border-slate-700 bg-slate-900/70 text-slate-300",
    },
    templateShowcase: {
      infoCard: "border-slate-700 bg-slate-900/60 text-slate-200",
      conversationCard: "border-slate-700 bg-slate-900/60 text-slate-200",
      vizContainer:
        "rounded-3xl border border-slate-800 bg-slate-950/60 shadow-[0_40px_100px_-50px_rgba(12,74,110,0.65)]",
      tag: "rounded-full border border-cyan-500/40 bg-cyan-500/10 px-2 py-1 text-[10px] font-semibold text-cyan-200",
      stat: "text-xs text-slate-400",
      summaryText: "text-sm text-slate-300",
      documentCard: "border-slate-700 bg-slate-900/60 text-slate-200",
    },
    switcher: {
      wrapper: "border border-slate-700/70 bg-slate-900/70 shadow-[0_12px_30px_-18px_rgba(8,47,73,0.8)] backdrop-blur",
      active: "bg-cyan-500/10 text-cyan-200 shadow-inner",
      inactive: "text-slate-300 hover:text-cyan-200",
    },
  },
};

export const LANDING_THEME_OPTIONS = Object.values(LANDING_THEMES);
