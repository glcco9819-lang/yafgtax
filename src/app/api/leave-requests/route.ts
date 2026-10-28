import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

export async function GET(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  const { searchParams } = new URL(request.url)
  const status = searchParams.get('status')

  let where: any = { userId: user!.id }
  if (status) where.status = status

  const requests = await db.leaveRequest.findMany({
    where,
    include: {
      reviewedBy: { select: { id: true, displayName: true } },
    },
    orderBy: { createdAt: 'desc' },
    take: 50,
  })

  return NextResponse.json({ requests })
}

export async function POST(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  try {
    const body = await request.json()
    const { startAt, endAt, reason, leaveType } = body

    if (!startAt || !endAt || !reason) {
      return NextResponse.json({ error: 'تاریخ شروع/پایان و دلیل الزامی است' }, { status: 400 })
    }

    const leaveRequest = await db.leaveRequest.create({
      data: {
        userId: user!.id,
        startAt: new Date(startAt),
        endAt: new Date(endAt),
        reason,
        leaveType: leaveType || 'personal',
        status: 'pending',
      },
    })

    await db.auditEvent.create({
      data: {
        actorId: user!.id,
        action: 'create',
        objectType: 'leave_request',
        objectId: leaveRequest.id,
        occurredAt: new Date(),
      },
    })

    // Notify supervisors/ceo
    const approvers = await db.user.findMany({
      where: { role: { in: ['supervisor', 'ceo'] }, isActive: true },
    })
    if (approvers.length > 0) {
      await db.notification.createMany({
        data: approvers.map(a => ({
          userId: a.id,
          eventKey: `leave-request-${leaveRequest.id}-${a.id}-${Date.now()}`,
          type: 'leave_request',
          title: 'درخواست مرخصی جدید',
          message: `${user!.displayName} درخواست مرخصی از ${startAt} تا ${endAt} ثبت کرد`,
        })),
      })
    }

    return NextResponse.json({ request: leaveRequest }, { status: 201 })
  } catch (error) {
    console.error('Leave request error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
