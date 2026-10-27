import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

async function checkInOut(request: NextRequest, eventType: 'check_in' | 'check_out') {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  const todayStart = new Date()
  todayStart.setHours(0, 0, 0, 0)
  const todayEnd = new Date()
  todayEnd.setHours(23, 59, 59, 999)

  const existing = await db.attendanceRecord.findFirst({
    where: {
      userId: user!.id,
      eventType,
      eventTime: { gte: todayStart, lte: todayEnd },
    },
  })

  if (existing) {
    return NextResponse.json({
      error: `امروز قبلاً ${eventType === 'check_in' ? 'ورود' : 'خروج'} ثبت شده است`,
      record: existing,
    }, { status: 409 })
  }

  const record = await db.attendanceRecord.create({
    data: {
      userId: user!.id,
      eventType,
      source: 'manual',
    },
  })

  return NextResponse.json({ record }, { status: 201 })
}

export async function POST(request: NextRequest) {
  return checkInOut(request, 'check_out')
}
