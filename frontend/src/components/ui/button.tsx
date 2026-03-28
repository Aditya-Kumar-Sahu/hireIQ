"use client";

import type { ButtonHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
};

const variantClasses: Record<NonNullable<ButtonProps["variant"]>, string> = {
  primary:
    "bg-[color:var(--accent)] text-white hover:bg-[color:var(--accent-strong)] shadow-[0_12px_32px_rgba(193,92,47,0.28)]",
  secondary:
    "border border-[color:var(--line)] bg-white/75 text-[color:var(--foreground)] hover:border-[color:var(--accent)] hover:text-[color:var(--accent-strong)]",
  ghost: "text-[color:var(--muted)] hover:bg-white/65 hover:text-[color:var(--foreground)]",
  danger: "bg-[color:var(--danger)] text-white hover:opacity-90",
};

const sizeClasses: Record<NonNullable<ButtonProps["size"]>, string> = {
  sm: "h-10 px-4 text-sm",
  md: "h-11 px-5 text-sm",
  lg: "h-12 px-6 text-base",
};

export function Button({
  className,
  variant = "primary",
  size = "md",
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center rounded-full font-semibold transition focus:outline-none focus-visible:ring-2 focus-visible:ring-[color:var(--accent)] focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60",
        variantClasses[variant],
        sizeClasses[size],
        className,
      )}
      {...props}
    />
  );
}
