"use client";

import { useEffect, useRef, useState } from "react";

import type { StreamEvent } from "@/lib/types";

export function useApplicationStatusStream(applicationId: string | undefined) {
  const [events, setEvents] = useState<StreamEvent[]>([]);
  const [streamStatus, setStreamStatus] = useState<
    "connecting" | "live" | "reconnecting" | "complete" | "failed"
  >("connecting");
  const terminalStreamEvent = useRef(false);

  useEffect(() => {
    if (!applicationId) {
      return;
    }

    setEvents([]);
    setStreamStatus("connecting");
    const source = new EventSource(`/api/applications/${applicationId}/status`);
    const eventNames = ["queued", "pipeline_started", "stage", "complete", "failed"];

    const handler = (incoming: Event) => {
      const message = incoming as MessageEvent<string>;
      try {
        const payload = JSON.parse(message.data) as StreamEvent;
        setEvents((current) => {
          if (
            current.some(
              (item) =>
                item.event === payload.event &&
                item.timestamp === payload.timestamp &&
                JSON.stringify(item.data) === JSON.stringify(payload.data),
            )
          ) {
            return current;
          }
          return [...current, payload];
        });
        if (payload.event === "complete" || payload.event === "failed") {
          terminalStreamEvent.current = true;
          setStreamStatus(payload.event);
          source.close();
        }
      } catch {
        // Ignore malformed events and keep the stream alive.
      }
    };

    source.onopen = () => {
      if (!terminalStreamEvent.current) {
        setStreamStatus("live");
      }
    };
    eventNames.forEach((name) => source.addEventListener(name, handler));
    source.onerror = () => {
      if (!terminalStreamEvent.current) {
        setStreamStatus("reconnecting");
      }
    };

    return () => {
      terminalStreamEvent.current = false;
      eventNames.forEach((name) => source.removeEventListener(name, handler));
      source.close();
    };
  }, [applicationId]);

  return { events, streamStatus };
}
