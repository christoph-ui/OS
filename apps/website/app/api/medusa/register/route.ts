import { NextRequest, NextResponse } from 'next/server';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:4080';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    // Forward the registration to FastAPI backend
    const response = await fetch(`${API_BASE_URL}/api/medusa/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      return NextResponse.json(error, { status: response.status });
    }

    const data = await response.json();

    return NextResponse.json(data);
  } catch (error) {
    console.error('Medusa registration error:', error);
    return NextResponse.json(
      { error: 'Failed to register for Medusa download' },
      { status: 500 }
    );
  }
}
