import { NextRequest, NextResponse } from 'next/server';

const BACKEND_URL = process.env.YFG_BACKEND_URL || 'http://127.0.0.1:8000';

// Catch-all proxy: forward ALL /api/* requests to the YFG FastAPI backend.
// Next.js has no other API routes — YFG is the only backend.

export async function GET(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return proxyRequest(req, params);
}

export async function POST(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return proxyRequest(req, params);
}

export async function PUT(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return proxyRequest(req, params);
}

export async function PATCH(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return proxyRequest(req, params);
}

export async function DELETE(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return proxyRequest(req, params);
}

export async function OPTIONS(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return proxyRequest(req, params);
}

export async function HEAD(req: NextRequest, { params }: { params: Promise<{ path?: string[] }> }) {
  return proxyRequest(req, params);
}

async function proxyRequest(req: NextRequest, params: Promise<{ path?: string[] }>) {
  const { path } = await params;
  const pathSegments = path ? path.join('/') : '';
  const fullPath = `/api/${pathSegments}`;
  const targetUrl = `${BACKEND_URL}${fullPath}${req.nextUrl.search}`;
  const method = req.method;

  // Forward cookies + content-type
  const headers = new Headers();
  const cookie = req.headers.get('cookie');
  if (cookie) headers.set('cookie', cookie);
  const contentType = req.headers.get('content-type');
  if (contentType) headers.set('content-type', contentType);

  let body: BodyInit | null = null;
  if (method !== 'GET' && method !== 'HEAD') {
    if (contentType?.includes('multipart/form-data')) {
      body = await req.formData();
    } else {
      body = await req.text();
    }
  }

  try {
    const upstream = await fetch(targetUrl, {
      method,
      headers,
      body,
      redirect: 'manual',
    });

    // Build response with status, body, and forwarded headers
    const responseHeaders = new Headers();
    upstream.headers.forEach((value, key) => {
      const lk = key.toLowerCase();
      // Skip auto-managed headers
      if (lk === 'transfer-encoding' || lk === 'content-encoding' || lk === 'content-length') return;
      responseHeaders.set(key, value);
    });

    const responseBody = await upstream.arrayBuffer();
    return new NextResponse(responseBody, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: responseHeaders,
    });
  } catch (e: any) {
    return NextResponse.json(
      { error: 'Backend unreachable', detail: e.message, path: fullPath },
      { status: 502 }
    );
  }
}
