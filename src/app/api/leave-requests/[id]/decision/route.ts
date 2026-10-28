import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response
  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const { id } = await params
  const body = await request.json()
  const { status, reviewNotes } = body

  if (!['approved', 'rejected'].includes(status)) {
    return NextResponse.json({ error: 'وضعیت نامعتبر' }, { status: 400 })
  }

  const leaveRequest = await db.leaveRequest.findUnique({ where: { id } })
  if (!leaveRequest) {
    return NextResponse.json({ error: 'درخواست یافت نشد' }, { status: 404 })
  }

  if (leaveRequest.status !== 'pending') {
    return NextResponse.json({ error: 'این درخواست قبلاً بررسی شده' }, { status: 400 })
  }

  const updated = await db.leaveRequest.update({
    where: { id },
    data: {
      status,
      reviewedById: user!.id,
      reviewNotes,
      reviewedAt: new Date(),
    },
  })

  await db.auditEvent.create({
    data: {
      actorId: user!.id,
      action: status,
      objectType: 'leave_request',
      objectId: id,
      occurredAt: new Date(),
      reason: reviewNotes,
    },
  })

  // Notify user
  await db.notification.create({
    data: {
      userId: leaveRequest.userId,
      eventKey: `leave-decision-${id}-${Date.now()}`,
      type: 'leave_decision',
      title: `پاسخ به درخواست مرخصی: ${status === 'approved' ? 'تأیید شد' : 'رد شد'}`,
      message: reviewNotes || 'بدون توضیحات اضافه',
    },
  })

  return NextResponse.json({ request: updated })
}
