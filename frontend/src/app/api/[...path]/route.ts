import { NextRequest, NextResponse } from 'next/server';

function getBackendUrl(): string {
  let url = (
    process.env.API_PROXY_URL ||
    process.env.BACKEND_URL ||
    process.env.NEXT_PUBLIC_API_URL ||
    'http://localhost:8000'
  ).replace(/\/$/, '');

  if (url && !/^https?:\/\//i.test(url)) {
    url = `https://${url}`;
  }

  return url;
}

async function proxy(req: NextRequest, pathSegments: string[]) {
  const backend = getBackendUrl();
  const path = pathSegments.join('/');
  const target = new URL(`${backend}/api/${path}`);

  req.nextUrl.searchParams.forEach((value, key) => {
    target.searchParams.set(key, value);
  });

  const headers = new Headers();
  const contentType = req.headers.get('content-type');
  if (contentType) {
    headers.set('content-type', contentType);
  }

  const init: RequestInit = {
    method: req.method,
    headers,
    cache: 'no-store',
  };

  if (req.method !== 'GET' && req.method !== 'HEAD') {
    init.body = await req.text();
  }

  try {
    const res = await fetch(target.toString(), init);
    const body = await res.arrayBuffer();
    const responseHeaders = new Headers();
    const responseType = res.headers.get('content-type');
    if (responseType) {
      responseHeaders.set('content-type', responseType);
    }
    return new NextResponse(body, { status: res.status, headers: responseHeaders });
  } catch (err) {
    const message = err instanceof Error ? err.message : 'unknown error';
    return NextResponse.json(
      {
        detail: `Backend unreachable at ${backend}. Set API_PROXY_URL on Render to your backend URL. (${message})`,
      },
      { status: 502 },
    );
  }
}

type RouteContext = { params: { path: string[] } };

export async function GET(req: NextRequest, { params }: RouteContext) {
  return proxy(req, params.path);
}

export async function POST(req: NextRequest, { params }: RouteContext) {
  return proxy(req, params.path);
}

export async function PUT(req: NextRequest, { params }: RouteContext) {
  return proxy(req, params.path);
}

export async function PATCH(req: NextRequest, { params }: RouteContext) {
  return proxy(req, params.path);
}

export async function DELETE(req: NextRequest, { params }: RouteContext) {
  return proxy(req, params.path);
}
