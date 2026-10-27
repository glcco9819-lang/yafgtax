import { NextRequest, NextResponse } from 'next/server'
import { db } from '@/lib/db'
import { hashPassword } from '@/lib/auth'

// POST /api/seed - seed initial demo data (only if database is empty)
export async function POST(request: NextRequest) {
  try {
    // Check if already seeded
    const userCount = await db.user.count()
    if (userCount > 0) {
      return NextResponse.json({ 
        message: 'دیتابیس از قبل پر شده است',
        count: userCount,
      })
    }

    // Create users
    const admin = await db.user.create({
      data: {
        username: 'admin',
        passwordHash: hashPassword('admin123'),
        displayName: 'مدیر سیستم',
        role: 'admin',
      },
    })

    const ceo = await db.user.create({
      data: {
        username: 'ceo',
        passwordHash: hashPassword('ceo123'),
        displayName: 'مدیرعامل',
        role: 'ceo',
      },
    })

    const supervisor = await db.user.create({
      data: {
        username: 'supervisor',
        passwordHash: hashPassword('super123'),
        displayName: 'سرپرست حسابداری',
        role: 'supervisor',
      },
    })

    const employees = []
    const employeeNames = ['کارمند یک', 'کارمند دو', 'کارمند سه', 'کارمند چهار', 'کارمند پنج']
    for (let i = 0; i < 5; i++) {
      const emp = await db.user.create({
        data: {
          username: `emp${i + 1}`,
          passwordHash: hashPassword('emp123'),
          displayName: employeeNames[i],
          role: 'employee',
        },
      })
      employees.push(emp)
    }

    // Create companies (5 sample companies for demo, supports up to 5000)
    const companies = []
    const companyData = [
      { code: 'C001', name: 'شرکت توسعه صنعت', software: 'hamkaran' },
      { code: 'C002', name: 'بازرگانی پارس', software: 'sepidar' },
      { code: 'C003', name: 'گروه مهندسی برق', software: 'holo' },
      { code: 'C004', name: 'شرکت بازرگانی آریا', software: 'tandis' },
      { code: 'C005', name: 'صنایع غذایی ماهان', software: 'mixed' },
    ]

    for (const c of companyData) {
      const company = await db.company.create({
        data: {
          code: c.code,
          name: c.name,
          accountingSoftware: c.software,
        },
      })
      companies.push(company)
    }

    // Assign companies to employees (round-robin)
    for (let i = 0; i < companies.length; i++) {
      const company = companies[i]
      const emp = employees[i % employees.length]
      await db.userCompanyAccess.create({
        data: {
          userId: emp.id,
          companyId: company.id,
          permissionSet: 'edit',
        },
      })
    }

    // Create some sample tasks
    const sampleTasks = [
      { title: 'ثبت اسناد ماه مهر ۱۴۰۵', companyId: companies[0].id, weight: 5 },
      { title: 'بستن دفاتر فصل پاییز', companyId: companies[1].id, weight: 8 },
      { title: 'گزارش مالیاتی سه‌ماهه', companyId: companies[2].id, weight: 7 },
      { title: 'تنظیم ترازنامه آزمایشی', companyId: companies[3].id, weight: 6 },
      { title: 'اصلاح اسناد مغایر', companyId: companies[4].id, weight: 4 },
    ]

    const now = new Date()
    for (let i = 0; i < sampleTasks.length; i++) {
      const t = sampleTasks[i]
      const dueAt = new Date(now.getTime() + (i + 1) * 24 * 60 * 60 * 1000)
      const emp = employees[i % employees.length]
      
      await db.task.create({
        data: {
          title: t.title,
          description: `انجام ${t.title} بر اساس دستورالعمل دفتر`,
          companyId: t.companyId,
          createdById: supervisor.id,
          dueAt,
          priority: i < 2 ? 'high' : 'medium',
          weight: t.weight,
          status: 'assigned',
          assignments: {
            create: { userId: emp.id, assignmentType: 'primary' },
          },
        },
      })
    }

    return NextResponse.json({
      message: 'داده‌های اولیه با موفقیت ساخته شد',
      created: {
        users: 8, // admin + ceo + supervisor + 5 employees
        companies: 5,
        tasks: 5,
        accessAssignments: 5,
      },
      credentials: {
        admin: 'admin / admin123',
        ceo: 'ceo / ceo123',
        supervisor: 'supervisor / super123',
        employees: 'emp1 to emp5 / emp123',
      },
    })
  } catch (error) {
    console.error('Seed error:', error)
    return NextResponse.json({ error: 'خطای داخلی سرور' }, { status: 500 })
  }
}
