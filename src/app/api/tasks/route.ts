import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth, hasCompanyAccess } from '@/lib/guards'

// GET /api/tasks - list tasks (filtered by role and company access)
export async function GET(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  const { searchParams } = new URL(request.url)
  const companyId = searchParams.get('companyId')
  const status = searchParams.get('status')
  const assignedToMe = searchParams.get('mine') === 'true'

  let where: any = {}
  
  if (status) where.status = status
  if (companyId) where.companyId = companyId

  // For employees, only tasks assigned to them OR that they created
  if (user!.role === 'employee') {
    if (assignedToMe) {
      where.assignments = { some: { userId: user!.id } }
    } else {
      where.OR = [
        { assignments: { some: { userId: user!.id } } },
        { createdById: user!.id },
      ]
    }
  }

  const tasks = await db.task.findMany({
    where,
    include: {
      company: { select: { id: true, name: true, code: true } },
      assignments: { include: { user: { select: { id: true, displayName: true, role: true } } } },
      _count: { select: { workSubmissions: true, checklistItems: true } },
    },
    orderBy: { createdAt: 'desc' },
    take: 100,
  })

  return NextResponse.json({ tasks })
}

// POST /api/tasks - create task (supervisor/ceo only)
export async function POST(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response
  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  try {
    const body = await request.json()
    const { title, description, companyId, dueAt, priority, weight, assigneeIds } = body

    if (!title || !companyId) {
      return NextResponse.json({ error: 'عنوان و شرکت الزامی است' }, { status: 400 })
    }

    // Verify company access for assigner
    const hasAccess = await hasCompanyAccess(user!.id, companyId)
    if (!hasAccess) {
      return NextResponse.json({ error: 'دسترسی به این شرکت ندارید' }, { status: 403 })
    }

    const task = await db.task.create({
      data: {
        title,
        description,
        companyId,
        createdById: user!.id,
        dueAt: dueAt ? new Date(dueAt) : null,
        priority: priority || 'medium',
        weight: weight || 1,
        status: 'assigned',
        assignments: assigneeIds && assigneeIds.length > 0 ? {
          create: assigneeIds.map((userId: string, index: number) => ({
            userId,
            assignmentType: index === 0 ? 'primary' : 'collaborator',
          })),
        } : undefined,
      },
      include: {
        company: { select: { id: true, name: true, code: true } },
        assignments: { include: { user: { select: { id: true, displayName: true, role: true } } } },
      },
    })

    // Audit log
    await db.auditEvent.create({
      data: {
        actorId: user!.id,
        action: 'create',
        objectType: 'task',
        objectId: task.id,
        occurredAt: new Date(),
        newState: JSON.stringify({ title, companyId, dueAt, priority }),
      },
    })

    // Create notifications for assignees
    if (assigneeIds && assigneeIds.length > 0) {
      await db.notification.createMany({
        data: assigneeIds.map((userId: string) => ({
          userId,
          eventKey: `task-assigned-${task.id}-${userId}-${Date.now()}`,
          type: 'task_assigned',
          title: 'تسک جدید',
          message: `تسک «${title}» به شما ارجاع شد`,
        })),
      })
    }

    return NextResponse.json({ task }, { status: 201 })
  } catch (error) {
    console.error('Create task error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
