import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

export async function GET(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const users = await db.user.findMany({
    select: {
      id: true,
      username: true,
      displayName: true,
      role: true,
      isActive: true,
      createdAt: true,
      _count: { select: { companyAccess: true, assignedTasks: true, submittedWorks: true } },
    },
    orderBy: { displayName: 'asc' },
  })

  return NextResponse.json({ users })
}

export async function POST(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response
  if (!['ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  try {
    const body = await request.json()
    const { username, password, displayName, role } = body

    if (!username || !password || !displayName) {
      return NextResponse.json({ error: 'نام کاربری، رمز و نام الزامی است' }, { status: 400 })
    }

    const existing = await db.user.findUnique({ where: { username } })
    if (existing) {
      return NextResponse.json({ error: 'نام کاربری قبلاً استفاده شده' }, { status: 400 })
    }

    // Hash password using SHA-256 with salt (sufficient for MVP)
    const { hashPassword } = await import('@/lib/auth')
    const passwordHash = hashPassword(password)

    const newUser = await db.user.create({
      data: {
        username,
        passwordHash,
        displayName,
        role: role || 'employee',
      },
    })

    // Audit log
    await db.auditEvent.create({
      data: {
        actorId: user!.id,
        action: 'create',
        objectType: 'user',
        objectId: newUser.id,
        occurredAt: new Date(),
        newState: JSON.stringify({ username, displayName, role }),
      },
    })

    return NextResponse.json({
      user: {
        id: newUser.id,
        username: newUser.username,
        displayName: newUser.displayName,
        role: newUser.role,
      },
    }, { status: 201 })
  } catch (error) {
    console.error('Create user error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
