import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { requireAuth } from '@/lib/guards'

// POST /api/submissions/[id]/decision - manager makes decision on submission
export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ id: string }> }
) {
  const { session, user, response } = await requireAuth(request)
  if (!session) return response

  if (!['supervisor', 'ceo', 'admin'].includes(user!.role)) {
    return NextResponse.json({ error: 'Forbidden - نیاز به نقش سرپرست یا مدیر' }, { status: 403 })
  }

  const { id } = await params
  const submission = await db.workSubmission.findUnique({
    where: { id },
    include: { task: true, submittedBy: true },
  })

  if (!submission) {
    return NextResponse.json({ error: 'گزارش کار یافت نشد' }, { status: 404 })
  }

  try {
    const body = await request.json()
    const { decisionType, score, reasonVisible, reasonConfidential, referenceVersionId } = body

    if (!decisionType || !['approved', 'approved_with_exception', 'returned', 'rejected'].includes(decisionType)) {
      return NextResponse.json({ error: 'نوع تصمیم نامعتبر' }, { status: 400 })
    }

    if (score !== undefined && (score < 0 || score > 100)) {
      return NextResponse.json({ error: 'نمره باید بین ۰ تا ۱۰۰ باشد' }, { status: 400 })
    }

    // For return/reject, reasonVisible is required
    if ((decisionType === 'returned' || decisionType === 'rejected') && !reasonVisible) {
      return NextResponse.json({ error: 'دلیل قابل مشاهده برای بازگشت/رد الزامی است' }, { status: 400 })
    }

    const previousState = JSON.stringify({
      status: submission.status,
      submissionScore: submission.submissionScore,
    })

    // Create decision record
    const decision = await db.managerDecision.create({
      data: {
        submissionId: id,
        reviewerId: user!.id,
        decisionType,
        reasonVisible,
        reasonConfidential,
        score,
        referenceVersionId,
      },
      include: {
        reviewer: { select: { id: true, displayName: true, role: true } },
      },
    })

    // Map decision type to submission status
    const statusMap: Record<string, string> = {
      approved: 'approved',
      approved_with_exception: 'approved_with_exception',
      returned: 'returned',
      rejected: 'rejected',
    }

    // Update submission status and score
    const updatedSubmission = await db.workSubmission.update({
      where: { id },
      data: {
        status: statusMap[decisionType],
        submissionScore: score,
        referenceVersionId: referenceVersionId || null,
      },
    })

    // Update task status based on decision
    const taskStatusMap: Record<string, string> = {
      approved: 'approved',
      approved_with_exception: 'approved_with_exception',
      returned: 'returned',
      rejected: 'rejected',
    }

    await db.task.update({
      where: { id: submission.taskId },
      data: { status: taskStatusMap[decisionType] },
    })

    // Audit log
    await db.auditEvent.create({
      data: {
        actorId: user!.id,
        action: decisionType,
        objectType: 'submission',
        objectId: id,
        occurredAt: new Date(),
        previousState,
        newState: JSON.stringify({
          status: statusMap[decisionType],
          score,
        }),
        reason: reasonVisible || reasonConfidential,
      },
    })

    // Notify employee
    await db.notification.create({
      data: {
        userId: submission.submittedById,
        eventKey: `decision-${decision.id}-${Date.now()}`,
        type: 'decision_made',
        title: `تصمیم روی تسک «${submission.task.title}»`,
        message: `وضعیت: ${
          decisionType === 'approved' ? 'تأیید شد' :
          decisionType === 'approved_with_exception' ? 'با ارفاق تأیید شد' :
          decisionType === 'returned' ? 'برای اصلاح بازگشت' :
          'رد شد'
        }${score !== undefined ? ` - نمره: ${score}/۱۰۰` : ''}`,
      },
    })

    return NextResponse.json({
      decision,
      submission: updatedSubmission,
    }, { status: 201 })
  } catch (error) {
    console.error('Decision error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
