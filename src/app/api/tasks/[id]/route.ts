import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth, hasCompanyAccess } from '@/lib/guards'

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  const { id } = await params

  const task = await db.task.findUnique({
    where: { id },
    include: {
      company: { select: { id: true, name: true, code: true } },
      createdBy: { select: { id: true, displayName: true, role: true } },
      assignments: { include: { user: { select: { id: true, displayName: true, role: true } } } },
      checklistItems: {
        include: { assignedTo: { select: { id: true, displayName: true } } },
        orderBy: { createdAt: 'asc' },
      },
      workSubmissions: {
        include: {
          submittedBy: { select: { id: true, displayName: true } },
          decisions: {
            include: { reviewer: { select: { id: true, displayName: true } } },
            orderBy: { createdAt: 'desc' },
          },
        },
        orderBy: { submittedAt: 'desc' },
      },
      referenceBindings: { include: { referenceVersion: true } },
    },
  })

  if (!task) {
    return NextResponse.json({ error: 'تسک یافت نشد' }, { status: 404 })
  }

  // Check access
  const hasAccess = await hasCompanyAccess(user!.id, task.companyId)
  if (!hasAccess && task.createdById !== user!.id && !task.assignments.some(a => a.userId === user!.id)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  return NextResponse.json({ task })
}

// PATCH /api/tasks/[id] - update task status
export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  const { id } = await params
  const body = await request.json()

  const task = await db.task.findUnique({ where: { id } })
  if (!task) {
    return NextResponse.json({ error: 'تسک یافت نشد' }, { status: 404 })
  }

  // Check access
  const hasAccess = await hasCompanyAccess(user!.id, task.companyId)
  if (!hasAccess && task.createdById !== user!.id) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const updateData: any = {}
  if (body.title) updateData.title = body.title
  if (body.description !== undefined) updateData.description = body.description
  if (body.dueAt) updateData.dueAt = new Date(body.dueAt)
  if (body.priority) updateData.priority = body.priority
  if (body.weight !== undefined) updateData.weight = body.weight
  if (body.status) updateData.status = body.status

  const previousState = JSON.stringify({
    title: task.title,
    status: task.status,
    priority: task.priority,
  })

  const updated = await db.task.update({
    where: { id },
    data: updateData,
  })

  // Audit log
  await db.auditEvent.create({
    data: {
      actorId: user!.id,
      action: 'update',
      objectType: 'task',
      objectId: id,
      occurredAt: new Date(),
      previousState,
      newState: JSON.stringify(updateData),
    },
  })

  return NextResponse.json({ task: updated })
}
