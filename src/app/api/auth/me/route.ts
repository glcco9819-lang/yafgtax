import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

export async function GET(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response
  return NextResponse.json({
    user: {
      id: user!.id,
      username: user!.username,
      displayName: user!.displayName,
      role: user!.role,
    },
  })
}
