"use client";

import { useDroppable } from "@dnd-kit/core";

import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import type { Application, ApplicationStatus } from "@/lib/types";
import { KanbanCard } from "@/components/jobs/kanban-card";

export function KanbanColumn({
  status,
  label,
  applications,
  isOver = false,
  movingApplicationId = null,
}: {
  status: ApplicationStatus;
  label: string;
  applications: Application[];
  isOver?: boolean;
  movingApplicationId?: string | null;
}) {
  const { setNodeRef } = useDroppable({
    id: status,
    data: { status },
  });

  return (
    <Card
      ref={setNodeRef}
      className={cn(
        "h-full transition",
        isOver && "border-[color:var(--accent)] bg-[rgba(255,244,235,0.92)]",
      )}
    >
      <div className="flex items-center justify-between gap-3">
        <div>
          <p className="text-lg font-semibold">{label}</p>
          <p className="text-sm text-[color:var(--muted)]">{applications.length} cards</p>
        </div>
        <Badge>{applications.length}</Badge>
      </div>

      <div className="mt-4 grid gap-3 min-h-[180px]">
        {applications.length === 0 ? (
          <div className="rounded-[1.2rem] border border-dashed border-[color:var(--line)] px-4 py-5 text-sm text-[color:var(--muted)]">
            Drop a candidate here.
          </div>
        ) : (
          applications.map((application) => (
            <KanbanCard
              key={application.id}
              application={application}
              dragging={movingApplicationId === application.id}
            />
          ))
        )}
      </div>
    </Card>
  );
}
