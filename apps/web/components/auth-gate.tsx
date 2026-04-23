"use client";

import { usePathname, useRouter } from "next/navigation";
import { type ReactNode, useEffect, useState } from "react";

const TOKEN_KEY = "twinai_access_token";

/** Mặc định bật: set NEXT_PUBLIC_REQUIRE_LOGIN=false để tắt (dev không dùng JWT). */
function isLoginWallEnabled(): boolean {
  return process.env.NEXT_PUBLIC_REQUIRE_LOGIN !== "false";
}

function safeReturnPath(pathWithQuery: string): string {
  if (!pathWithQuery.startsWith("/") || pathWithQuery.startsWith("//")) {
    return "/";
  }
  return pathWithQuery;
}

export function AuthGate({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const [allowed, setAllowed] = useState(() => !isLoginWallEnabled());

  useEffect(() => {
    if (!isLoginWallEnabled()) {
      setAllowed(true);
      return;
    }
    if (pathname === "/login") {
      setAllowed(true);
      return;
    }
    const token = typeof window !== "undefined" ? window.localStorage.getItem(TOKEN_KEY) : null;
    if (!token) {
      const fullPath =
        typeof window !== "undefined" ? `${window.location.pathname}${window.location.search}` : pathname || "/";
      router.replace(`/login?next=${encodeURIComponent(safeReturnPath(fullPath))}`);
      return;
    }
    setAllowed(true);
  }, [pathname, router]);

  if (!isLoginWallEnabled()) {
    return <>{children}</>;
  }
  if (pathname === "/login") {
    return <>{children}</>;
  }
  if (!allowed) {
    return (
      <div className="admin-shell-root" style={{ padding: "2rem", textAlign: "center" }}>
        <p>Đang kiểm tra phiên đăng nhập…</p>
      </div>
    );
  }
  return <>{children}</>;
}
