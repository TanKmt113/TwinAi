import { NextRequest, NextResponse } from "next/server";
import { randomUUID } from "crypto";

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

  let response: Response;
  try {
    response = await fetch(targetUrl, {
      method: request.method,
      headers: buildHeaders(request),
      body: request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer(),
      cache: "no-store",
    });
  } catch (error) {
    const requestId = randomUUID();
    const message = error instanceof Error ? error.message : "Unknown proxy error";
    console.error("Backend proxy failed", {
      requestId,
      method: request.method,
      targetUrl,
      message,
    });
    return NextResponse.json(
      {
        request_id: requestId,
        error: "backend_proxy_failed",
        message,
        log: `Backend proxy failed request_id=${requestId} target_url=${targetUrl}`,
      },
      { status: 502 },
    );
  }

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

function buildHeaders(request: NextRequest) {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }
  return headers;
}
