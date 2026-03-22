import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "Not scheduled";
  }

  return new Intl.DateTimeFormat("en-US", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(value));
}

export function titleCase(value: string) {
  return value
    .split(/[_-\s]+/)
    .filter(Boolean)
    .map((chunk) => chunk[0].toUpperCase() + chunk.slice(1))
    .join(" ");
}
