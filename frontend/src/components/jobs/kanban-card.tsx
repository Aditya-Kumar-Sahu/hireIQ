"use client";

import Link from "next/link";
import { useDraggable } from "@dnd-kit/core";
import { CSS } from "@dnd-kit/utilities";

import { Badge } from "@/components/ui/badge";
import { cn, formatDate } from "@/lib/utils";
import type { Application } from "@/lib/types";

export function KanbanCard({
  application,
  dragging = false,
}: {
  application: Application;
  dragging?: boolean;
}) {
  const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
    id: application.id,
    data: {
      applicationId: application.id,
      status: application.status,
    },
  });

  return (
    <div
      ref={setNodeRef}
      className={cn(
        "rounded-[1.2rem] border border-[color:var(--line)] bg-white/75 p-4 transition hover:border-[color:var(--accent)] focus:outline-none focus:ring-2 focus:ring-[color:var(--accent)]",
        (isDragging || dragging) && "opacity-70 shadow-[0_18px_40px_rgba(92,52,19,0.16)]",
      )}
      style={{
        transform: CSS.Translate.toString(transform),
      }}
      {...listeners}
      {...attributes}
    >
      <Link href={`/applications/${application.id}`} className="block focus:outline-none">
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="font-semibold">{application.candidate?.name ?? "Candidate"}</p>
            <p className="mt-1 text-sm text-[color:var(--muted)]">
              Score {application.score?.toFixed(2) ?? "Pending"}
            </p>
          </div>
          <Badge>{application.status}</Badge>
        </div>
        <p className="mt-2 text-xs uppercase tracking-[0.18em] text-[color:var(--muted-soft)]">
          {formatDate(application.updated_at)}
        </p>
      </Link>
    </div>
  );
}
