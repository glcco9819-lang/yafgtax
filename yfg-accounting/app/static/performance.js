const performanceCategories={ACCOUNTING:'عملیات حسابداری',RECONCILIATION:'تطبیق و کنترل اسناد',CLIENT_SERVICE:'پیگیری مشتری',ADMINISTRATION:'امور اداری',OTHER:'سایر'};

const PERF_ISSUE_LABELS = {
  MISSING_FROM_REFERENCE: 'در مرجع نیست',
  DEBIT_MISMATCH: 'اختلاف بدهکار',
  CREDIT_MISMATCH: 'اختلاف بستانکار',
  DATE_MISMATCH: 'اختلاف تاریخ',
  ACCOUNT_MISMATCH: 'اختلاف حساب',
  DESCRIPTION_MISMATCH: 'اختلاف شرح',
  DUPLICATE: 'ردیف تکراری',
  OUT_OF_RANGE: 'خارج از بازه',
};

const PERF_ISSUE_COLORS = {
  MISSING_FROM_REFERENCE: '#fee2e2',
  DEBIT_MISMATCH: '#fed7aa',
  CREDIT_MISMATCH: '#fed7aa',
  DATE_MISMATCH: '#fef3c7',
  ACCOUNT_MISMATCH: '#fef3c7',
  DESCRIPTION_MISMATCH: '#e0f2fe',
  DUPLICATE: '#f3e8ff',
  OUT_OF_RANGE: '#fee2e2',
};

async function renderPerformanceEntries(){
  const rows = await api('/performance-entries');
  state.performanceEntries = rows;
  const isManager = ['ADMIN','CEO'].includes(state.me.role);
  const pending = rows.filter(r => r.status === 'PENDING').length;
  const totalMinutes = rows.reduce((sum, r) => sum + Number(r.duration_minutes || 0), 0);
  // Fetch companies for the dropdown (available to all users with company access)
  let companies = [];
  try { companies = await api('/companies'); } catch(e) { companies = []; }
  state.yfgCompanies = companies;
  const action = head('ثبت عملکرد', 'فعالیت روزانه و زمان صرف‌شده را مستقل از ماژول تسک ثبت کنید.', `<button class="btn primary" data-action="new-performance">＋ ثبت عملکرد</button>`);
  const cards = `<div class="stats-grid"><article class="stat-card"><div class="stat-top">گزارش‌ها</div><div class="stat-value">${num(rows.length)}</div><div class="stat-caption">در فهرست قابل مشاهده</div></article><article class="stat-card"><div class="stat-top">در انتظار بررسی</div><div class="stat-value">${num(pending)}</div><div class="stat-caption">نیازمند اقدام مدیر</div></article><article class="stat-card"><div class="stat-top">زمان ثبت‌شده</div><div class="stat-value">${num(Math.round(totalMinutes / 60 * 10) / 10)} <small>ساعت</small></div><div class="stat-caption">مجموع همین فهرست</div></article></div>`;

  const priorityLabel = {NORMAL:'عادی', IMPORTANT:'مهم', CRITICAL:'خیلی مهم'};
  const table = rows.length ? `<div class="table-card"><table class="data-table"><thead><tr>
    ${isManager ? '<th>کارمند</th>' : ''}
    <th>تاریخ</th><th>شرکت</th><th>نوع</th><th>شرح فعالیت</th><th>زمان</th><th>اولویت</th><th>مهلت</th><th>پیشرفت</th>
    <th>وضعیت</th><th>فایل اکسل</th><th>یادداشت مدیر</th><th></th>
  </tr></thead><tbody>
    ${rows.map(r => `
      <tr>
        ${isManager ? `<td>${esc(r.user_name || '—')}</td>` : ''}
        <td>${esc(r.work_date)}</td>
        <td>${esc(r.company_name || '—')}</td>
        <td>${esc(performanceCategories[r.category] || r.category)}</td>
        <td><b>${esc(r.title)}</b>${r.description ? `<small class="muted block">${esc(r.description)}</small>` : ''}${r.fiscal_period ? `<small class="muted block">دوره: ${esc(r.fiscal_period)}</small>` : ''}</td>
        <td>${num(r.duration_minutes)} دقیقه</td>
        <td><span class="tag">${esc(priorityLabel[r.priority] || r.priority || 'عادی')}</span>${r.weight > 1 ? ` <small style="color:#64748b;">وزن ${num(r.weight)}</small>` : ''}</td>
        <td>${esc(r.due_date || '—')}</td>
        <td>
          <div style="display:flex;align-items:center;gap:4px;">
            <div style="width:50px;height:5px;background:#eef2f3;border-radius:3px;overflow:hidden;">
              <div style="width:${Math.min(100, r.progress || 0)}%;height:100%;background:#0b8f89;"></div>
            </div>
            <small>${num(r.progress || 0)}٪</small>
          </div>
        </td>
        <td>${statusTag(r.status)}</td>
        <td><button class="btn soft small" data-action="perf-files" data-id="${esc(r.id)}">📁 فایل‌ها</button></td>
        <td>${r.review_note ? esc(r.review_note) : '—'}</td>
        <td>
          <div class="table-actions">
            ${r.user_id === state.me.id && r.status !== 'APPROVED' ? `<button class="btn soft small" data-action="edit-performance" data-id="${esc(r.id)}">ویرایش</button>` : ''}
            ${isManager && r.user_id !== state.me.id && r.status !== 'APPROVED' ? `<button class="btn soft small" data-action="review-performance" data-id="${esc(r.id)}">بررسی</button>` : ''}
            <button class="btn soft small" data-action="perf-files" data-id="${esc(r.id)}">📁 فایل‌ها</button>
          </div>
        </td>
      </tr>
    `).join('')}
  </tbody></table></div>` : empty('هنوز عملکردی ثبت نشده است', 'برای ثبت اولین فعالیت، دکمهٔ «ثبت عملکرد» را بزنید.');

  $('#view-performance-entries').innerHTML = action + cards + `<div class="panel"><div class="panel-head"><div><h3>${isManager ? 'گزارش‌های عملکرد تیم' : 'عملکردهای من'}</h3><p>${isManager ? 'گزارش‌های کارکنان را بررسی کنید؛ هر کاربر فقط گزارش خودش را ویرایش می‌کند.' : 'گزارش‌های ثبت‌شده و نتیجهٔ بررسی مدیر را پیگیری کنید.'}</p></div><span class="tag">ماژول مستقل</span></div>${table}</div>`;
}

function openPerformanceForm(entryId = null){
  const existing = state.performanceEntries.find(x => x.id === entryId);
  const today = new Intl.DateTimeFormat('fa-IR-u-ca-persian', {year:'numeric', month:'2-digit', day:'2-digit'}).format(new Date()).replaceAll('-', '/');
  const companies = state.yfgCompanies || [];
  const companyOptions = companies.map(c => `<option value="${esc(c.id)}" ${existing?.company_id === c.id ? 'selected' : ''}>${esc(c.name)}</option>`).join('');
  const priorityOptions = [['NORMAL','عادی'],['IMPORTANT','مهم'],['CRITICAL','خیلی مهم']].map(([key, label]) =>
    `<option value="${key}" ${existing?.priority === key ? 'selected' : ''}>${label}</option>`).join('');
  const form = modal(existing ? 'ویرایش ثبت عملکرد' : 'ثبت عملکرد روزانه', 'فعالیت را با تاریخ شمسی و زمان صرف‌شده ثبت کنید. می‌توانید شرکت، دوره مالی، اولویت و مهلت را هم مشخص کنید.', `<form id="performanceEntryForm" class="stack">
    <div class="form-grid">
      <label>تاریخ شمسی<input name="work_date" required maxlength="12" placeholder="۱۴۰۵/۰۷/۲۷" value="${esc(existing?.work_date || today)}"></label>
      <label>نوع عملکرد<select name="category" required>${Object.entries(performanceCategories).map(([key, label]) => `<option value="${key}" ${existing?.category === key ? 'selected' : ''}>${label}</option>`).join('')}</select></label>
      <label class="wide-field">عنوان فعالیت<input name="title" required minlength="2" maxlength="120" placeholder="مثلاً بررسی اسناد شرکت الف" value="${esc(existing?.title || '')}"></label>
      <label>مدت زمان (دقیقه)<input name="duration_minutes" type="number" required min="1" max="1440" step="5" value="${esc(existing?.duration_minutes || 60)}"></label>
      <label>شرکت (اختیاری)<select name="company_id"><option value="">— بدون شرکت —</option>${companyOptions}</select></label>
      <label>دوره مالی<input name="fiscal_period" maxlength="40" placeholder="۱۴۰۵/۰۷" value="${esc(existing?.fiscal_period || '')}"></label>
      <label>اولویت<select name="priority">${priorityOptions}</select></label>
      <label>وزن ارزیابی<select name="weight"><option value="1" ${existing?.weight === 1 ? 'selected' : ''}>عادی · ۱</option><option value="2" ${existing?.weight === 2 ? 'selected' : ''}>مهم · ۲</option><option value="3" ${existing?.weight === 3 ? 'selected' : ''}>خیلی مهم · ۳</option></select></label>
      <label>مهلت (شمسی، اختیاری)<input name="due_date" maxlength="12" placeholder="۱۴۰۵/۰۷/۳۰" value="${esc(existing?.due_date || '')}"></label>
      <label>پیشرفت (٪)<input name="progress" type="number" min="0" max="100" value="${esc(existing?.progress || 0)}"></label>
      <label class="wide-field">دامنه کار<input name="scope" maxlength="500" placeholder="مثلاً اسناد از ۱۴۰۵/۰۷/۰۱ تا ۱۴۰۵/۰۷/۳۰" value="${esc(existing?.scope || '')}"></label>
      <label class="wide-field">شرح یا نتیجه<textarea name="description" maxlength="2000" placeholder="خلاصهٔ کار انجام‌شده یا نتیجهٔ آن">${esc(existing?.description || '')}</textarea></label>
    </div>
    <button class="btn primary">${existing ? 'ذخیره تغییرات' : 'ثبت برای بررسی'}</button>
  </form>`, {wide: true});
  $('#performanceEntryForm', form).addEventListener('submit', async e => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    values.duration_minutes = Number(values.duration_minutes);
    values.weight = Number(values.weight);
    values.progress = Number(values.progress);
    values.due_date = values.due_date || '';
    try {
      await api(existing ? `/performance-entries/${existing.id}` : '/performance-entries', json(existing ? 'PUT' : 'POST', values));
      $('#modalRoot').innerHTML = '';
      toast('ثبت عملکرد ذخیره شد');
      await renderPerformanceEntries();
    } catch (err) { toast(err.message, true); }
  });
}

function reviewPerformanceEntry(id){
  const form = modal('بررسی عملکرد', 'گزارش را تأیید کنید یا برای اصلاح بازگردانید.', `<form id="performanceReviewForm" class="stack">
    <label>نتیجه<select name="status"><option value="APPROVED">تأیید</option><option value="NEEDS_EDIT">بازگشت برای اصلاح</option></select></label>
    <label>یادداشت<textarea name="review_note" maxlength="1000" placeholder="در صورت نیاز، توضیح کوتاه بنویسید"></textarea></label>
    <button class="btn primary">ثبت بررسی</button>
  </form>`);
  $('#performanceReviewForm', form).addEventListener('submit', async e => {
    e.preventDefault();
    const values = Object.fromEntries(new FormData(e.currentTarget));
    try {
      await api(`/performance-entries/${id}/review`, json('POST', values));
      $('#modalRoot').innerHTML = '';
      toast('بررسی عملکرد ثبت شد');
      await renderPerformanceEntries();
    } catch (err) { toast(err.message, true); }
  });
}

// ============ Performance files modal — submissions + reference + diffs ============

async function openPerfFilesModal(entryId){
  try {
    // Fetch entry + submissions + references
    const entry = state.performanceEntries.find(e => e.id === entryId);
    if (!entry) { toast('عملکرد پیدا نشد', true); return; }
    const submissions = await api(`/performance-entries/${entryId}/submissions`);
    const references = await api(`/performance-entries/${entryId}/references`);
    const isManager = ['ADMIN', 'CEO'].includes(state.me.role);
    const isOwner = entry.user_id === state.me.id;
    const root = document.getElementById('modalRoot');
    if (!root) { alert('modalRoot not found'); return; }

    root.innerHTML = `
      <div style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px;" onclick="if(event.target===this)window.__closePerfFiles()">
        <div style="background:#fff;border-radius:14px;padding:24px;max-width:900px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 50px rgba(0,0,0,0.25);font-family:Vazirmatn,system-ui,sans-serif;color:#0f172a;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;border-bottom:1px solid #f1f5f9;padding-bottom:14px;">
            <div>
              <h2 style="margin:0;font-size:18px;">📁 فایل‌های عملکرد: ${esc(entry.title)}</h2>
              <p style="font-size:12px;color:#64748b;margin-top:4px;">کارمند: ${esc(entry.user_name || '—')} • تاریخ: ${esc(entry.work_date)}</p>
            </div>
            <button onclick="window.__closePerfFiles()" style="background:#f1f5f9;border:none;width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:18px;">✕</button>
          </div>

          <div style="margin-bottom:18px;">
            <h3 style="font-size:14px;margin:0 0 8px;">📤 آپلود فایل اکسل ${isOwner ? '(کارمند)' : ''}</h3>
            <form id="perfFileForm" style="display:grid;gap:8px;border:1px dashed #cbd5e1;padding:14px;border-radius:10px;background:#f8fafc;">
              <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;">
                <label style="font-size:12px;">از تاریخ<input name="claimed_start" placeholder="۱۴۰۵/۰۷/۰۱" style="padding:6px;border:1px solid #cbd5e1;border-radius:6px;"></label>
                <label style="font-size:12px;">تا تاریخ<input name="claimed_end" placeholder="۱۴۰۵/۰۷/۳۰" style="padding:6px;border:1px solid #cbd5e1;border-radius:6px;"></label>
              </div>
              <label style="font-size:12px;">یادداشت<input name="note" placeholder="توضیح کوتاه" style="padding:6px;border:1px solid #cbd5e1;border-radius:6px;"></label>
              <label style="font-size:12px;">فایل اکسل (.xlsx)<input type="file" name="file" accept=".xlsx" required style="padding:6px;"></label>
              <button type="submit" class="btn primary" style="padding:8px 16px;border:0;border-radius:8px;background:#0b8f89;color:#fff;cursor:pointer;font-family:inherit;">ارسال فایل</button>
              <p style="font-size:11px;color:#64748b;margin:0;">قالب فایل باید مطابق با <a href="/api/template" target="_blank" style="color:#0b8f89;">قالب نمونه</a> باشد. در صورت اختلاف، پیام خطا نمایش داده می‌شود.</p>
            </form>
          </div>

          ${isManager ? `
            <div style="margin-bottom:18px;border-top:1px solid #f1f5f9;padding-top:14px;">
              <h3 style="font-size:14px;margin:0 0 8px;">📥 آپلود فایل مرجع (مدیر)</h3>
              <form id="perfRefForm" style="display:grid;gap:8px;border:1px dashed #cbd5e1;padding:14px;border-radius:10px;background:#fef9e7;">
                <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
                  <label style="font-size:12px;">دوره مالی<input name="fiscal_period" placeholder="۱۴۰۵/۰۷" style="padding:6px;border:1px solid #cbd5e1;border-radius:6px;"></label>
                  <label style="font-size:12px;">از<input name="coverage_start" placeholder="۱۴۰۵/۰۷/۰۱" style="padding:6px;border:1px solid #cbd5e1;border-radius:6px;"></label>
                  <label style="font-size:12px;">تا<input name="coverage_end" placeholder="۱۴۰۵/۰۷/۳۰" style="padding:6px;border:1px solid #cbd5e1;border-radius:6px;"></label>
                </div>
                <label style="font-size:12px;">فایل مرجع اکسل (.xlsx)<input type="file" name="file" accept=".xlsx" required style="padding:6px;"></label>
                <button type="submit" class="btn primary" style="padding:8px 16px;border:0;border-radius:8px;background:#0b8f89;color:#fff;cursor:pointer;font-family:inherit;">بارگذاری مرجع و بررسی همه ارسال‌ها</button>
                <p style="font-size:11px;color:#64748b;margin:0;">بعد از بارگذاری، همه‌ی ارسال‌های قبلی این عملکرد با مرجع بررسی می‌شوند و اختلافات ذخیره می‌شوند.</p>
              </form>
            </div>
          ` : ''}

          <div style="border-top:1px solid #f1f5f9;padding-top:14px;">
            <h3 style="font-size:14px;margin:0 0 8px;">🗂 مراجع بارگذاری‌شده (${references.length})</h3>
            ${references.length ? `
              <table style="width:100%;border-collapse:collapse;font-size:12px;margin-bottom:14px;">
                <thead><tr style="background:#f8fafc;">
                  <th style="padding:6px;text-align:right;">نسخه</th>
                  <th>فایل</th><th>دوره</th><th>ردیف</th><th>بارگذار</th><th>تاریخ</th>
                </tr></thead>
                <tbody>
                  ${references.map(r => `
                    <tr style="border-bottom:1px solid #f1f5f9;">
                      <td style="padding:6px;text-align:center;"><b>v${r.version}</b></td>
                      <td style="padding:6px;">${esc(r.original_name)}</td>
                      <td style="padding:6px;text-align:center;">${esc(r.fiscal_period || '—')}</td>
                      <td style="padding:6px;text-align:center;">${r.row_count}</td>
                      <td style="padding:6px;text-align:center;">${esc(r.uploaded_by_name || '—')}</td>
                      <td style="padding:6px;text-align:center;">${timeFmt(r.created_at)}</td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            ` : '<p style="font-size:12px;color:#64748b;padding:10px;background:#f8fafc;border-radius:8px;">هنوز مرجعی بارگذاری نشده — مدیر باید فایل مرجع را آپلود کند.</p>'}

            <h3 style="font-size:14px;margin:14px 0 8px;">📨 ارسال‌های کارمند (${submissions.length})</h3>
            ${submissions.length ? `
              <table style="width:100%;border-collapse:collapse;font-size:12px;">
                <thead><tr style="background:#f8fafc;">
                  <th style="padding:6px;text-align:right;">نسخه</th>
                  <th>فایل</th><th>ردیف</th><th>قالب</th><th>اختلاف</th><th>وضعیت</th><th>تاریخ</th><th>عملیات</th>
                </tr></thead>
                <tbody>
                  ${submissions.map(s => `
                    <tr style="border-bottom:1px solid #f1f5f9;">
                      <td style="padding:6px;text-align:center;"><b>v${s.version}</b></td>
                      <td style="padding:6px;">${esc(s.original_name)}<br><small style="color:#94a3b8;">${s.note || ''}</small></td>
                      <td style="padding:6px;text-align:center;">${s.row_count}</td>
                      <td style="padding:6px;text-align:center;">${s.template_valid ? '✓ معتبر' : '✗ نامعتبر'}</td>
                      <td style="padding:6px;text-align:center;">${(s.diff_count || 0) > 0 ? `<b style="color:#dc2626;">${s.diff_count}</b>` : `<b style="color:#16a34a;">۰</b>`}</td>
                      <td style="padding:6px;text-align:center;">${s.status === 'PENDING' ? '🟡 در انتظار' : s.status === 'APPROVED' ? '🟢 تأیید' : s.status === 'RETURNED' ? '🟠 بازگشت' : '🔴 رد'}</td>
                      <td style="padding:6px;text-align:center;">${timeFmt(s.created_at)}</td>
                      <td style="padding:6px;">
                        <button class="btn soft small" onclick="window.__showPerfDiffs('${entryId}', '${s.id}')" style="padding:4px 8px;font-size:11px;border:1px solid #cbd5e1;background:#f1f5f9;border-radius:6px;cursor:pointer;">🔍 اختلافات</button>
                        <a href="/api/performance-entries/${entryId}/submissions/${s.id}/diffs/excel" style="padding:4px 8px;font-size:11px;border:1px solid #cbd5e1;background:#e0f2fe;color:#0c4a6e;border-radius:6px;text-decoration:none;display:inline-block;margin-top:2px;">⬇ Excel</a>
                        ${isManager ? `
                          <div style="margin-top:4px;display:flex;gap:4px;">
                            <button onclick="window.__perfDecide('${entryId}', '${s.id}', 'APPROVED')" style="padding:3px 6px;font-size:10px;border:0;border-radius:4px;background:#16a34a;color:#fff;cursor:pointer;">تأیید</button>
                            <button onclick="window.__perfDecide('${entryId}', '${s.id}', 'RETURNED')" style="padding:3px 6px;font-size:10px;border:0;border-radius:4px;background:#ea580c;color:#fff;cursor:pointer;">بازگشت</button>
                            <button onclick="window.__perfDecide('${entryId}', '${s.id}', 'REJECTED')" style="padding:3px 6px;font-size:10px;border:0;border-radius:4px;background:#dc2626;color:#fff;cursor:pointer;">رد</button>
                          </div>
                        ` : ''}
                      </td>
                    </tr>
                  `).join('')}
                </tbody>
              </table>
            ` : '<p style="font-size:12px;color:#64748b;padding:10px;background:#f8fafc;border-radius:8px;">هنوز فایلی ارسال نشده.</p>'}
          </div>
        </div>
      </div>
    `;
    window.__closePerfFiles = () => { root.innerHTML = ''; };

    // File submit handler
    const fileForm = document.getElementById('perfFileForm');
    fileForm.addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(e.currentTarget);
      try {
        const res = await fetch(`/api/performance-entries/${entryId}/submit-file`, {
          method: 'POST', body: fd, credentials: 'same-origin',
        });
        const data = await res.json();
        if (data.accepted === false) {
          // Template validation failed
          alert('❌ فایل با قالب سیستم مطابقت ندارد:\n\n' + (data.errors || []).join('\n') + '\n\n' + (data.message || ''));
        } else if (data.accepted) {
          toast(`فایل آپلود شد — ${data.diff_count || 0} اختلاف`);
          window.__closePerfFiles();
          openPerfFilesModal(entryId);  // reload
        } else {
          toast(data.detail || 'خطا در آپلود', true);
        }
      } catch (err) { toast(err.message, true); }
    });

    // Reference upload handler
    const refForm = document.getElementById('perfRefForm');
    if (refForm) {
      refForm.addEventListener('submit', async e => {
        e.preventDefault();
        const fd = new FormData(e.currentTarget);
        try {
          const res = await fetch(`/api/performance-entries/${entryId}/reference`, {
            method: 'POST', body: fd, credentials: 'same-origin',
          });
          const data = await res.json();
          if (res.ok) {
            toast(data.message || `مرجع آپلود شد — ${data.re_reconciled_submissions || 0} ارسال بررسی شد`);
            window.__closePerfFiles();
            openPerfFilesModal(entryId);  // reload
          } else {
            toast(data.detail || 'خطا در آپلود مرجع', true);
          }
        } catch (err) { toast(err.message, true); }
      });
    }
  } catch (e) { toast(e.message, true); }
}

// Show diffs for a submission
window.__showPerfDiffs = async (entryId, subId) => {
  try {
    const data = await api(`/performance-entries/${entryId}/submissions/${subId}/diffs`);
    const root = document.getElementById('modalRoot');
    if (!root) return;
    const diffs = data.diffs || [];
    const report = data.report || {};
    root.innerHTML = `
      <div style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px;" onclick="if(event.target===this)window.__closePerfDiffs()">
        <div style="background:#fff;border-radius:14px;padding:24px;max-width:1100px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 50px rgba(0,0,0,0.25);font-family:Vazirmatn,system-ui,sans-serif;color:#0f172a;">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;border-bottom:1px solid #f1f5f9;padding-bottom:14px;">
            <div>
              <h2 style="margin:0;font-size:16px;">🔍 اختلافات نسخه ${data.submission.version}</h2>
              <p style="font-size:11px;color:#64748b;margin-top:4px;">
                ${report.row_count || 0} ردیف •
                تطبیق دقیق: ${report.matched_exact ?? '—'} •
                فقط در ارسال: ${report.submission_only ?? '—'} •
                فقط در مرجع: ${report.reference_only ?? '—'}
              </p>
            </div>
            <div style="display:flex;gap:8px;align-items:center;">
              <a href="/api/performance-entries/${entryId}/submissions/${subId}/diffs/excel" style="padding:6px 12px;font-size:12px;border:0;border-radius:8px;background:#0b8f89;color:#fff;text-decoration:none;">⬇ Excel</a>
              <button onclick="window.__closePerfDiffs()" style="background:#f1f5f9;border:none;width:32px;height:32px;border-radius:8px;cursor:pointer;font-size:18px;">✕</button>
            </div>
          </div>
          ${diffs.length ? `
            <table style="width:100%;border-collapse:collapse;font-size:11px;">
              <thead><tr style="background:#f1f5f9;">
                <th style="padding:6px;">ردیف</th><th>سند</th><th>خط</th><th>تاریخ</th><th>حساب</th><th>بدهکار</th><th>بستانکار</th><th>شرح</th><th>نوع</th><th>جزئیات</th>
              </tr></thead>
              <tbody>
                ${diffs.map(d => `
                  <tr style="border-bottom:1px solid #f1f5f9;background:${PERF_ISSUE_COLORS[d.issue_type] || '#fff'};">
                    <td style="padding:5px;">${d.source_row}</td>
                    <td style="padding:5px;">${esc(d.voucher)}</td>
                    <td style="padding:5px;">${esc(d.line)}</td>
                    <td style="padding:5px;">${esc(d.date)}</td>
                    <td style="padding:5px;">${esc(d.account)}</td>
                    <td style="padding:5px;color:#dc2626;">${d.debit}${d.ref_debit && d.ref_debit !== d.debit ? ` (${esc(d.ref_debit)})` : ''}</td>
                    <td style="padding:5px;color:#dc2626;">${d.credit}${d.ref_credit && d.ref_credit !== d.credit ? ` (${esc(d.ref_credit)})` : ''}</td>
                    <td style="padding:5px;max-width:200px;">${esc(d.description)}</td>
                    <td style="padding:5px;"><b>${PERF_ISSUE_LABELS[d.issue_type] || d.issue_type}</b></td>
                    <td style="padding:5px;max-width:300px;">${esc(d.issue_detail)}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          ` : '<p style="padding:30px;text-align:center;color:#16a34a;font-size:14px;">✓ هیچ اختلافی پیدا نشد — همه ردیف‌ها با مرجع مطابقت دارند.</p>'}
          <button onclick="window.__closePerfDiffs()" class="btn primary" style="margin-top:18px;padding:8px 16px;border:0;border-radius:8px;background:#0b8f89;color:#fff;cursor:pointer;font-family:inherit;width:100%;">بستن</button>
        </div>
      </div>
    `;
    window.__closePerfDiffs = () => { root.innerHTML = ''; };
  } catch (e) { toast(e.message, true); }
};

// Manager decision on a submission
window.__perfDecide = async (entryId, subId, decision) => {
  const note = prompt(`یادداشت برای ${decision === 'APPROVED' ? 'تأیید' : decision === 'RETURNED' ? 'بازگشت' : 'رد'}:`, '');
  if (note === null) return;
  try {
    await api(`/performance-entries/${entryId}/submissions/${subId}/decision`, json('POST', {decision, note}));
    toast(`تصمیم ثبت شد: ${decision}`);
    window.__closePerfFiles && window.__closePerfFiles();
    setTimeout(() => openPerfFilesModal(entryId), 100);
  } catch (err) { toast(err.message, true); }
};

// Hook into nav clicks for "perf-files" action
document.addEventListener('click', async e => {
  const btn = e.target.closest('[data-action="perf-files"]');
  if (!btn) return;
  e.preventDefault();
  await openPerfFilesModal(btn.dataset.id);
});
