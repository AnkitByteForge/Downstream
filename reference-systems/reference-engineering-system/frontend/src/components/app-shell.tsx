"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
  LayoutDashboard,
  FolderKanban,
  FileQuestion,
  FileStack,
  FileDiff,
  Activity,
  ClipboardCheck,
  BookOpen,
  LogOut,
} from "lucide-react";

import { authApi, type SessionOut } from "@/lib/api-client";
import { cn } from "@/lib/utils";

interface AppShellProps {
  session: SessionOut | null;
  projectId?: number;
  children: React.ReactNode;
}

function NavLink({
  href,
  icon: Icon,
  label,
  active,
}: {
  href: string;
  icon: typeof LayoutDashboard;
  label: string;
  active: boolean;
}) {
  return (
    <Link
      href={href}
      className={cn(
        "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
        active
          ? "bg-slate-800 text-white"
          : "text-slate-300 hover:bg-slate-800/60 hover:text-white"
      )}
    >
      <Icon className="h-4 w-4 shrink-0" />
      {label}
    </Link>
  );
}

export function AppShell({ session, projectId, children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();

  async function handleLogout() {
    await authApi.logout();
    router.replace("/login");
  }

  return (
    <div className="flex min-h-screen flex-1">
      <aside className="flex w-60 shrink-0 flex-col bg-slate-900 text-slate-100">
        <div className="flex h-14 items-center gap-2 border-b border-slate-800 px-4">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-blue-600 text-sm font-bold">
            RE
          </div>
          <span className="text-sm font-semibold tracking-tight">Reference Engineering</span>
        </div>

        <nav className="flex flex-1 flex-col gap-1 p-3">
          <NavLink
            href="/dashboard"
            icon={LayoutDashboard}
            label="Dashboard"
            active={pathname === "/dashboard"}
          />
          <NavLink
            href="/projects"
            icon={FolderKanban}
            label="Projects"
            active={pathname === "/projects"}
          />
          {projectId != null && (
            <>
              <div className="mt-4 mb-1 px-3 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
                Current project
              </div>
              <NavLink
                href={`/projects/${projectId}/rfis`}
                icon={FileQuestion}
                label="RFIs"
                active={pathname.startsWith(`/projects/${projectId}/rfis`)}
              />
              <NavLink
                href={`/projects/${projectId}/drawings`}
                icon={FileStack}
                label="Drawings"
                active={pathname.startsWith(`/projects/${projectId}/drawings`)}
              />
              <NavLink
                href={`/projects/${projectId}/submittals`}
                icon={ClipboardCheck}
                label="Submittals"
                active={pathname.startsWith(`/projects/${projectId}/submittals`)}
              />
              <NavLink
                href={`/projects/${projectId}/design-changes`}
                icon={FileDiff}
                label="Design Changes"
                active={pathname.startsWith(`/projects/${projectId}/design-changes`)}
              />
              <NavLink
                href={`/projects/${projectId}/specifications`}
                icon={BookOpen}
                label="Specifications"
                active={pathname.startsWith(`/projects/${projectId}/specifications`)}
              />
              <NavLink
                href={`/projects/${projectId}/activity`}
                icon={Activity}
                label="Activity"
                active={pathname.startsWith(`/projects/${projectId}/activity`)}
              />
            </>
          )}
        </nav>

        <div className="border-t border-slate-800 p-3">
          {session && (
            <div className="mb-2 px-3 text-xs text-slate-400">
              <div className="font-medium text-slate-200">{session.role.replace(/_/g, " ")}</div>
              <div>Project #{session.project_id}</div>
            </div>
          )}
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm font-medium text-slate-300 transition-colors hover:bg-slate-800/60 hover:text-white"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 bg-muted/30">{children}</main>
    </div>
  );
}
