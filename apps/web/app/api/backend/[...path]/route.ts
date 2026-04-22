import { NextRequest, NextResponse } from "next/server";

const backendBaseUrl = process.env.BACKEND_INTERNAL_URL ?? process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

type RouteContext = {
  params: Promise<{
    path: string[];
  }>;
};

async function proxy(request: NextRequest, context: RouteContext) {
  const { path } = await context.params;
  const targetPath = path.join("/");
  const url = new URL(request.url);
  const targetUrl = `${backendBaseUrl}/${targetPath}${url.search}`;

  const response = await fetch(targetUrl, {
    method: request.method,
    headers: {
      "content-type": request.headers.get("content-type") ?? "application/json",
    },
    body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.text(),
    cache: "no-store",
  });

  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: {
      "content-type": response.headers.get("content-type") ?? "application/json",
    },
  });
}

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

