import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

export async function GET(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  const { searchParams } = new URL(request.url)
  const companyId = searchParams.get('companyId')

  let where: any = { status: 'active' }
  if (companyId) where.companyId = companyId

  const versions = await db.referenceVersion.findMany({
    where,
    include: {
      company: { select: { id: true, name: true, code: true } },
      uploadedBy: { select: { id: true, displayName: true } },
      fiscalPeriod: { select: { id: true, name: true } },
    },
    orderBy: { createdAt: 'desc' },
    take: 50,
  })

  return NextResponse.json({ versions })
}

export async function POST(request: NextRequest) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response
  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden' }, { status: 403 })
  }

  try {
    const formData = await request.formData()
    const companyId = formData.get('companyId') as string
    const fiscalPeriodId = (formData.get('fiscalPeriodId') as string) || null
    const dateRangeStart = formData.get('dateRangeStart') as string
    const dateRangeEnd = formData.get('dateRangeEnd') as string
    const notes = formData.get('notes') as string
    const file = formData.get('file') as File

    if (!companyId) {
      return NextResponse.json({ error: 'شناسه شرکت الزامی است' }, { status: 400 })
    }

    // Get next version number for this company+period
    const where: any = { companyId }
    if (fiscalPeriodId) where.fiscalPeriodId = fiscalPeriodId
    const lastVersion = await db.referenceVersion.findFirst({
      where,
      orderBy: { versionNumber: 'desc' },
    })
    const versionNumber = (lastVersion?.versionNumber || 0) + 1

    let filePath: string | null = null
    let fileHash: string | null = null
    if (file) {
      const buffer = Buffer.from(await file.arrayBuffer())
      const { createHash } = await import('crypto')
      fileHash = createHash('sha256').update(buffer).digest('hex')
      const uploadDir = '/tmp/acc-office-references'
      const fs = await import('fs/promises')
      await fs.mkdir(uploadDir, { recursive: true })
      const fileName = `${fileHash}-${file.name}`
      filePath = `${uploadDir}/${fileName}`
      await fs.writeFile(filePath, buffer)
    }

    // Mark previous versions as superseded
    if (lastVersion) {
      await db.referenceVersion.updateMany({
        where: { companyId, status: 'active', ...(fiscalPeriodId ? { fiscalPeriodId } : {}) },
        data: { status: 'superseded' },
      })
    }

    const version = await db.referenceVersion.create({
      data: {
        companyId,
        fiscalPeriodId,
        versionNumber,
        uploadedById: user!.id,
        fileHash,
        filePath,
        dateRangeStart: dateRangeStart ? new Date(dateRangeStart) : null,
        dateRangeEnd: dateRangeEnd ? new Date(dateRangeEnd) : null,
        status: 'active',
        notes,
      },
      include: {
        company: { select: { id: true, name: true, code: true } },
        uploadedBy: { select: { id: true, displayName: true } },
      },
    })

    await db.auditEvent.create({
      data: {
        actorId: user!.id,
        action: 'create',
        objectType: 'reference_version',
        objectId: version.id,
        occurredAt: new Date(),
        newState: JSON.stringify({ versionNumber, companyId }),
      },
    })

    return NextResponse.json({ version }, { status: 201 })
  } catch (error) {
    console.error('Create reference error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
