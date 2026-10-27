import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth, hasCompanyAccess } from '@/lib/guards'
import { createHash } from 'crypto'

// POST /api/tasks/[id]/submit - employee submits work report with Excel file
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  const { id } = await params
  const task = await db.task.findUnique({
    where: { id },
    include: { company: true },
  })

  if (!task) {
    return NextResponse.json({ error: 'تسک یافت نشد' }, { status: 404 })
  }

  // Check if user is assigned to this task
  const assignment = await db.taskAssignment.findUnique({
    where: {
      taskId_userId_assignmentType: {
        taskId: id,
        userId: user!.id,
        assignmentType: 'primary',
      },
    },
  })

  if (!assignment && task.createdById !== user!.id) {
    return NextResponse.json({ error: 'شما به این تسک ارجاع نشده‌اید' }, { status: 403 })
  }

  try {
    const formData = await request.formData()
    const periodStart = formData.get('periodStart') as string
    const periodEnd = formData.get('periodEnd') as string
    const description = formData.get('description') as string
    const file = formData.get('file') as File

    if (!periodStart || !periodEnd) {
      return NextResponse.json({ error: 'بازه زمانی الزامی است' }, { status: 400 })
    }

    let filePath: string | null = null
    let fileHash: string | null = null

    if (file) {
      const buffer = Buffer.from(await file.arrayBuffer())
      fileHash = createHash('sha256').update(buffer).digest('hex')

      // Check if same file already submitted (Idempotency for duplicate file)
      const existing = await db.workSubmission.findFirst({
        where: {
          fileHash,
          submittedById: user!.id,
          taskId: id,
        },
      })
      if (existing) {
        return NextResponse.json({
          error: 'این فایل قبلاً برای همین تسک ثبت شده است',
          submission: existing,
        }, { status: 409 })
      }

      // Store file locally (in MVP, we save with a hashed name)
      const uploadDir = '/tmp/acc-office-uploads'
      const fs = await import('fs/promises')
      await fs.mkdir(uploadDir, { recursive: true })
      const fileName = `${fileHash}-${file.name}`
      filePath = `${uploadDir}/${fileName}`
      await fs.writeFile(filePath, buffer)
    }

    // Create submission
    const submission = await db.workSubmission.create({
      data: {
        taskId: id,
        submittedById: user!.id,
        periodStart: new Date(periodStart),
        periodEnd: new Date(periodEnd),
        description,
        filePath,
        fileHash,
        status: 'received',
      },
      include: {
        submittedBy: { select: { id: true, displayName: true } },
      },
    })

    // Update task status
    await db.task.update({
      where: { id },
      data: { status: 'submitted' },
    })

    // Audit log
    await db.auditEvent.create({
      data: {
        actorId: user!.id,
        action: 'create',
        objectType: 'submission',
        objectId: submission.id,
        occurredAt: new Date(),
        newState: JSON.stringify({
          periodStart,
          periodEnd,
          hasFile: !!file,
          fileHash,
        }),
      },
    })

    // Notify creator/manager
    await db.notification.create({
      data: {
        userId: task.createdById,
        eventKey: `submission-received-${submission.id}-${Date.now()}`,
        type: 'submission_received',
        title: 'گزارش کار جدید',
        message: `گزارش جدید برای تسک «${task.title}» از ${user!.displayName}`,
      },
    })

    return NextResponse.json({ submission }, { status: 201 })
  } catch (error) {
    console.error('Submit work error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
