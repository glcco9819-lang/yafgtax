import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

// GET /api/dashboard - manager dashboard stats
export async function GET(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  // Stats
  const totalCompanies = await db.company.count({ where: { isActive: true } })
  const totalUsers = await db.user.count({ where: { isActive: true } })
  const totalTasks = await db.task.count()
  const openTasks = await db.task.count({
    where: { status: { in: ['assigned', 'in_progress', 'submitted', 'reconciling', 'needs_review', 'returned'] } },
  })
  const overdueTasks = await db.task.count({
    where: {
      dueAt: { lt: new Date() },
      status: { notIn: ['approved', 'approved_with_exception', 'rejected', 'cancelled'] },
    },
  })
  const pendingSubmissions = await db.workSubmission.count({
    where: { status: 'received' },
  })

  // Recent submissions
  const recentSubmissions = await db.workSubmission.findMany({
    include: {
      submittedBy: { select: { id: true, displayName: true } },
      task: { select: { id: true, title: true, company: { select: { name: true } } } },
    },
    orderBy: { submittedAt: 'desc' },
    take: 10,
  })

  // Recent decisions
  const recentDecisions = await db.managerDecision.findMany({
    include: {
      reviewer: { select: { id: true, displayName: true } },
      submission: { include: { submittedBy: { select: { displayName: true } }, task: { select: { title: true } } } },
    },
    orderBy: { createdAt: 'desc' },
    take: 10,
  })

  // Notifications
  const notifications = await db.notification.findMany({
    where: { userId: user!.id, isRead: false },
    orderBy: { createdAt: 'desc' },
    take: 20,
  })

  // Recent audit events
  const recentActivity = await db.auditEvent.findMany({
    include: { actor: { select: { id: true, displayName: true, role: true } } },
    orderBy: { occurredAt: 'desc' },
    take: 15,
  })

  return NextResponse.json({
    stats: {
      totalCompanies,
      totalUsers,
      totalTasks,
      openTasks,
      overdueTasks,
      pendingSubmissions,
    },
    recentSubmissions,
    recentDecisions,
    notifications,
    recentActivity,
  })
}
