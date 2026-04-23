"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { loginFromBrowser } from "../../lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [userCode, setUserCode] = useState("USR-TP-OPS-001");
  const [password, setPassword] = useState("demo");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const res = await loginFromBrowser(userCode.trim(), password);
      window.localStorage.setItem("twinai_access_token", res.access_token);
      router.push("/workflows");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Lỗi đăng nhập.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="admin-shell-root" style={{ maxWidth: 420, margin: "3rem auto", padding: "0 1rem" }}>
      <p className="breadcrumb">
        <Link href="/">← Trang chủ</Link>
      </p>
      <h1>Đăng nhập MVP</h1>
      <p className="muted">
        Chỉ hoạt động khi API bật <code>AUTH_ENABLED=true</code> và <code>JWT_SECRET</code> đã cấu hình. Mật khẩu seed mặc định:{" "}
        <strong>demo</strong>.
      </p>
      <form onSubmit={onSubmit} className="workflow-actions-block">
        {error ? <p className="error-text">{error}</p> : null}
        <label className="workflow-note">
          <span>User code</span>
          <input value={userCode} onChange={(e) => setUserCode(e.target.value)} disabled={busy} autoComplete="username" />
        </label>
        <label className="workflow-note">
          <span>Mật khẩu</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            disabled={busy}
            autoComplete="current-password"
          />
        </label>
        <button className="primary-button" type="submit" disabled={busy}>
          {busy ? "Đang đăng nhập…" : "Đăng nhập"}
        </button>
      </form>
    </main>
  );
}
