import { AppShell } from "@/components/app-shell";
import { SessionProvider } from "@/components/providers/session-provider";

export default function ProtectedLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <SessionProvider>
      <AppShell>{children}</AppShell>
    </SessionProvider>
  );
}
