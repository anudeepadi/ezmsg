"use client";

import Link from "next/link";
import {
  GitBranch,
  Clock,
  Users,
  Shield,
  MessageSquare,
  BarChart3,
  ArrowRight,
  Activity,
  Zap,
  Globe,
  Terminal,
  ChevronRight,
  Server,
  Workflow,
} from "lucide-react";
import { Threads } from "@/components/backgrounds/threads";

/* ─── Data ──────────────────────────────────────── */

const capabilities = [
  {
    icon: GitBranch,
    label: "Protocol Engine",
    title: "V11 branching protocol with conditional paths",
    specs: [
      "Node types: message, check-in, escalation, checkout",
      "Edge conditions: timeout, response, variable match",
      "Session state persisted in Redis (sub-ms lookup)",
      "Bilingual templates with variable interpolation",
    ],
  },
  {
    icon: Clock,
    label: "Scheduler",
    title: "Timezone-aware delivery with retry logic",
    specs: [
      "Configurable delivery windows per participant",
      "Exponential backoff: up to 8 retries",
      "Batch processing: 100 messages per cycle",
      "Oldest-pending monitoring with auto-requeue",
    ],
  },
  {
    icon: MessageSquare,
    label: "Delivery",
    title: "Multi-channel with automatic fallback",
    specs: [
      "SMS via Twilio (primary channel)",
      "Push notifications via Firebase FCM",
      "Channel fallback on delivery failure",
      "Per-message delivery receipts and status tracking",
    ],
  },
  {
    icon: Users,
    label: "Participants",
    title: "Cohort management with full audit trails",
    specs: [
      "Bulk enrollment via API or admin dashboard",
      "Protocol stage tracking per participant",
      "HELPNOW escalation and SLIP detection",
      "Withdrawal and suspension workflows",
    ],
  },
  {
    icon: Shield,
    label: "Security",
    title: "Research-grade data protection",
    specs: [
      "JWT auth with HttpOnly secure cookies",
      "API key isolation (timing-safe comparison)",
      "AES-256 PII encryption at rest",
      "Role-based access: admin, researcher, observer",
    ],
  },
  {
    icon: BarChart3,
    label: "Analytics",
    title: "Real-time queue health and delivery metrics",
    specs: [
      "Sent / pending / failed / in-progress counters",
      "Per-project and global scheduler dashboards",
      "Message latency tracking (oldest pending)",
      "Exportable delivery logs for analysis",
    ],
  },
];

const architectureLayers = [
  {
    label: "CLIENT",
    items: [
      "Next.js 14 (App Router)",
      "React Flow graph editor",
      "Zustand state",
    ],
  },
  {
    label: "API",
    items: [
      "FastAPI + async/await",
      "~70 REST endpoints",
      "SlowAPI rate limiting",
    ],
  },
  {
    label: "DATA",
    items: [
      "PostgreSQL (19 models)",
      "Redis (sessions + cache)",
      "Alembic migrations",
    ],
  },
  {
    label: "DELIVERY",
    items: ["Background worker", "Twilio SMS", "Firebase FCM push"],
  },
];

const endpoints = [
  {
    method: "POST",
    path: "/v1/auth/login",
    desc: "Authenticate and set cookie",
  },
  { method: "GET", path: "/v1/projects", desc: "List all projects" },
  {
    method: "POST",
    path: "/v1/projects/:id/nodes",
    desc: "Create protocol node",
  },
  {
    method: "POST",
    path: "/v1/protocol/session/start",
    desc: "Start participant session",
  },
  {
    method: "POST",
    path: "/v1/protocol/session/respond",
    desc: "Process participant response",
  },
  { method: "GET", path: "/v1/scheduler/health", desc: "Queue health metrics" },
];

/* ─── Page ──────────────────────────────────────── */

export default function HomePage() {
  // Teal accent converted to 0-1 RGB for Threads: #0d7377
  const tealColor: [number, number, number] = [0.051, 0.451, 0.467];

  return (
    <div className="min-h-dvh">
      {/* ── Hero ──────────────────────────────── */}
      <section className="relative overflow-hidden">
        {/* Threads background */}
        <div className="absolute inset-0 z-0 opacity-20">
          <Threads
            color={tealColor}
            amplitude={1.2}
            distance={0.3}
            enableMouseInteraction
          />
        </div>

        <div className="relative z-10 mx-auto max-w-6xl px-6 pt-24 pb-28">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-start">
            {/* Left: Copy */}
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full border border-border bg-surface mb-8">
                <span className="relative flex size-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-accent opacity-75" />
                  <span className="relative inline-flex rounded-full size-2 bg-accent" />
                </span>
                <span className="text-caption font-mono font-medium text-text-secondary">
                  PROTOCOL ENGINE v1.0
                </span>
              </div>

              <h1 className="text-display font-serif text-text mb-6 leading-[1.08] text-balance">
                Messaging protocols{" "}
                <span className="text-accent">for health interventions</span>
              </h1>
              <p className="text-body text-text-secondary max-w-lg mb-10 leading-relaxed text-pretty">
                Design branching message sequences, schedule timezone-aware
                delivery, and monitor queue health — built for research teams
                running intervention studies at scale.
              </p>

              <div className="flex items-center gap-4">
                <Link
                  href="/login"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md bg-accent text-white font-medium text-body-sm hover:bg-accent-hover transition-colors focus:outline-none focus:ring-2 focus:ring-accent/20 focus:ring-offset-2"
                >
                  Go to Dashboard
                  <ArrowRight className="size-4" />
                </Link>
                <a
                  href="#about"
                  className="inline-flex items-center gap-2 px-5 py-2.5 rounded-md border border-border text-text-secondary font-medium text-body-sm hover:text-text hover:bg-surface-warm transition-colors"
                >
                  Learn More
                </a>
              </div>
            </div>

            {/* Right: Protocol flow visualization */}
            <div className="rounded-lg border border-border bg-surface overflow-hidden shadow-card">
              {/* Terminal header */}
              <div className="flex items-center gap-2 px-4 py-2.5 border-b border-border bg-background">
                <div className="flex gap-1.5">
                  <span className="size-2.5 rounded-full bg-border-strong" />
                  <span className="size-2.5 rounded-full bg-border-strong" />
                  <span className="size-2.5 rounded-full bg-border-strong" />
                </div>
                <span className="text-caption font-mono text-text-muted ml-2">
                  protocol_v11.yaml
                </span>
              </div>
              {/* Protocol definition */}
              <pre className="p-5 text-[13px] leading-[1.7] font-mono text-text-secondary overflow-x-auto">
                <span className="text-text-muted">
                  # V11 Quit-Smoking Protocol
                </span>
                {"\n"}
                <span className="text-accent">protocol</span>:{"\n"}
                {"  "}
                <span className="text-text">name</span>:{" "}
                <span className="text-text-secondary">
                  &quot;QuitTxt 2025&quot;
                </span>
                {"\n"}
                {"  "}
                <span className="text-text">nodes</span>:{" "}
                <span className="text-text-muted">1,024</span>
                {"\n"}
                {"  "}
                <span className="text-text">templates</span>:{" "}
                <span className="text-text-muted">2,048 (en/es)</span>
                {"\n"}
                {"\n"}
                <span className="text-accent">flow</span>:{"\n"}
                {"  "}
                <span className="text-text">entry</span>{" "}
                <span className="text-text-muted">→</span>{" "}
                <span className="text-text">daily_checkin</span>
                {"\n"}
                {"  "}
                <span className="text-text">daily_checkin</span>{" "}
                <span className="text-text-muted">→</span>{" "}
                <span className="text-success">on_track</span>{" "}
                <span className="text-text-muted">
                  | response == &quot;good&quot;
                </span>
                {"\n"}
                {"  "}
                <span className="text-text">daily_checkin</span>{" "}
                <span className="text-text-muted">→</span>{" "}
                <span className="text-warning">slip_support</span>{" "}
                <span className="text-text-muted">
                  | response == &quot;slip&quot;
                </span>
                {"\n"}
                {"  "}
                <span className="text-text">daily_checkin</span>{" "}
                <span className="text-text-muted">→</span>{" "}
                <span className="text-error">helpnow</span>{" "}
                <span className="text-text-muted">
                  | response == &quot;help&quot;
                </span>
                {"\n"}
                {"  "}
                <span className="text-text">daily_checkin</span>{" "}
                <span className="text-text-muted">→</span>{" "}
                <span className="text-text-muted">timeout_nudge</span>{" "}
                <span className="text-text-muted">| no_response 24h</span>
                {"\n"}
                {"\n"}
                <span className="text-accent">delivery</span>:{"\n"}
                {"  "}
                <span className="text-text">channels</span>:{" "}
                <span className="text-text-muted">[sms, push]</span>
                {"\n"}
                {"  "}
                <span className="text-text">window</span>:{" "}
                <span className="text-text-muted">
                  08:00–20:00 participant_tz
                </span>
                {"\n"}
                {"  "}
                <span className="text-text">retry</span>:{" "}
                <span className="text-text-muted">exponential(max=8)</span>
              </pre>
            </div>
          </div>
        </div>
      </section>

      {/* ── About ─────────────────────────────── */}
      <section id="about" className="border-t border-border bg-surface-warm">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
            <div>
              <span className="text-caption font-mono font-medium text-accent uppercase">
                About Cadence
              </span>
              <h2 className="text-headline font-serif text-text mt-3 mb-6 text-balance">
                A complete platform for automated health messaging
              </h2>
              <p className="text-body text-text-secondary leading-relaxed mb-4 text-pretty">
                Cadence is a messaging protocol management system designed for
                research teams running behavioral health intervention studies.
                It handles the full lifecycle — from designing branching message
                protocols to delivering SMS and push notifications on
                personalized schedules.
              </p>
              <p className="text-body text-text-secondary leading-relaxed text-pretty">
                Built on the V11 protocol specification used in quit-smoking
                interventions, Cadence supports complex conditional flows,
                bilingual templates, timezone-aware scheduling, and real-time
                monitoring of message delivery across thousands of participants.
              </p>
            </div>

            <div className="space-y-4">
              {[
                {
                  icon: Workflow,
                  title: "Visual Protocol Editor",
                  desc: "Drag-and-drop graph editor for building branching message flows with conditional edges and variable-based routing.",
                },
                {
                  icon: Globe,
                  title: "Participant-Centric Delivery",
                  desc: "Each participant gets messages in their timezone, preferred language, and on their chosen channel — with automatic fallback.",
                },
                {
                  icon: Shield,
                  title: "Research-Grade Security",
                  desc: "HIPAA-conscious design with AES-256 encryption, role-based access, and full audit trails on every interaction.",
                },
              ].map((item) => {
                const Icon = item.icon;
                return (
                  <div
                    key={item.title}
                    className="flex gap-4 p-5 rounded-lg border border-border bg-surface"
                  >
                    <div className="flex-shrink-0 size-10 rounded-md bg-accent-light flex items-center justify-center">
                      <Icon className="size-5 text-accent" />
                    </div>
                    <div>
                      <h3 className="text-body font-medium text-text mb-1">
                        {item.title}
                      </h3>
                      <p className="text-body-sm text-text-secondary leading-relaxed text-pretty">
                        {item.desc}
                      </p>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </section>

      {/* ── How It Works ────────────────────── */}
      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-16">
            <span className="text-caption font-mono font-medium text-accent uppercase">
              Message Lifecycle
            </span>
            <h2 className="text-headline font-serif text-text mt-3 text-balance">
              From protocol definition to delivery
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-px bg-border rounded-lg overflow-hidden">
            {[
              {
                step: "01",
                icon: Workflow,
                title: "Define",
                desc: "Build node graph with message templates, conditions, and branching paths",
              },
              {
                step: "02",
                icon: Users,
                title: "Enroll",
                desc: "Add participants with timezone, language preference, and channel settings",
              },
              {
                step: "03",
                icon: Zap,
                title: "Schedule",
                desc: "Engine evaluates protocol state and queues messages within delivery windows",
              },
              {
                step: "04",
                icon: Globe,
                title: "Deliver",
                desc: "Messages sent via SMS/push with retry logic, receipts, and failure handling",
              },
            ].map((item) => {
              const Icon = item.icon;
              return (
                <div key={item.step} className="bg-surface p-8 flex flex-col">
                  <div className="flex items-center gap-3 mb-6">
                    <span className="text-caption font-mono text-accent font-medium tabular-nums">
                      {item.step}
                    </span>
                    <Icon className="size-4 text-text-muted" />
                  </div>
                  <h3 className="text-subtitle font-serif text-text mb-2 text-balance">
                    {item.title}
                  </h3>
                  <p className="text-body-sm text-text-secondary leading-relaxed text-pretty">
                    {item.desc}
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Capabilities ────────────────────── */}
      <section id="features" className="border-t border-border bg-surface-warm">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="mb-16">
            <span className="text-caption font-mono font-medium text-accent uppercase">
              Capabilities
            </span>
            <h2 className="text-headline font-serif text-text mt-3 text-balance">
              Technical specifications
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {capabilities.map((cap) => {
              const Icon = cap.icon;
              return (
                <div
                  key={cap.label}
                  className="group rounded-lg border border-border bg-surface p-6 hover:border-accent/30 transition-colors"
                >
                  <div className="flex items-center gap-3 mb-4">
                    <div className="size-8 rounded-md bg-accent-light flex items-center justify-center group-hover:bg-accent transition-colors">
                      <Icon className="size-4 text-accent group-hover:text-white transition-colors" />
                    </div>
                    <span className="text-caption font-mono font-medium text-accent uppercase">
                      {cap.label}
                    </span>
                  </div>
                  <h3 className="text-body font-medium text-text mb-4 text-balance">
                    {cap.title}
                  </h3>
                  <ul className="space-y-2">
                    {cap.specs.map((spec) => (
                      <li
                        key={spec}
                        className="flex items-start gap-2 text-body-sm text-text-secondary"
                      >
                        <ChevronRight className="size-3.5 text-border-strong mt-0.5 flex-shrink-0" />
                        <span className="text-pretty">{spec}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── Architecture ────────────────────── */}
      <section id="architecture" className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-24">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
            {/* Left: Stack */}
            <div>
              <span className="text-caption font-mono font-medium text-accent uppercase">
                Architecture
              </span>
              <h2 className="text-headline font-serif text-text mt-3 mb-8 text-balance">
                System overview
              </h2>

              <div className="space-y-4">
                {architectureLayers.map((layer) => (
                  <div
                    key={layer.label}
                    className="rounded-lg border border-border bg-surface p-5"
                  >
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-caption font-mono font-medium text-accent">
                        {layer.label}
                      </span>
                      <div className="flex-1 h-px bg-border" />
                    </div>
                    <div className="flex flex-wrap gap-2">
                      {layer.items.map((item) => (
                        <span
                          key={item}
                          className="inline-flex items-center px-2.5 py-1 rounded-md bg-background text-body-sm text-text-secondary font-mono"
                        >
                          {item}
                        </span>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Right: API endpoints */}
            <div>
              <div className="flex items-center gap-3 mb-8">
                <Terminal className="size-4 text-accent" />
                <span className="text-caption font-mono font-medium text-accent uppercase">
                  REST API — Key Endpoints
                </span>
              </div>

              <div className="rounded-lg border border-border bg-surface overflow-hidden">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-border bg-background">
                      <th className="px-4 py-2.5 text-left text-caption font-mono font-medium text-text-muted">
                        METHOD
                      </th>
                      <th className="px-4 py-2.5 text-left text-caption font-mono font-medium text-text-muted">
                        ENDPOINT
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {endpoints.map((ep) => (
                      <tr
                        key={ep.path}
                        className="border-b border-border last:border-0 hover:bg-background/50 transition-colors"
                      >
                        <td className="px-4 py-3">
                          <span
                            className={`text-caption font-mono font-medium ${
                              ep.method === "POST"
                                ? "text-accent"
                                : "text-success"
                            }`}
                          >
                            {ep.method}
                          </span>
                        </td>
                        <td className="px-4 py-3">
                          <div>
                            <code className="text-body-sm font-mono text-text">
                              {ep.path}
                            </code>
                            <p className="text-caption text-text-muted mt-0.5">
                              {ep.desc}
                            </p>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="mt-4 flex items-center gap-2 px-1">
                <Server className="size-3.5 text-text-muted" />
                <span className="text-caption text-text-muted">
                  ~70 endpoints total &middot; OpenAPI spec at{" "}
                  <code className="font-mono">/docs</code>
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Stats Strip ─────────────────────── */}
      <section className="border-t border-border bg-surface-warm">
        <div className="mx-auto max-w-6xl px-6 py-16">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {[
              { value: "19", label: "Database models", sub: "SQLAlchemy ORM" },
              { value: "~70", label: "API endpoints", sub: "FastAPI async" },
              {
                value: "1,024",
                label: "Protocol nodes",
                sub: "V11 full import",
              },
              {
                value: "2,048",
                label: "Message templates",
                sub: "en/es bilingual",
              },
            ].map((stat) => (
              <div key={stat.label} className="text-center">
                <p className="text-headline font-mono text-text font-medium tabular-nums">
                  {stat.value}
                </p>
                <p className="text-body-sm text-text-secondary mt-1">
                  {stat.label}
                </p>
                <p className="text-caption text-text-muted mt-0.5">
                  {stat.sub}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ───────────────────────────────── */}
      <section className="border-t border-border">
        <div className="mx-auto max-w-6xl px-6 py-24 text-center">
          <h2 className="text-headline font-serif text-text mb-4 text-balance">
            Ready to manage your messaging protocols?
          </h2>
          <p className="text-body text-text-secondary mb-8 max-w-md mx-auto text-pretty">
            Sign in to access the admin dashboard, design protocols, enroll
            participants, and monitor delivery in real time.
          </p>
          <Link
            href="/login"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-md bg-accent text-white font-medium text-body hover:bg-accent-hover transition-colors focus:outline-none focus:ring-2 focus:ring-accent/20 focus:ring-offset-2"
          >
            Go to Dashboard
            <ArrowRight className="size-4" />
          </Link>
        </div>
      </section>

      {/* ── Footer ──────────────────────────── */}
      <footer className="border-t border-border bg-surface-warm">
        <div className="mx-auto max-w-6xl px-6 py-8 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="flex items-center justify-center size-7 rounded-md bg-accent text-white">
              <Activity className="size-3.5" />
            </div>
            <span className="text-body-sm font-serif text-text">Cadence</span>
          </div>
          <div className="flex items-center gap-6">
            <a
              href="#about"
              className="text-caption text-text-muted hover:text-text transition-colors"
            >
              About
            </a>
            <a
              href="#features"
              className="text-caption text-text-muted hover:text-text transition-colors"
            >
              Capabilities
            </a>
            <a
              href="#architecture"
              className="text-caption text-text-muted hover:text-text transition-colors"
            >
              Architecture
            </a>
            <span className="text-caption text-text-muted">
              Messaging Protocol Management System
            </span>
          </div>
        </div>
      </footer>
    </div>
  );
}
