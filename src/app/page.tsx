'use client'

import { useState, useEffect, useCallback } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Slider } from '@/components/ui/slider'
import { Checkbox } from '@/components/ui/checkbox'
import { Toaster } from '@/components/ui/toaster'
import { useToast } from '@/hooks/use-toast'
import { ScrollArea } from '@/components/ui/scroll-area'
import { 
  Building2, Users, ClipboardList, Calendar, Bell, LogOut, 
  CheckCircle2, AlertCircle, Clock, FileSpreadsheet, Settings,
  UserCircle, TrendingUp, Plus, ChevronLeft, Activity, FileText
} from 'lucide-react'

// ============ Types ============
interface User {
  id: string
  username: string
  displayName: string
  role: 'employee' | 'supervisor' | 'ceo' | 'admin'
}

interface Company {
  id: string
  code: string
  name: string
  accountingSoftware: string
  isActive: boolean
  _count?: { tasks: number; userAccess: number }
}

interface Task {
  id: string
  title: string
  description: string | null
  status: string
  priority: string
  weight: number
  dueAt: string | null
  createdAt: string
  company: { id: string; name: string; code: string }
  createdBy: { id: string; displayName: string; role: string }
  assignments: Array<{
    user: { id: string; displayName: string; role: string }
    assignmentType: string
  }>
  workSubmissions?: WorkSubmission[]
  checklistItems?: Array<{
    id: string
    title: string
    isCompleted: boolean
    assignedTo?: { displayName: string } | null
  }>
}

interface WorkSubmission {
  id: string
  status: string
  submissionScore: number | null
  periodStart: string
  periodEnd: string
  description: string | null
  submittedAt: string
  submittedBy: { id: string; displayName: string }
  decisions?: Array<{
    id: string
    decisionType: string
    score: number | null
    reasonVisible: string | null
    reviewer: { displayName: string }
  }>
}

interface DashboardStats {
  totalCompanies: number
  totalUsers: number
  totalTasks: number
  openTasks: number
  overdueTasks: number
  pendingSubmissions: number
}

interface AuditEvent {
  id: string
  action: string
  objectType: string
  objectId: string | null
  occurredAt: string
  reason: string | null
  actor: { displayName: string; role: string } | null
}

// ============ Helpers ============
const STATUS_LABELS: Record<string, string> = {
  draft: 'پیش‌نویس',
  assigned: 'ارجاع‌شده',
  in_progress: 'در حال انجام',
  submitted: 'تحویل‌شده',
  reconciling: 'در حال تطبیق',
  needs_review: 'نیازمند بررسی',
  returned: 'برگشتی',
  approved: 'تأییدشده',
  approved_with_exception: 'تأیید با ارفاق',
  rejected: 'ردشده',
  cancelled: 'لغوشده',
  received: 'دریافت‌شده',
  processing: 'در حال پردازش',
  verified: 'تأیید شده',
  mismatch_found: 'مغایرت یافت شد',
}

const STATUS_COLORS: Record<string, string> = {
  draft: 'bg-gray-100 text-gray-800',
  assigned: 'bg-blue-100 text-blue-800',
  in_progress: 'bg-amber-100 text-amber-800',
  submitted: 'bg-cyan-100 text-cyan-800',
  reconciling: 'bg-purple-100 text-purple-800',
  needs_review: 'bg-orange-100 text-orange-800',
  returned: 'bg-red-100 text-red-800',
  approved: 'bg-green-100 text-green-800',
  approved_with_exception: 'bg-yellow-100 text-yellow-800',
  rejected: 'bg-red-200 text-red-900',
  cancelled: 'bg-gray-200 text-gray-700',
}

const PRIORITY_LABELS: Record<string, string> = {
  low: 'پایین',
  medium: 'متوسط',
  high: 'بالا',
  critical: 'بحرانی',
}

const ROLE_LABELS: Record<string, string> = {
  employee: 'کارمند',
  supervisor: 'سرپرست',
  ceo: 'مدیرعامل',
  admin: 'مدیر سیستم',
}

const SOFTWARE_LABELS: Record<string, string> = {
  hamkaran: 'همکاران',
  sepidar: 'سپیدار',
  holo: 'هلو',
  tandis: 'تندیس',
  mixed: 'ترکیبی',
}

function formatDate(date: string | null): string {
  if (!date) return '—'
  try {
    return new Date(date).toLocaleDateString('fa-IR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    })
  } catch {
    return date
  }
}

// ============ API helpers ============
async function apiFetch(url: string, options?: RequestInit, token?: string) {
  const headers: Record<string, string> = {
    ...(options?.headers || {}),
  }
  if (token) headers['Authorization'] = `Bearer ${token}`
  if (options?.body && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(url, { ...options, headers })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: 'خطای ناشناخته' }))
    throw new Error(err.error || `HTTP ${res.status}`)
  }
  return res.json()
}

// ============ Main Page ============
export default function Home() {
  const { toast } = useToast()
  const [token, setToken] = useState<string | null>(null)
  const [user, setUser] = useState<User | null>(null)
  const [loginForm, setLoginForm] = useState({ username: '', password: '' })
  const [loginLoading, setLoginLoading] = useState(false)

  // Load token from localStorage
  useEffect(() => {
    const saved = localStorage.getItem('acc_office_token')
    const savedUser = localStorage.getItem('acc_office_user')
    if (saved && savedUser) {
      setToken(saved)
      setUser(JSON.parse(savedUser))
    }
  }, [])

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoginLoading(true)
    try {
      const data = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify(loginForm),
      })
      setToken(data.token)
      setUser(data.user)
      localStorage.setItem('acc_office_token', data.token)
      localStorage.setItem('acc_office_user', JSON.stringify(data.user))
      toast({ title: 'ورود موفق', description: `خوش آمدید ${data.user.displayName}` })
    } catch (err: any) {
      toast({ title: 'خطا در ورود', description: err.message, variant: 'destructive' })
    } finally {
      setLoginLoading(false)
    }
  }

  const handleLogout = () => {
    setToken(null)
    setUser(null)
    localStorage.removeItem('acc_office_token')
    localStorage.removeItem('acc_office_user')
  }

  if (!token || !user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-50 to-slate-200 p-4">
        <Card className="w-full max-w-md">
          <CardHeader className="text-center">
            <div className="mx-auto w-16 h-16 bg-gradient-to-br from-teal-500 to-cyan-700 rounded-2xl flex items-center justify-center mb-3">
              <FileSpreadsheet className="w-9 h-9 text-white" />
            </div>
            <CardTitle className="text-2xl">سامانه مدیریت دفتر حسابداری</CardTitle>
            <CardDescription>برای ادامه وارد حساب خود شوید</CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleLogin} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username">نام کاربری</Label>
                <Input
                  id="username"
                  value={loginForm.username}
                  onChange={e => setLoginForm({ ...loginForm, username: e.target.value })}
                  placeholder="نام کاربری"
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password">رمز عبور</Label>
                <Input
                  id="password"
                  type="password"
                  value={loginForm.password}
                  onChange={e => setLoginForm({ ...loginForm, password: e.target.value })}
                  placeholder="رمز عبور"
                  required
                />
              </div>
              <Button type="submit" disabled={loginLoading} className="w-full bg-teal-600 hover:bg-teal-700">
                {loginLoading ? 'در حال ورود...' : 'ورود'}
              </Button>
              <div className="text-xs text-muted-foreground bg-muted p-3 rounded-md text-center space-y-1">
                <div className="font-semibold">حساب‌های آزمایشی (پس از seed):</div>
                <div>admin / admin123 — مدیر سیستم</div>
                <div>supervisor / super123 — سرپرست</div>
                <div>ceo / ceo123 — مدیرعامل</div>
                <div>emp1 تا emp5 / emp123 — کارمندان</div>
              </div>
              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={async () => {
                  try {
                    await apiFetch('/api/seed', { method: 'POST' })
                    toast({ title: 'داده‌های اولیه ساخته شد', description: 'اکنون می‌توانید وارد شوید' })
                  } catch (err: any) {
                    toast({ title: 'توجه', description: err.message, variant: 'default' })
                  }
                }}
              >
                <Settings className="w-4 h-4 ml-2" />
                ساخت داده‌های اولیه (seed)
              </Button>
            </form>
          </CardContent>
        </Card>
      </div>
    )
  }

  return <Dashboard token={token} user={user} onLogout={handleLogout} />
}

// ============ Dashboard Component ============
function Dashboard({ token, user, onLogout }: { token: string; user: User; onLogout: () => void }) {
  const { toast } = useToast()
  const [tab, setTab] = useState('overview')

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100">
      {/* Header */}
      <header className="bg-white border-b shadow-sm sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 py-3 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-gradient-to-br from-teal-500 to-cyan-700 rounded-xl flex items-center justify-center">
              <FileSpreadsheet className="w-6 h-6 text-white" />
            </div>
            <div>
              <div className="font-bold text-slate-900">سامانه مدیریت دفتر حسابداری</div>
              <div className="text-xs text-slate-500">نسخه MVP ۱.۰</div>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <div className="text-left">
              <div className="font-medium text-sm text-slate-900">{user.displayName}</div>
              <div className="text-xs text-slate-500">{ROLE_LABELS[user.role]}</div>
            </div>
            <div className="w-9 h-9 bg-slate-100 rounded-full flex items-center justify-center">
              <UserCircle className="w-6 h-6 text-slate-600" />
            </div>
            <Button variant="ghost" size="sm" onClick={onLogout}>
              <LogOut className="w-4 h-4 ml-2" />
              خروج
            </Button>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="max-w-7xl mx-auto px-4 py-6">
        <Tabs value={tab} onValueChange={setTab} className="space-y-4">
          <TabsList className="grid grid-cols-2 md:grid-cols-5 gap-1">
            <TabsTrigger value="overview" className="flex items-center gap-2">
              <TrendingUp className="w-4 h-4" />
              <span className="hidden sm:inline">نمای کلی</span>
            </TabsTrigger>
            <TabsTrigger value="tasks" className="flex items-center gap-2">
              <ClipboardList className="w-4 h-4" />
              <span className="hidden sm:inline">تسک‌ها</span>
            </TabsTrigger>
            <TabsTrigger value="companies" className="flex items-center gap-2">
              <Building2 className="w-4 h-4" />
              <span className="hidden sm:inline">شرکت‌ها</span>
            </TabsTrigger>
            {['supervisor', 'ceo', 'admin'].includes(user.role) && (
              <TabsTrigger value="users" className="flex items-center gap-2">
                <Users className="w-4 h-4" />
                <span className="hidden sm:inline">کاربران</span>
              </TabsTrigger>
            )}
            <TabsTrigger value="hr" className="flex items-center gap-2">
              <Calendar className="w-4 h-4" />
              <span className="hidden sm:inline">حضور و مرخصی</span>
            </TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <OverviewTab token={token} user={user} />
          </TabsContent>
          <TabsContent value="tasks">
            <TasksTab token={token} user={user} />
          </TabsContent>
          <TabsContent value="companies">
            <CompaniesTab token={token} user={user} />
          </TabsContent>
          {['supervisor', 'ceo', 'admin'].includes(user.role) && (
            <TabsContent value="users">
              <UsersTab token={token} />
            </TabsContent>
          )}
          <TabsContent value="hr">
            <HRTab token={token} />
          </TabsContent>
        </Tabs>
      </main>

      <footer className="bg-white border-t mt-12 py-4 text-center text-sm text-slate-500">
        <p>© ۱۴۰۵ سامانه مدیریت دفتر حسابداری — نسخه MVP ۱.۰</p>
      </footer>
    </div>
  )
}

// ============ Overview Tab ============
function OverviewTab({ token, user }: { token: string; user: User }) {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [recentSubmissions, setRecentSubmissions] = useState<any[]>([])
  const [recentActivity, setRecentActivity] = useState<AuditEvent[]>([])
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    if (!['supervisor', 'ceo', 'admin'].includes(user.role)) return
    try {
      const data = await apiFetch('/api/dashboard', {}, token)
      setStats(data.stats)
      setRecentSubmissions(data.recentSubmissions)
      setRecentActivity(data.recentActivity)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [token, user])

  useEffect(() => { load() }, [load])

  if (!['supervisor', 'ceo', 'admin'].includes(user.role)) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>خوش آمدید</CardTitle>
          <CardDescription>
            {user.displayName} عزیز، شما با نقش {ROLE_LABELS[user.role]} وارد شده‌اید.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">
            برای مشاهده تسک‌های خود به تب «تسک‌ها» بروید. برای ثبت گزارش کار، فایل اکسل و بازه زمانی را آماده کنید.
          </p>
        </CardContent>
      </Card>
    )
  }

  if (loading) return <div className="text-center py-12 text-muted-foreground">در حال بارگذاری...</div>

  return (
    <div className="space-y-6">
      {/* Stats cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <StatCard icon={<Building2 className="w-5 h-5" />} label="شرکت‌ها" value={stats?.totalCompanies || 0} color="bg-blue-50 text-blue-700" />
        <StatCard icon={<Users className="w-5 h-5" />} label="کاربران" value={stats?.totalUsers || 0} color="bg-purple-50 text-purple-700" />
        <StatCard icon={<ClipboardList className="w-5 h-5" />} label="کل تسک‌ها" value={stats?.totalTasks || 0} color="bg-teal-50 text-teal-700" />
        <StatCard icon={<Clock className="w-5 h-5" />} label="تسک‌های باز" value={stats?.openTasks || 0} color="bg-amber-50 text-amber-700" />
        <StatCard icon={<AlertCircle className="w-5 h-5" />} label="عقب‌افتاده" value={stats?.overdueTasks || 0} color="bg-red-50 text-red-700" />
        <StatCard icon={<FileText className="w-5 h-5" />} label="گزارش‌های جدید" value={stats?.pendingSubmissions || 0} color="bg-cyan-50 text-cyan-700" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent submissions */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <FileText className="w-5 h-5" />
              آخرین گزارش‌های کار
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="max-h-80">
              {recentSubmissions.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground text-sm">گزارشی یافت نشد</div>
              ) : (
                <div className="space-y-2">
                  {recentSubmissions.map((s: any) => (
                    <div key={s.id} className="flex items-center justify-between p-2 hover:bg-muted rounded-md">
                      <div className="flex-1 min-w-0">
                        <div className="font-medium truncate">{s.task?.title}</div>
                        <div className="text-xs text-muted-foreground">
                          {s.submittedBy?.displayName} • {formatDate(s.submittedAt)}
                        </div>
                      </div>
                      <Badge className={STATUS_COLORS[s.status] || 'bg-gray-100'}>
                        {STATUS_LABELS[s.status] || s.status}
                      </Badge>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>

        {/* Recent activity */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg flex items-center gap-2">
              <Activity className="w-5 h-5" />
              فعالیت‌های اخیر
            </CardTitle>
          </CardHeader>
          <CardContent>
            <ScrollArea className="max-h-80">
              {recentActivity.length === 0 ? (
                <div className="text-center py-4 text-muted-foreground text-sm">فعالیتی یافت نشد</div>
              ) : (
                <div className="space-y-2">
                  {recentActivity.map(a => (
                    <div key={a.id} className="flex items-start gap-2 text-sm p-2">
                      <div className="w-2 h-2 bg-teal-500 rounded-full mt-1.5 flex-shrink-0" />
                      <div className="flex-1">
                        <span className="font-medium">{a.actor?.displayName || 'سیستم'}</span>
                        <span className="text-muted-foreground"> — {translateAction(a.action)} ({translateObjectType(a.objectType)})</span>
                        <div className="text-xs text-muted-foreground">{formatDate(a.occurredAt)}</div>
                        {a.reason && <div className="text-xs text-muted-foreground italic mt-1">«{a.reason}»</div>}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </ScrollArea>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

function translateAction(action: string): string {
  const map: Record<string, string> = {
    create: 'ایجاد کرد',
    update: 'به‌روزرسانی کرد',
    delete: 'حذف کرد',
    login: 'وارد شد',
    logout: 'خارج شد',
    approve: 'تأیید کرد',
    reject: 'رد کرد',
    returned: 'برگرداند',
    approved: 'تأیید کرد',
    'approved_with_exception': 'با ارفاق تأیید کرد',
    approved_with_exception: 'با ارفاق تأیید کرد',
  }
  return map[action] || action
}

function translateObjectType(t: string): string {
  const map: Record<string, string> = {
    task: 'تسک',
    submission: 'گزارش کار',
    user: 'کاربر',
    company: 'شرکت',
    leave_request: 'مرخصی',
    reference_version: 'فایل مرجع',
  }
  return map[t] || t
}

function StatCard({ icon, label, value, color }: { icon: React.ReactNode; label: string; value: number; color: string }) {
  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-2xl font-bold">{value}</div>
            <div className="text-xs text-muted-foreground">{label}</div>
          </div>
          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${color}`}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

// ============ Tasks Tab ============
function TasksTab({ token, user }: { token: string; user: User }) {
  const [tasks, setTasks] = useState<Task[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [selectedTask, setSelectedTask] = useState<Task | null>(null)

  const load = useCallback(async () => {
    try {
      const data = await apiFetch('/api/tasks', {}, token)
      setTasks(data.tasks)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { load() }, [load])

  if (loading) return <div className="text-center py-12 text-muted-foreground">در حال بارگذاری...</div>

  if (selectedTask) {
    return <TaskDetail task={selectedTask} token={token} user={user} onBack={() => { setSelectedTask(null); load() }} />
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">تسک‌ها</h2>
        {['supervisor', 'ceo', 'admin'].includes(user.role) && (
          <Button onClick={() => setCreateOpen(true)} className="bg-teal-600 hover:bg-teal-700">
            <Plus className="w-4 h-4 ml-2" />
            تسک جدید
          </Button>
        )}
      </div>

      {tasks.length === 0 ? (
        <Card>
          <CardContent className="text-center py-12 text-muted-foreground">
            <ClipboardList className="w-12 h-12 mx-auto mb-3 opacity-50" />
            <p>هیچ تسکی یافت نشد</p>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-3">
          {tasks.map(t => (
            <Card key={t.id} className="cursor-pointer hover:shadow-md transition-shadow" onClick={() => setSelectedTask(t)}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <Badge variant="outline" className="bg-slate-50">{t.company.code}</Badge>
                      <h3 className="font-semibold truncate">{t.title}</h3>
                    </div>
                    <div className="text-sm text-muted-foreground truncate">{t.company.name}</div>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-muted-foreground">
                      <span>مسئول: {t.assignments.map(a => a.user.displayName).join('، ') || '—'}</span>
                      <span>وزن: {t.weight}</span>
                      <span>اولویت: {PRIORITY_LABELS[t.priority] || t.priority}</span>
                      {t.dueAt && <span>مهلت: {formatDate(t.dueAt)}</span>}
                    </div>
                  </div>
                  <div className="flex flex-col items-end gap-1">
                    <Badge className={STATUS_COLORS[t.status] || 'bg-gray-100'}>
                      {STATUS_LABELS[t.status] || t.status}
                    </Badge>
                    {(t.workSubmissions?.length || 0) > 0 && (
                      <span className="text-xs text-muted-foreground">{t.workSubmissions?.length} گزارش</span>
                    )}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      <CreateTaskDialog open={createOpen} onOpenChange={setCreateOpen} token={token} onCreated={load} />
    </div>
  )
}

function CreateTaskDialog({ open, onOpenChange, token, onCreated }: { open: boolean; onOpenChange: (v: boolean) => void; token: string; onCreated: () => void }) {
  const { toast } = useToast()
  const [form, setForm] = useState({
    title: '',
    description: '',
    companyId: '',
    dueAt: '',
    priority: 'medium',
    weight: 1,
  })
  const [companies, setCompanies] = useState<Company[]>([])
  const [users, setUsers] = useState<any[]>([])
  const [assigneeIds, setAssigneeIds] = useState<string[]>([])
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    if (open) {
      apiFetch('/api/companies', {}, token).then(d => setCompanies(d.companies)).catch(() => {})
      apiFetch('/api/users', {}, token).then(d => setUsers(d.users)).catch(() => {})
    }
  }, [open, token])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    try {
      await apiFetch('/api/tasks', {
        method: 'POST',
        body: JSON.stringify({ ...form, dueAt: form.dueAt || undefined, assigneeIds }),
      }, token)
      toast({ title: 'تسک ایجاد شد' })
      setForm({ title: '', description: '', companyId: '', dueAt: '', priority: 'medium', weight: 1 })
      setAssigneeIds([])
      onOpenChange(false)
      onCreated()
    } catch (err: any) {
      toast({ title: 'خطا', description: err.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>ایجاد تسک جدید</DialogTitle>
          <DialogDescription>تسک به کارمندان انتخاب‌شده ارجاع داده می‌شود</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-1.5">
            <Label htmlFor="title">عنوان *</Label>
            <Input id="title" value={form.title} onChange={e => setForm({ ...form, title: e.target.value })} required />
          </div>
          <div className="space-y-1.5">
            <Label htmlFor="desc">توضیحات</Label>
            <Textarea id="desc" value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>شرکت *</Label>
              <Select value={form.companyId} onValueChange={v => setForm({ ...form, companyId: v })}>
                <SelectTrigger><SelectValue placeholder="انتخاب شرکت" /></SelectTrigger>
                <SelectContent>
                  {companies.map(c => (
                    <SelectItem key={c.id} value={c.id}>{c.name} ({c.code})</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>مهلت انجام</Label>
              <Input type="date" value={form.dueAt} onChange={e => setForm({ ...form, dueAt: e.target.value })} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>اولویت</Label>
              <Select value={form.priority} onValueChange={v => setForm({ ...form, priority: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="low">پایین</SelectItem>
                  <SelectItem value="medium">متوسط</SelectItem>
                  <SelectItem value="high">بالا</SelectItem>
                  <SelectItem value="critical">بحرانی</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>وزن (۱-۱۰): {form.weight}</Label>
              <Slider
                value={[form.weight]}
                min={1}
                max={10}
                step={1}
                onValueChange={v => setForm({ ...form, weight: v[0] })}
              />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>مسئولان</Label>
            <div className="border rounded-md p-3 max-h-32 overflow-y-auto space-y-2">
              {users.filter(u => u.role === 'employee').map(u => (
                <label key={u.id} className="flex items-center gap-2 cursor-pointer">
                  <Checkbox
                    checked={assigneeIds.includes(u.id)}
                    onCheckedChange={(checked) => {
                      if (checked) setAssigneeIds([...assigneeIds, u.id])
                      else setAssigneeIds(assigneeIds.filter(id => id !== u.id))
                    }}
                  />
                  <span className="text-sm">{u.displayName}</span>
                </label>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
            <Button type="submit" disabled={loading} className="bg-teal-600 hover:bg-teal-700">
              {loading ? 'در حال ایجاد...' : 'ایجاد تسک'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function TaskDetail({ task, token, user, onBack }: { task: Task; token: string; user: User; onBack: () => void }) {
  const [submitOpen, setSubmitOpen] = useState(false)
  const [decisionOpen, setDecisionOpen] = useState(false)
  const [currentSubmission, setCurrentSubmission] = useState<WorkSubmission | null>(null)
  const [submissions, setSubmissions] = useState<WorkSubmission[]>(task.workSubmissions || [])

  return (
    <div className="space-y-4">
      <Button variant="ghost" onClick={onBack} className="mb-2">
        <ChevronLeft className="w-4 h-4 ml-2" />
        بازگشت به فهرست
      </Button>

      <Card>
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline">{task.company.code}</Badge>
                <Badge className={STATUS_COLORS[task.status]}>{STATUS_LABELS[task.status]}</Badge>
              </div>
              <CardTitle className="text-xl">{task.title}</CardTitle>
              <CardDescription>{task.company.name}</CardDescription>
            </div>
            <div className="text-left text-sm">
              <div className="text-muted-foreground">اولویت: {PRIORITY_LABELS[task.priority]}</div>
              <div className="text-muted-foreground">وزن: {task.weight}</div>
              {task.dueAt && <div className="text-muted-foreground">مهلت: {formatDate(task.dueAt)}</div>}
            </div>
          </div>
        </CardHeader>
        {task.description && (
          <CardContent>
            <div className="text-sm text-muted-foreground whitespace-pre-wrap">{task.description}</div>
          </CardContent>
        )}
      </Card>

      {/* Submissions section */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-lg">گزارش‌های کار</CardTitle>
          {user.role === 'employee' && (
            <Button onClick={() => setSubmitOpen(true)} size="sm" className="bg-teal-600 hover:bg-teal-700">
              <Plus className="w-4 h-4 ml-2" />
              ثبت گزارش کار
            </Button>
          )}
        </CardHeader>
        <CardContent>
          {submissions.length === 0 ? (
            <div className="text-center py-6 text-muted-foreground text-sm">هنوز گزارشی ثبت نشده</div>
          ) : (
            <div className="space-y-3">
              {submissions.map(s => (
                <div key={s.id} className="border rounded-md p-3">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <Badge className={STATUS_COLORS[s.status]}>{STATUS_LABELS[s.status] || s.status}</Badge>
                        {s.submissionScore !== null && (
                          <Badge variant="outline">نمره: {s.submissionScore}/۱۰۰</Badge>
                        )}
                      </div>
                      <div className="text-sm mt-1">
                        <div>بازه: {formatDate(s.periodStart)} تا {formatDate(s.periodEnd)}</div>
                        <div className="text-muted-foreground">ثبت توسط: {s.submittedBy.displayName}</div>
                        <div className="text-muted-foreground">زمان: {formatDate(s.submittedAt)}</div>
                        {s.description && <div className="mt-1 text-sm">{s.description}</div>}
                      </div>
                      {s.decisions && s.decisions.length > 0 && (
                        <div className="mt-2 border-t pt-2 space-y-1">
                          {s.decisions.map(d => (
                            <div key={d.id} className="text-xs bg-muted p-2 rounded">
                              <div className="font-medium">
                                تصمیم: {STATUS_LABELS[d.decisionType] || d.decisionType}
                                {d.score !== null && ` - نمره: ${d}/۱۰۰`}
                                <span className="text-muted-foreground"> — توسط {d.reviewer.displayName}</span>
                              </div>
                              {d.reasonVisible && <div className="mt-1">دلیل قابل مشاهده: {d.reasonVisible}</div>}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                    {['supervisor', 'ceo', 'admin'].includes(user.role) && s.status === 'received' && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => { setCurrentSubmission(s); setDecisionOpen(true) }}
                      >
                        تصمیم‌گیری
                      </Button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      <SubmitWorkDialog
        open={submitOpen}
        onOpenChange={setSubmitOpen}
        taskId={task.id}
        token={token}
        onSubmitted={() => {
          // Reload submissions by re-fetching task detail
          apiFetch(`/api/tasks/${task.id}`, {}, token).then(d => {
            setSubmissions(d.task.workSubmissions || [])
          }).catch(() => {})
          setSubmitOpen(false)
        }}
      />

      {currentSubmission && (
        <DecisionDialog
          open={decisionOpen}
          onOpenChange={setDecisionOpen}
          submission={currentSubmission}
          token={token}
          onDecided={() => {
            apiFetch(`/api/tasks/${task.id}`, {}, token).then(d => {
              setSubmissions(d.task.workSubmissions || [])
              setCurrentSubmission(null)
            }).catch(() => {})
            setDecisionOpen(false)
          }}
        />
      )}
    </div>
  )
}

function SubmitWorkDialog({ open, onOpenChange, taskId, token, onSubmitted }: any) {
  const { toast } = useToast()
  const [form, setForm] = useState({ periodStart: '', periodEnd: '', description: '' })
  const [file, setFile] = useState<File | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!form.periodStart || !form.periodEnd) {
      toast({ title: 'بازه زمانی الزامی است', variant: 'destructive' })
      return
    }
    setLoading(true)
    try {
      const formData = new FormData()
      formData.append('periodStart', form.periodStart)
      formData.append('periodEnd', form.periodEnd)
      formData.append('description', form.description)
      if (file) formData.append('file', file)

      const res = await fetch(`/api/tasks/${taskId}/submit`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` },
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({ error: 'خطا' }))
        throw new Error(err.error)
      }
      toast({ title: 'گزارش کار ثبت شد' })
      setForm({ periodStart: '', periodEnd: '', description: '' })
      setFile(null)
      onSubmitted()
    } catch (err: any) {
      toast({ title: 'خطا', description: err.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>ثبت گزارش کار</DialogTitle>
          <DialogDescription>فایل اکسل اسناد و بازه زمانی را وارد کنید</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1.5">
              <Label>از تاریخ *</Label>
              <Input type="date" value={form.periodStart} onChange={e => setForm({ ...form, periodStart: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label>تا تاریخ *</Label>
              <Input type="date" value={form.periodEnd} onChange={e => setForm({ ...form, periodEnd: e.target.value })} required />
            </div>
          </div>
          <div className="space-y-1.5">
            <Label>توضیحات</Label>
            <Textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })} rows={2} />
          </div>
          <div className="space-y-1.5">
            <Label>فایل اکسل اسناد (اختیاری)</Label>
            <Input
              type="file"
              accept=".xlsx,.xls,.csv"
              onChange={e => setFile(e.target.files?.[0] || null)}
            />
            <div className="text-xs text-muted-foreground">
              قالب: شناسه ردیف، شماره سند، تاریخ، کد کل، معین، تفصیل، شرح، بدهکار، بستانکار
            </div>
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
            <Button type="submit" disabled={loading} className="bg-teal-600 hover:bg-teal-700">
              {loading ? 'در حال ثبت...' : 'ثبت گزارش'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

function DecisionDialog({ open, onOpenChange, submission, token, onDecided }: any) {
  const { toast } = useToast()
  const [decisionType, setDecisionType] = useState<'approved' | 'approved_with_exception' | 'returned' | 'rejected'>('approved')
  const [score, setScore] = useState(80)
  const [reasonVisible, setReasonVisible] = useState('')
  const [reasonConfidential, setReasonConfidential] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if ((decisionType === 'returned' || decisionType === 'rejected') && !reasonVisible) {
      toast({ title: 'دلیل قابل مشاهده برای بازگشت/رد الزامی است', variant: 'destructive' })
      return
    }
    setLoading(true)
    try {
      await apiFetch(`/api/submissions/${submission.id}/decision`, {
        method: 'POST',
        body: JSON.stringify({
          decisionType,
          score,
          reasonVisible: reasonVisible || null,
          reasonConfidential: reasonConfidential || null,
        }),
      }, token)
      toast({ title: 'تصمیم ثبت شد' })
      onDecided()
    } catch (err: any) {
      toast({ title: 'خطا', description: err.message, variant: 'destructive' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>تصمیم روی گزارش کار</DialogTitle>
          <DialogDescription>نمره ۰-۱۰۰ مستقل از نوع تصمیم است</DialogDescription>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="space-y-3">
          <div className="space-y-2">
            <Label>نوع تصمیم *</Label>
            <Select value={decisionType} onValueChange={(v: any) => setDecisionType(v)}>
              <SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>
                <SelectItem value="approved">تأیید عادی</SelectItem>
                <SelectItem value="approved_with_exception">تأیید با ارفاق</SelectItem>
                <SelectItem value="returned">بازگشت برای اصلاح</SelectItem>
                <SelectItem value="rejected">رد نهایی</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>نمره: {score}/۱۰۰</Label>
            <Slider value={[score]} min={0} max={100} step={1} onValueChange={v => setScore(v[0])} />
          </div>
          <div className="space-y-1.5">
            <Label>دلیل قابل مشاهده (برای کارمند)</Label>
            <Textarea
              value={reasonVisible}
              onChange={e => setReasonVisible(e.target.value)}
              rows={2}
              placeholder={decisionType === 'returned' || decisionType === 'rejected' ? 'الزامی برای بازگشت/رد' : 'اختیاری'}
            />
          </div>
          <div className="space-y-1.5">
            <Label>یادداشت محرمانه مدیر</Label>
            <Textarea
              value={reasonConfidential}
              onChange={e => setReasonConfidential(e.target.value)}
              rows={2}
              placeholder="فقط مدیر می‌بیند"
            />
          </div>
          <DialogFooter>
            <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>انصراف</Button>
            <Button type="submit" disabled={loading} className="bg-teal-600 hover:bg-teal-700">
              {loading ? 'در حال ثبت...' : 'ثبت تصمیم'}
            </Button>
          </DialogFooter>
        </form>
      </DialogContent>
    </Dialog>
  )
}

// ============ Companies Tab ============
function CompaniesTab({ token, user }: { token: string; user: User }) {
  const [companies, setCompanies] = useState<Company[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({ code: '', name: '', accountingSoftware: 'mixed' })

  const load = useCallback(async () => {
    try {
      const data = await apiFetch('/api/companies', {}, token)
      setCompanies(data.companies)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { load() }, [load])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiFetch('/api/companies', {
        method: 'POST',
        body: JSON.stringify(form),
      }, token)
      setForm({ code: '', name: '', accountingSoftware: 'mixed' })
      setCreateOpen(false)
      load()
    } catch (err: any) {
      console.error(err)
    }
  }

  if (loading) return <div className="text-center py-12 text-muted-foreground">در حال بارگذاری...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">شرکت‌ها</h2>
        {['supervisor', 'ceo', 'admin'].includes(user.role) && (
          <Button onClick={() => setCreateOpen(true)} className="bg-teal-600 hover:bg-teal-700">
            <Plus className="w-4 h-4 ml-2" />
            شرکت جدید
          </Button>
        )}
      </div>

      <Card>
        <CardContent className="p-0">
          {companies.length === 0 ? (
            <div className="text-center py-12 text-muted-foreground">
              <Building2 className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>شرکتی یافت نشد</p>
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>کد</TableHead>
                  <TableHead>نام</TableHead>
                  <TableHead>نرم‌افزار حسابداری</TableHead>
                  <TableHead>تعداد تسک‌ها</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {companies.map(c => (
                  <TableRow key={c.id}>
                    <TableCell className="font-mono">{c.code}</TableCell>
                    <TableCell className="font-medium">{c.name}</TableCell>
                    <TableCell>
                      <Badge variant="outline">{SOFTWARE_LABELS[c.accountingSoftware] || c.accountingSoftware}</Badge>
                    </TableCell>
                    <TableCell>{c._count?.tasks || 0}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>ایجاد شرکت جدید</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="space-y-1.5">
              <Label>کد شرکت *</Label>
              <Input value={form.code} onChange={e => setForm({ ...form, code: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label>نام شرکت *</Label>
              <Input value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label>نرم‌افزار حسابداری</Label>
              <Select value={form.accountingSoftware} onValueChange={v => setForm({ ...form, accountingSoftware: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="hamkaran">همکاران</SelectItem>
                  <SelectItem value="sepidar">سپیدار</SelectItem>
                  <SelectItem value="holo">هلو</SelectItem>
                  <SelectItem value="tandis">تندیس</SelectItem>
                  <SelectItem value="mixed">ترکیبی</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>انصراف</Button>
              <Button type="submit" className="bg-teal-600 hover:bg-teal-700">ایجاد</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ============ Users Tab ============
function UsersTab({ token }: { token: string }) {
  const [users, setUsers] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({ username: '', password: '', displayName: '', role: 'employee' })

  const load = useCallback(async () => {
    try {
      const data = await apiFetch('/api/users', {}, token)
      setUsers(data.users)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { load() }, [load])

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiFetch('/api/users', {
        method: 'POST',
        body: JSON.stringify(form),
      }, token)
      setForm({ username: '', password: '', displayName: '', role: 'employee' })
      setCreateOpen(false)
      load()
    } catch (err: any) {
      console.error(err)
    }
  }

  if (loading) return <div className="text-center py-12 text-muted-foreground">در حال بارگذاری...</div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold">کاربران</h2>
        <Button onClick={() => setCreateOpen(true)} className="bg-teal-600 hover:bg-teal-700">
          <Plus className="w-4 h-4 ml-2" />
          کاربر جدید
        </Button>
      </div>

      <Card>
        <CardContent className="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>نام نمایشی</TableHead>
                <TableHead>نام کاربری</TableHead>
                <TableHead>نقش</TableHead>
                <TableHead>وضعیت</TableHead>
                <TableHead>شرکت‌ها</TableHead>
                <TableHead>تسک‌های ارجاعی</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {users.map(u => (
                <TableRow key={u.id}>
                  <TableCell className="font-medium">{u.displayName}</TableCell>
                  <TableCell className="font-mono">{u.username}</TableCell>
                  <TableCell>
                    <Badge variant="outline">{ROLE_LABELS[u.role] || u.role}</Badge>
                  </TableCell>
                  <TableCell>
                    <Badge className={u.isActive ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}>
                      {u.isActive ? 'فعال' : 'غیرفعال'}
                    </Badge>
                  </TableCell>
                  <TableCell>{u._count?.companyAccess || 0}</TableCell>
                  <TableCell>{u._count?.assignedTasks || 0}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>ایجاد کاربر جدید</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleCreate} className="space-y-3">
            <div className="space-y-1.5">
              <Label>نام نمایشی *</Label>
              <Input value={form.displayName} onChange={e => setForm({ ...form, displayName: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label>نام کاربری *</Label>
              <Input value={form.username} onChange={e => setForm({ ...form, username: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label>رمز عبور *</Label>
              <Input type="password" value={form.password} onChange={e => setForm({ ...form, password: e.target.value })} required />
            </div>
            <div className="space-y-1.5">
              <Label>نقش</Label>
              <Select value={form.role} onValueChange={v => setForm({ ...form, role: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="employee">کارمند</SelectItem>
                  <SelectItem value="supervisor">سرپرست</SelectItem>
                  <SelectItem value="ceo">مدیرعامل</SelectItem>
                  <SelectItem value="admin">مدیر سیستم</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>انصراف</Button>
              <Button type="submit" className="bg-teal-600 hover:bg-teal-700">ایجاد</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ============ HR Tab ============
function HRTab({ token }: { token: string }) {
  const { toast } = useToast()
  const [leaveRequests, setLeaveRequests] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [form, setForm] = useState({ startAt: '', endAt: '', reason: '', leaveType: 'personal' })
  const [todayAttendance, setTodayAttendance] = useState<{ check_in?: any; check_out?: any }>({})

  const load = useCallback(async () => {
    try {
      const data = await apiFetch('/api/leave-requests', {}, token)
      setLeaveRequests(data.requests)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }, [token])

  useEffect(() => { load() }, [load])

  const handleCheckIn = async () => {
    try {
      const data = await apiFetch('/api/attendance/check-in', { method: 'POST' }, token)
      setTodayAttendance({ ...todayAttendance, check_in: data.record })
      toast({ title: 'ورود ثبت شد' })
    } catch (err: any) {
      toast({ title: 'خطا', description: err.message, variant: 'destructive' })
    }
  }

  const handleCheckOut = async () => {
    try {
      const data = await apiFetch('/api/attendance/check-out', { method: 'POST' }, token)
      setTodayAttendance({ ...todayAttendance, check_out: data.record })
      toast({ title: 'خروج ثبت شد' })
    } catch (err: any) {
      toast({ title: 'خطا', description: err.message, variant: 'destructive' })
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      await apiFetch('/api/leave-requests', {
        method: 'POST',
        body: JSON.stringify(form),
      }, token)
      setForm({ startAt: '', endAt: '', reason: '', leaveType: 'personal' })
      setCreateOpen(false)
      load()
      toast({ title: 'درخواست مرخصی ثبت شد' })
    } catch (err: any) {
      toast({ title: 'خطا', description: err.message, variant: 'destructive' })
    }
  }

  if (loading) return <div className="text-center py-12 text-muted-foreground">در حال بارگذاری...</div>

  return (
    <div className="space-y-4">
      <h2 className="text-2xl font-bold">حضور و غیاب و مرخصی</h2>

      {/* Attendance section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            <Clock className="w-5 h-5" />
            ثبت ورود و خروج
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-3">
            <Button onClick={handleCheckIn} className="bg-green-600 hover:bg-green-700">
              <CheckCircle2 className="w-4 h-4 ml-2" />
              ثبت ورود
            </Button>
            <Button onClick={handleCheckOut} variant="outline" className="border-red-200 text-red-700 hover:bg-red-50">
              <LogOut className="w-4 h-4 ml-2" />
              ثبت خروج
            </Button>
          </div>
          <div className="mt-3 text-sm text-muted-foreground">
            برای امروز: {todayAttendance.check_in ? `ورود: ${formatDate(todayAttendance.check_in.eventTime)}` : 'ورود ثبت نشده'} 
            {' • '}
            {todayAttendance.check_out ? `خروج: ${formatDate(todayAttendance.check_out.eventTime)}` : 'خروج ثبت نشده'}
          </div>
        </CardContent>
      </Card>

      {/* Leave requests */}
      <Card>
        <CardHeader className="flex-row items-center justify-between">
          <CardTitle className="text-lg flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            درخواست‌های مرخصی
          </CardTitle>
          <Button onClick={() => setCreateOpen(true)} size="sm" className="bg-teal-600 hover:bg-teal-700">
            <Plus className="w-4 h-4 ml-2" />
            درخواست جدید
          </Button>
        </CardHeader>
        <CardContent>
          {leaveRequests.length === 0 ? (
            <div className="text-center py-6 text-muted-foreground text-sm">درخواستی یافت نشد</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>از</TableHead>
                  <TableHead>تا</TableHead>
                  <TableHead>نوع</TableHead>
                  <TableHead>دلیل</TableHead>
                  <TableHead>وضعیت</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {leaveRequests.map(r => (
                  <TableRow key={r.id}>
                    <TableCell>{formatDate(r.startAt)}</TableCell>
                    <TableCell>{formatDate(r.endAt)}</TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {r.leaveType === 'personal' ? 'شخصی' : r.leaveType === 'sick' ? 'بیماری' : r.leaveType === 'emergency' ? 'اضطراری' : 'استحقاقی'}
                      </Badge>
                    </TableCell>
                    <TableCell className="max-w-xs truncate">{r.reason}</TableCell>
                    <TableCell>
                      <Badge className={
                        r.status === 'approved' ? 'bg-green-100 text-green-800' :
                        r.status === 'rejected' ? 'bg-red-100 text-red-800' :
                        'bg-amber-100 text-amber-800'
                      }>
                        {r.status === 'approved' ? 'تأیید شد' : r.status === 'rejected' ? 'رد شد' : 'در انتظار'}
                      </Badge>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Dialog open={createOpen} onOpenChange={setCreateOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>درخواست مرخصی جدید</DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label>از تاریخ *</Label>
                <Input type="date" value={form.startAt} onChange={e => setForm({ ...form, startAt: e.target.value })} required />
              </div>
              <div className="space-y-1.5">
                <Label>تا تاریخ *</Label>
                <Input type="date" value={form.endAt} onChange={e => setForm({ ...form, endAt: e.target.value })} required />
              </div>
            </div>
            <div className="space-y-1.5">
              <Label>نوع مرخصی</Label>
              <Select value={form.leaveType} onValueChange={v => setForm({ ...form, leaveType: v })}>
                <SelectTrigger><SelectValue /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="personal">شخصی</SelectItem>
                  <SelectItem value="sick">بیماری</SelectItem>
                  <SelectItem value="emergency">اضطراری</SelectItem>
                  <SelectItem value="vacation">استحقاقی</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1.5">
              <Label>دلیل *</Label>
              <Textarea value={form.reason} onChange={e => setForm({ ...form, reason: e.target.value })} rows={2} required />
            </div>
            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => setCreateOpen(false)}>انصراف</Button>
              <Button type="submit" className="bg-teal-600 hover:bg-teal-700">ثبت درخواست</Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}
