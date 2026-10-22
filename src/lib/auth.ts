import { createHash, randomBytes } from 'crypto'

// Hash password with salt using SHA-256 (suitable for SQLite/MVP, use bcrypt in production)
export function hashPassword(password: string): string {
  const salt = randomBytes(16).toString('hex')
  const hash = createHash('sha256').update(salt + password).digest('hex')
  return `${salt}:${hash}`
}

export function verifyPassword(password: string, stored: string): boolean {
  const [salt, hash] = stored.split(':')
  if (!salt || !hash) return false
  const computed = createHash('sha256').update(salt + password).digest('hex')
  return hash === computed
}

// Session token (simple JWT-like, NOT for production - use NextAuth in prod)
export function createSessionToken(userId: string, role: string): string {
  const payload = {
    userId,
    role,
    exp: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
  }
  return Buffer.from(JSON.stringify(payload)).toString('base64')
}

export function verifySessionToken(token: string): { userId: string; role: string } | null {
  try {
    const payload = JSON.parse(Buffer.from(token, 'base64').toString())
    if (payload.exp < Date.now()) return null
    return { userId: payload.userId, role: payload.role }
  } catch {
    return null
  }
}

// Get session from request headers
export function getSession(request: Request): { userId: string; role: string } | null {
  const auth = request.headers.get('Authorization')
  if (!auth?.startsWith('Bearer ')) return null
  return verifySessionToken(auth.slice(7))
}
