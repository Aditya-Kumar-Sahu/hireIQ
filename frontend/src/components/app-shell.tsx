"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import {
  BriefcaseBusiness,
  Gauge,
  LogOut,
  Menu,
  ScanSearch,
  Settings,
  Sparkles,
  X,
} from "lucide-react";

import { useSession } from "@/components/providers/session-provider";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const navigation = [
  { href: "/dashboard", label: "Dashboard", icon: Gauge },
  { href: "/jobs", label: "Jobs", icon: BriefcaseBusiness },
  { href: "/candidates", label: "Candidates", icon: ScanSearch },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { loading, logout, user } = useSession();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => {
    if (!loading && !user) {
      router.replace("/login");
    }
  }, [loading, router, user]);

  useEffect(() => {
    setSidebarOpen(false);
  }, [pathname]);

  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="glass-panel rounded-[1.8rem] px-8 py-6 text-center">
          <p className="eyebrow">HireIQ</p>
          <p className="mt-2 text-lg font-semibold">Loading recruiter workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen px-4 py-4 md:px-6 md:py-6">
      {/* Mobile header */}
      <div className="mb-4 flex items-center justify-between md:hidden">
        <div className="flex items-center gap-2">
          <Sparkles className="h-5 w-5 text-[color:var(--accent)]" />
          <span className="text-lg font-semibold">HireIQ</span>
        </div>
        <button
          type="button"
          onClick={() => setSidebarOpen(!sidebarOpen)}
          className="rounded-xl border border-[color:var(--line)] bg-white/80 p-2 text-[color:var(--muted)] transition hover:bg-white hover:text-[color:var(--foreground)]"
          aria-label={sidebarOpen ? "Close menu" : "Open menu"}
        >
          {sidebarOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
        </button>
      </div>

      {/* Mobile sidebar overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/20 backdrop-blur-sm md:hidden"
          onClick={() => setSidebarOpen(false)}
          aria-hidden="true"
        />
      )}

      <div className="mx-auto grid min-h-[calc(100vh-2rem)] max-w-7xl gap-4 md:grid-cols-[280px_minmax(0,1fr)]">
        <aside className={cn(
          "glass-panel rounded-[2rem] p-5",
          "fixed inset-y-4 left-4 right-4 z-50 md:static md:inset-auto",
          "transition-transform duration-300 ease-in-out",
          sidebarOpen ? "translate-x-0" : "-translate-x-[calc(100%+2rem)] md:translate-x-0"
        )}>
          <div className="rounded-[1.65rem] bg-[linear-gradient(160deg,#fff6ee_0%,#ffe8d2_100%)] p-5">
            <div className="flex items-center gap-3">
              <div className="rounded-2xl bg-white/80 p-3 text-[color:var(--accent)]">
                <Sparkles className="h-5 w-5" />
              </div>
              <div>
                <p className="eyebrow">Recruiter Workspace</p>
                <h1 className="text-2xl font-semibold">HireIQ</h1>
              </div>
            </div>
            <p className="mt-4 text-sm leading-6 text-[color:var(--muted)]">
              Semantic screening, agent orchestration, and live status in one workspace.
            </p>
          </div>

          <nav className="mt-6 grid gap-2">
            {navigation.map((item) => {
              const Icon = item.icon;
              const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition",
                    active
                      ? "bg-white text-[color:var(--accent-strong)] shadow-[0_18px_44px_rgba(92,52,19,0.1)]"
                      : "text-[color:var(--muted)] hover:bg-white/70 hover:text-[color:var(--foreground)]",
                  )}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>

          <div className="mt-6 rounded-[1.4rem] border border-[color:var(--line)] bg-white/70 p-4">
            <p className="eyebrow">Signed in as</p>
            <p className="mt-2 text-sm font-semibold">{user.email}</p>
            <p className="mt-1 text-sm text-[color:var(--muted)]">{user.role}</p>
            <Button
              className="mt-4 w-full"
              type="button"
              variant="secondary"
              onClick={() => {
                logout();
                router.replace("/login");
              }}
            >
              <LogOut className="mr-2 h-4 w-4" />
              Log out
            </Button>
          </div>
        </aside>

        <div className="glass-panel rounded-[2rem] p-5 md:p-7">{children}</div>
      </div>
    </div>
  );
}
