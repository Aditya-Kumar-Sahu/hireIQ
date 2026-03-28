import type { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type BadgeVariant = "default" | "success" | "warning" | "danger";

const variantClasses: Record<BadgeVariant, string> = {
  default: "bg-white/75 text-[color:var(--muted)]",
  success: "bg-[rgba(15,118,110,0.12)] text-[color:var(--success)]",
  warning: "bg-[rgba(180,83,9,0.12)] text-[color:var(--warning)]",
  danger: "bg-[rgba(180,35,24,0.12)] text-[color:var(--danger)]",
};

const variantAriaLabels: Record<BadgeVariant, string> = {
  default: "",
  success: "Success: ",
  warning: "Warning: ",
  danger: "Error: ",
};

export function Badge({
  className,
  variant = "default",
  children,
  ...props
}: HTMLAttributes<HTMLSpanElement> & { variant?: BadgeVariant }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em]",
        variantClasses[variant],
        className,
      )}
      {...props}
    >
      {variantAriaLabels[variant] && (
        <span className="sr-only">{variantAriaLabels[variant]}</span>
      )}
      {children}
    </span>
  );
}
