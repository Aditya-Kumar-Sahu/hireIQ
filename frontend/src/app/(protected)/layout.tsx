import { AppShell } from "@/components/app-shell";
import { QueryProvider } from "@/components/providers/query-provider";
import { SessionProvider } from "@/components/providers/session-provider";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <QueryProvider>
      <SessionProvider>
        <AppShell>{children}</AppShell>
      </SessionProvider>
    </QueryProvider>
  );
}
