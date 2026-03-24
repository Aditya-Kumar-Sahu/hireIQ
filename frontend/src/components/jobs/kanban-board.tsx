"use client";

import { DndContext, DragOverlay, KeyboardSensor, PointerSensor, closestCorners, useSensor, useSensors, type DragEndEvent, type DragOverEvent, type UniqueIdentifier } from "@dnd-kit/core";
import { sortableKeyboardCoordinates } from "@dnd-kit/sortable";
import { useMemo, useState } from "react";

import { KanbanCard } from "@/components/jobs/kanban-card";
import { KanbanColumn } from "@/components/jobs/kanban-column";
import type { Application, ApplicationStatus } from "@/lib/types";

type KanbanColumnConfig = {
  status: ApplicationStatus;
  label: string;
};

export function KanbanBoard({
  columns,
  applications,
  movingApplicationId = null,
  onMoveApplication,
}: {
  columns: KanbanColumnConfig[];
  applications: Application[];
  movingApplicationId?: string | null;
  onMoveApplication: (applicationId: string, nextStatus: ApplicationStatus) => void;
}) {
  const [activeId, setActiveId] = useState<UniqueIdentifier | null>(null);
  const [overStatus, setOverStatus] = useState<ApplicationStatus | null>(null);
  const sensors = useSensors(
    useSensor(PointerSensor, { activationConstraint: { distance: 6 } }),
    useSensor(KeyboardSensor, { coordinateGetter: sortableKeyboardCoordinates }),
  );

  const applicationMap = useMemo(
    () => new Map(applications.map((application) => [application.id, application])),
    [applications],
  );
  const activeApplication =
    activeId && typeof activeId === "string" ? applicationMap.get(activeId) ?? null : null;

  function handleDragOver(event: DragOverEvent) {
    const status = typeof event.over?.id === "string" ? (event.over.id as ApplicationStatus) : null;
    setOverStatus(status);
  }

  function handleDragEnd(event: DragEndEvent) {
    setActiveId(null);
    const applicationId =
      typeof event.active.id === "string" ? event.active.id : null;
    const nextStatus =
      typeof event.over?.id === "string" ? (event.over.id as ApplicationStatus) : null;

    setOverStatus(null);
    if (!applicationId || !nextStatus) {
      return;
    }

    const currentStatus = applicationMap.get(applicationId)?.status;
    if (!currentStatus || currentStatus === nextStatus) {
      return;
    }
    onMoveApplication(applicationId, nextStatus);
  }

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCorners}
      onDragStart={(event) => setActiveId(event.active.id)}
      onDragOver={handleDragOver}
      onDragCancel={() => {
        setActiveId(null);
        setOverStatus(null);
      }}
      onDragEnd={handleDragEnd}
    >
      <div className="grid gap-4 xl:grid-cols-4">
        {columns.map((column) => (
          <KanbanColumn
            key={column.status}
            status={column.status}
            label={column.label}
            applications={applications.filter((application) => application.status === column.status)}
            isOver={overStatus === column.status}
            movingApplicationId={movingApplicationId}
          />
        ))}
      </div>

      <DragOverlay>
        {activeApplication ? <KanbanCard application={activeApplication} dragging /> : null}
      </DragOverlay>
    </DndContext>
  );
}
