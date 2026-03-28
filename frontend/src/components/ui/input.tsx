import type { InputHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "h-12 w-full rounded-2xl border border-[color:var(--line)] bg-white/80 px-4 text-sm outline-none transition placeholder:text-[color:var(--muted-soft)] focus:border-[color:var(--accent)] focus:ring-2 focus:ring-[rgba(193,92,47,0.16)] disabled:cursor-not-allowed disabled:opacity-60 file:mr-4 file:rounded-full file:border-0 file:bg-[color:var(--accent)] file:px-4 file:py-2 file:text-sm file:font-semibold file:text-white",
        className,
      )}
      {...props}
    />
  );
}
