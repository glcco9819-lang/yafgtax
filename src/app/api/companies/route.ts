import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

// GET /api/companies - list companies (filtered by user access)
export async function GET(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  // For employees, return only companies they have access to
  // For supervisors/ceo/admin, return all companies
  if (['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    const companies = await db.company.findMany({
      where: { isActive: true },
      include: {
        _count: { select: { tasks: true, userAccess: true } },
      },
      orderBy: { name: 'asc' },
    })
    return NextResponse.json({ companies })
  } else {
    const companies = await db.company.findMany({
      where: {
        isActive: true,
        userAccess: { some: { userId: user!.id } },
      },
      include: {
        _count: { select: { tasks: true } },
      },
      orderBy: { name: 'asc' },
    })
    return NextResponse.json({ companies })
  }
}

// POST /api/companies - create new company (supervisor/ceo/admin only)
export async function POST(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response
  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  try {
    const body = await request.json()
    const { code, name, accountingSoftware } = body

    if (!code || !name) {
      return NextResponse.json({ error: 'کد و نام شرکت الزامی است' }, { status: 400 })
    }

    // Check uniqueness
    const existing = await db.company.findUnique({ where: { code } })
    if (existing) {
      return NextResponse.json({ error: 'کد شرکت قبلاً استفاده شده است' }, { status: 400 })
    }

    const company = await db.company.create({
      data: {
        code,
        name,
        accountingSoftware: accountingSoftware || 'mixed',
      },
    })

    // Audit log
    await db.auditEvent.create({
      data: {
        actorId: user!.id,
        action: 'create',
        objectType: 'company',
        objectId: company.id,
        occurredAt: new Date(),
        newState: JSON.stringify({ code, name, accountingSoftware }),
      },
    })

    return NextResponse.json({ company }, { status: 201 })
  } catch (error) {
    console.error('Create company error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
