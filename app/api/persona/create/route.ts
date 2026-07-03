// G 20260624
/*
    让 Next.js 知道你的 Python FastAPI 后端运行在哪里
*/
import { NextRequest, NextResponse } from "next/server";

// 如果 .env.local 里配置了 PY_BACKEND_URL，就用配置的地址；
// 如果没有配置，就默认使用 http://127.0.0.1:8000。
const PY_BACKEND_URL = process.env.PY_BACKEND_URL ?? "http://127.0.0.1:8000";

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const response = await fetch(`${PY_BACKEND_URL}/api/persona/create`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
      cache: "no-store",
    });

    const data = await response.json();

    return NextResponse.json(data, {
      status: response.status,
    });
  } catch (error) {
    return NextResponse.json(
      {
        error: "Failed to create persona",
        detail: error instanceof Error ? error.message : String(error),
      },
      { status: 500 },
    );
  }
}

// G 20260624 #