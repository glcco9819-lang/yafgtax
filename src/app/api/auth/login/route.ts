import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { hashPassword, verifyPassword, createSessionToken } from '@/lib/auth'

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { username, password } = body

    if (!username || !password) {
      return NextResponse.json({ error: 'نام کاربری و رمز عبور الزامی است' }, { status: 400 })
    }

    const user = await db.user.findUnique({ where: { username } })
    if (!user || !user.isActive) {
      return NextResponse.json({ error: 'نام کاربری یا رمز عبور نادرست است' }, { status: 401 })
    }

    if (!verifyPassword(password, user.passwordHash)) {
      return NextResponse.json({ error: 'نام کاربری یا رمز عبور نادرست است' }, { status: 401 })
    }

    // Audit log
    await db.auditEvent.create({
      data: {
        actorId: user.id,
        action: 'login',
        objectType: 'user',
        objectId: user.id,
        occurredAt: new Date(),
      },
    })

    const token = createSessionToken(user.id, user.role)
    return NextResponse.json({
      token,
      user: {
        id: user.id,
        username: user.username,
        displayName: user.displayName,
        role: user.role,
      },
    })
  } catch (error) {
    console.error('Login error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
