// /home/toxic/projects/sovereign-projects/tau/engine/packages/ai/src/routing/nemotron-effort.ts
export const REASONING_MAP = {
  super: { none: "none", low: "low", medium: "low", high: "high", xhigh: "high", max: "high" },
  lightning: { none: "none", medium: "medium", high: "high", xhigh: "xhigh" },
} as const;

export function getEffort(modelId: string, requested: string): string {
  if (modelId.includes("super")) {
    if (requested === "xhigh") {
      console.warn("[sovereign] Super has no xhigh, clamping to high");
      return "high";
    }
    return REASONING_MAP.super[requested as keyof typeof REASONING_MAP.super] || "high";
  }
  return REASONING_MAP.lightning[requested as keyof typeof REASONING_MAP.lightning] || "high";
}
