"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store";
import {
  LayoutDashboard,
  FolderKanban,
  Users,
  FileText,
  GitBranch,
  Variable,
  BarChart3,
  Clock,
  Settings,
  LogOut,
  PlayCircle,
  MessageCircle,
  Send,
} from "lucide-react";

const navigation = [
  { name: "Dashboard", href: "/admin", icon: LayoutDashboard },
  { name: "Projects", href: "/admin/projects", icon: FolderKanban },
  { name: "Scheduler", href: "/admin/scheduler", icon: Clock },
];

const projectNavigation = [
  {
    name: "Participants",
    href: "/admin/projects/[id]/participants",
    icon: Users,
  },
  { name: "Templates", href: "/admin/projects/[id]/templates", icon: FileText },
  { name: "Nodes", href: "/admin/projects/[id]/nodes", icon: GitBranch },
  { name: "Variables", href: "/admin/projects/[id]/variables", icon: Variable },
  {
    name: "Analytics",
    href: "/admin/projects/[id]/analytics",
    icon: BarChart3,
  },
  {
    name: "Delivery",
    href: "/admin/projects/[id]/delivery",
    icon: Send,
  },
  {
    name: "Test Protocol",
    href: "/admin/projects/[id]/test-protocol",
    icon: PlayCircle,
  },
  {
    name: "Simulator",
    href: "/admin/projects/[id]/simulator",
    icon: MessageCircle,
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuthStore();

  // Extract project ID from pathname if viewing project details
  const projectMatch = pathname.match(/\/admin\/projects\/(\d+)/);
  const currentProjectId = projectMatch ? projectMatch[1] : null;

  const handleLogout = async () => {
    await logout();
  };

  return (
    <aside className="fixed inset-y-0 left-0 w-64 bg-surface border-r border-border flex flex-col">
      {/* Logo */}
      <div className="h-16 flex items-center px-6 border-b border-border">
        <Link href="/admin" className="flex items-center gap-2">
          <span className="text-title text-text font-serif">Cadence</span>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-1 overflow-y-auto scrollbar-thin">
        {navigation.map((item) => {
          const Icon = item.icon;
          const isActive =
            item.href === "/admin"
              ? pathname === "/admin"
              : pathname.startsWith(item.href);

          return (
            <Link
              key={item.name}
              href={item.href}
              className={cn(isActive ? "nav-item-active" : "nav-item")}
            >
              <Icon className="h-5 w-5" />
              {item.name}
            </Link>
          );
        })}

        {/* Project-specific navigation */}
        {currentProjectId && (
          <>
            <div className="pt-4 pb-2">
              <span className="px-3 text-caption font-medium text-text-muted uppercase tracking-wider">
                Current Project
              </span>
            </div>
            {projectNavigation.map((item) => {
              const Icon = item.icon;
              const href = item.href.replace("[id]", currentProjectId);
              const isActive =
                pathname === href || pathname.startsWith(href + "/");

              return (
                <Link
                  key={item.name}
                  href={href}
                  className={cn(isActive ? "nav-item-active" : "nav-item")}
                >
                  <Icon className="h-5 w-5" />
                  {item.name}
                </Link>
              );
            })}
          </>
        )}
      </nav>

      {/* User section */}
      <div className="p-4 border-t border-border">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-9 w-9 rounded-full bg-background flex items-center justify-center">
            <span className="text-body-sm font-medium text-text-secondary">
              {user?.full_name
                ? user.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()
                : user?.email?.[0]?.toUpperCase()}
            </span>
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-body-sm font-medium text-text truncate">
              {user?.full_name || user?.email}
            </p>
            <p className="text-caption text-text-muted truncate">
              {user?.role}
            </p>
          </div>
        </div>

        <div className="flex gap-2">
          <Link
            href="/admin/settings"
            className="btn-ghost flex-1 text-text-secondary"
          >
            <Settings className="h-4 w-4" />
            Settings
          </Link>
          <button
            onClick={handleLogout}
            className="btn-ghost text-text-secondary"
          >
            <LogOut className="h-4 w-4" />
          </button>
        </div>
      </div>
    </aside>
  );
}
