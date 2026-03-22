import type { TextareaHTMLAttributes } from "react";

import { cn } from "@/lib/utils";

export function Textarea({
  className,
  ...props
}: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cn(
        "min-h-[140px] w-full rounded-[1.4rem] border border-[color:var(--line)] bg-white/80 px-4 py-3 text-sm outline-none transition placeholder:text-[color:var(--muted-soft)] focus:border-[color:var(--accent)] focus:ring-2 focus:ring-[rgba(193,92,47,0.16)]",
        className,
      )}
      {...props}
    />
  );
}
