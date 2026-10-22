import { NextRequest, NextResponse } from 'next/server'
import { db } from './db'
import { getSession } from './auth'

export async function requireAuth(request: NextRequest) {
  const session = getSession(request)
  if (!session) {
    return {
      session: null,
      response: NextResponse.json({ error: 'Unauthorized' }, { status: 401 }),
    }
  }
  const user = await db.user.findUnique({ where: { id: session.userId } })
  if (!user || !user.isActive) {
    return {
      session: null,
      response: NextResponse.json({ error: 'User not found or inactive' }, { status: 401 }),
    }
  }
  return { session, user, response: null }
}

export async function requireRole(request: NextRequest, roles: string[]) {
  const auth = await requireAuth(request)
  if (!auth.session) return auth
  if (!roles.includes(auth.session.role)) {
    return {
      session: null,
      response: NextResponse.json({ error: 'Forbidden' }, { status: 403 }),
    }
  }
  return auth
}

export async function hasCompanyAccess(userId: string, companyId: string): Promise<boolean> {
  // Supervisors and CEOs have access to all companies
  const user = await db.user.findUnique({ where: { id: userId } })
  if (!user) return false
  if (['supervisor', 'ceo', 'admin'].includes(user.role)) return true
  const access = await db.userCompanyAccess.findUnique({
    where: { userId_companyId: { userId, companyId } },
  })
  return !!access
}
