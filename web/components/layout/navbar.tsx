"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { Activity } from "lucide-react";

const navLinks = [
  { name: "About", href: "/#about" },
  { name: "Capabilities", href: "/#features" },
  { name: "Architecture", href: "/#architecture" },
];

export function Navbar() {
  return (
    <nav className="sticky top-0 z-50 border-b border-border bg-background/80 backdrop-blur-sm">
      <div className="mx-auto max-w-6xl flex items-center justify-between h-14 px-6">
        {/* Logo */}
        <Link href="/" className="flex items-center gap-2.5">
          <div className="relative flex items-center justify-center w-7 h-7 rounded-md bg-accent text-white">
            <Activity className="h-3.5 w-3.5" />
            <span className="absolute -top-0.5 -right-0.5 w-1.5 h-1.5 rounded-full bg-accent animate-pulse" />
          </div>
          <span className="text-body font-serif font-semibold text-text">
            Cadence
          </span>
          <span className="text-caption font-mono text-text-muted ml-1">
            v1.0
          </span>
        </Link>

        {/* Nav links */}
        <div className="flex items-center gap-6">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              className="text-body-sm text-text-muted hover:text-text transition-colors"
            >
              {link.name}
            </a>
          ))}

          <div className="w-px h-4 bg-border" />

          <Link
            href="/login"
            className={cn(
              "inline-flex items-center px-3.5 py-1.5 rounded-md text-body-sm font-medium transition-all",
              "bg-accent text-white hover:bg-accent-hover",
              "focus:outline-none focus:ring-2 focus:ring-accent/20 focus:ring-offset-2",
            )}
          >
            Sign in
          </Link>
        </div>
      </div>
    </nav>
  );
}
