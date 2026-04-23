"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import type { ReactNode } from "react";

type AdminShellProps = {
  title: string;
  eyebrow: string;
  status: string;
  isOnline: boolean;
  tag?: string;
  children: ReactNode;
};

const navItems = [
  { href: "/", label: "Tổng quan" },
  { href: "/operations", label: "Vận hành" },
  { href: "/assets", label: "Tài sản" },
  { href: "/org", label: "Tổ chức" },
  { href: "/ontology", label: "Ontology" },
  { href: "/manuals", label: "Manual / RAG" },
  { href: "/workflows", label: "Task / Mua hàng" },
  { href: "/audit-logs", label: "Audit log" },
];

export function AdminShell({ title, eyebrow, status, isOnline, tag, children }: AdminShellProps) {
  const pathname = usePathname();

  return (
    <div className="admin-shell">
      <aside className="admin-sidebar" aria-label="Admin navigation">
        <div className="brand-block">
          <strong>TwinAI</strong>
          <span>Ontology Admin</span>
        </div>
        <nav className="admin-nav">
          {navItems.map((item) => (
            <Link className={pathname === item.href ? "active" : undefined} href={item.href} key={item.href}>
              {item.label}
            </Link>
          ))}
        </nav>
        <div className="phase-panel">
          <span>Roadmap</span>
          <strong>Phase 04+</strong>
          <p>Manual, Chat, Rule Engine và Neo4j sync đang là trọng tâm hiện tại.</p>
        </div>
      </aside>

      <main className="admin-main">
        <header className="admin-header">
          <div>
            <p className="eyebrow">{eyebrow}</p>
            <h1>{title}</h1>
          </div>
          <div className="header-actions">
            <span className={isOnline ? "status" : "status warning"}>{status}</span>
            {tag ? <span className="status neutral">{tag}</span> : null}
          </div>
        </header>
        {children}
      </main>
    </div>
  );
}
