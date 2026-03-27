import { cn } from "@/lib/utils";

interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className }: SkeletonProps) {
  return (
    <div
      className={cn(
        "animate-pulse rounded-2xl bg-[color:var(--line)]",
        className
      )}
    />
  );
}

export function CardSkeleton({ className }: SkeletonProps) {
  return (
    <div className={cn("rounded-[1.75rem] border border-[color:var(--line)] bg-white/75 p-6", className)}>
      <Skeleton className="h-3 w-20 rounded-full" />
      <Skeleton className="mt-4 h-8 w-3/4 rounded-xl" />
      <Skeleton className="mt-4 h-4 w-full rounded-lg" />
      <Skeleton className="mt-2 h-4 w-2/3 rounded-lg" />
    </div>
  );
}

export function StatCardSkeleton() {
  return (
    <div className="rounded-[1.75rem] border border-[color:var(--line)] bg-white/75 p-6">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <Skeleton className="h-3 w-16 rounded-full" />
          <Skeleton className="mt-4 h-10 w-20 rounded-xl" />
          <Skeleton className="mt-3 h-4 w-full rounded-lg" />
        </div>
        <Skeleton className="h-11 w-11 rounded-2xl" />
      </div>
    </div>
  );
}

export function ListItemSkeleton() {
  return (
    <div className="rounded-[1.25rem] border border-[color:var(--line)] bg-white/75 p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1">
          <Skeleton className="h-5 w-40 rounded-lg" />
          <Skeleton className="mt-2 h-4 w-24 rounded-lg" />
        </div>
        <Skeleton className="h-6 w-16 rounded-full" />
      </div>
    </div>
  );
}
