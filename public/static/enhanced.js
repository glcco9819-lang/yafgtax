// YFG Enhanced Features v2.0 - Fixed version
// Adds: Dashboard Charts, Kanban View, Time Tracking, Chat, Automations, ISO 30414

(function() {
  'use strict';
  
  const CHART_COLORS = ['#0b8f89','#f59e0b','#ef4444','#8b5cf6','#3b82f6','#10b981','#ec4899','#f97316'];
  let charts = {};
  let timerInterval = null;
  let timerStart = null;
  let currentChannel = null;

  // Retry mechanism - keeps trying until DOM is ready
  let retries = 0;
  const tryInit = setInterval(() => {
    retries++;
    if (retries > 50) { clearInterval(tryInit); return; }
    const nav = document.getElementById('nav');
    const main = document.querySelector('main');
    if (nav && nav.children.length > 0 && main) {
      // Check if already initialized
      if (nav.querySelector('[data-view="kanban"]')) { clearInterval(tryInit); return; }
      clearInterval(tryInit);
      init();
    }
  }, 200);

  function esc(s) { return String(s ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
  function toast(msg, err) {
    const e = document.getElementById('toast');
    if (!e) { console.log(msg); return; }
    e.textContent = msg; e.style.background = err ? '#9f413d' : '#163f49';
    e.classList.remove('hidden');
    clearTimeout(toast.timer); toast.timer = setTimeout(() => e.classList.add('hidden'), 3600);
  }
  function timeFmt(s) { if(!s) return '—'; const d=new Date(s); return isNaN(d)?esc(s):new Intl.DateTimeFormat('fa-IR-u-ca-persian',{timeZone:'Asia/Tehran',hour:'2-digit',minute:'2-digit',year:'numeric',month:'2-digit',day:'2-digit'}).format(d); }

  async function api(path, opt = {}) {
    const cfg = {credentials: 'same-origin', ...opt, headers: {...(opt.body instanceof FormData ? {} : {'Content-Type': 'application/json'}), ...(opt.headers || {})}};
    let res;
    try { res = await fetch('/api' + path, cfg); } catch(e) { throw Error('اتصال به سرور برقرار نشد.'); }
    let data;
    try { data = await res.json(); } catch { data = {detail: 'پاسخ سرور قابل خواندن نیست'}; }
    if (!res.ok) throw Error(data.detail || 'عملیات ناموفق بود');
    return data;
  }

  function init() {
    console.log('YFG Enhanced v2.0 initializing...');
    addTimerWidget();
    addNavItems();
    addViewSections();
    loadActiveTimer();
    // Hook into dashboard rendering
    const dashBtn = document.querySelector('[data-view="dashboard"]');
    if (dashBtn) {
      dashBtn.addEventListener('click', () => setTimeout(renderDashboardCharts, 600));
    }
  }

  // ============ Nav Items ============
  function addNavItems() {
    const nav = document.getElementById('nav');
    if (!nav) return;
    const isAdmin = typeof state !== 'undefined' && (state.me?.role === 'ADMIN' || state.me?.role === 'CEO');
    const items = [
      {view: 'kanban', icon: '▦', label: 'کانبان', admin: false},
      {view: 'kpi-report', icon: '🎯', label: 'گزارش KPI', admin: true},
      {view: 'time', icon: '◷', label: 'تایم ترکینگ', admin: false},
      {view: 'chat', icon: '✉', label: 'گفتگو', admin: false},
      {view: 'automations', icon: '⚙', label: 'اتوماسیون', admin: true},
      {view: 'iso30414', icon: '📊', label: 'گزارش ISO ۳۰۴۱۴', admin: true},
      {view: 'settings', icon: '🔧', label: 'تنظیمات', admin: true},
    ];
    items.forEach(item => {
      if (nav.querySelector(`[data-view="${item.view}"]`)) return;
      const btn = document.createElement('button');
      btn.className = 'nav-item' + (item.admin ? ' admin-only' : '');
      btn.dataset.view = item.view;
      btn.innerHTML = `<span class="nav-icon">${item.icon}</span> ${item.label}`;
      btn.addEventListener('click', () => {
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        btn.classList.add('active');
        showView(item.view);
      });
      nav.appendChild(btn);
    });
  }

  // ============ View Sections ============
  function addViewSections() {
    const main = document.querySelector('main');
    if (!main) return;
    ['kanban','kpi-report','time','chat','automations','iso30414','settings'].forEach(v => {
      if (document.getElementById(`view-${v}`)) return;
      const section = document.createElement('section');
      section.id = `view-${v}`;
      section.className = 'view hidden';
      main.appendChild(section);
    });
  }

  function showView(view) {
    document.querySelectorAll('.view').forEach(v => v.classList.add('hidden'));
    const section = document.getElementById(`view-${view}`);
    if (section) section.classList.remove('hidden');
    switch(view) {
      case 'kanban': renderKanban(); break;
      case 'kpi-report': renderKPIReport(); break;
      case 'time': renderTimeTracking(); break;
      case 'chat': renderChat(); break;
      case 'automations': renderAutomations(); break;
      case 'iso30414': renderISO30414(); break;
      case 'settings': renderSettings(); break;
    }
  }

  // Also override app.js renderPerformance to call KPI report (for nav-item "گزارش عملکرد تیم")
  window.renderPerformance = function() { renderKPIReport(); };

  // ============ Timer Widget ============
  function addTimerWidget() {
    if (document.getElementById('timerWidget')) return;
    const widget = document.createElement('div');
    widget.id = 'timerWidget';
    widget.style.cssText = 'position:fixed;bottom:20px;left:20px;z-index:100;background:#0b8f89;color:#fff;padding:12px 20px;border-radius:12px;box-shadow:0 4px 12px rgba(0,0,0,0.2);font-size:14px;display:none;';
    widget.innerHTML = `<div style="display:flex;align-items:center;gap:10px;"><span id="timerDisplay" style="font-family:monospace;font-size:18px;">00:00:00</span><button id="timerStopBtn" style="background:#ef4444;color:#fff;border:none;padding:6px 16px;border-radius:8px;cursor:pointer;font-size:12px;">توقف</button></div><div id="timerTask" style="font-size:11px;margin-top:4px;opacity:0.8;"></div>`;
    document.body.appendChild(widget);
    document.getElementById('timerStopBtn')?.addEventListener('click', stopTimer);
  }

  async function loadActiveTimer() {
    try {
      const active = await api('/time/active');
      if (active && active.start_at) {
        timerStart = new Date(active.start_at);
        document.getElementById('timerWidget').style.display = 'block';
        document.getElementById('timerTask').textContent = active.task_title || '';
        startTimerInterval();
      }
    } catch(e) {}
  }

  function startTimerInterval() {
    if (timerInterval) clearInterval(timerInterval);
    timerInterval = setInterval(() => {
      if (!timerStart) return;
      const elapsed = Math.floor((Date.now() - timerStart.getTime()) / 1000);
      const h = String(Math.floor(elapsed/3600)).padStart(2,'0');
      const m = String(Math.floor((elapsed%3600)/60)).padStart(2,'0');
      const s = String(elapsed%60).padStart(2,'0');
      const d = document.getElementById('timerDisplay');
      if (d) d.textContent = `${h}:${m}:${s}`;
    }, 1000);
  }

  async function startTimer(taskId, taskTitle) {
    try {
      await api('/time/start', {method:'POST', body: JSON.stringify({task_id: taskId, description: ''})});
      timerStart = new Date();
      document.getElementById('timerWidget').style.display = 'block';
      document.getElementById('timerTask').textContent = taskTitle || '';
      startTimerInterval();
      toast('تایمر شروع شد');
    } catch(e) { toast(e.message, true); }
  }

  async function stopTimer() {
    try {
      const r = await api('/time/stop', {method:'POST'});
      clearInterval(timerInterval); timerStart = null;
      document.getElementById('timerWidget').style.display = 'none';
      toast(`تایمر متوقف شد — ${Math.round(r.duration_seconds/60)} دقیقه`);
    } catch(e) { toast(e.message, true); }
  }

  // ============ Dashboard Charts ============
  async function renderDashboardCharts() {
    try {
      const data = await api('/dashboard/charts');
      const container = document.querySelector('#view-dashboard') || document.querySelector('[data-view="dashboard"]');
      if (!container) return;
      let chartArea = document.getElementById('chartArea');
      if (chartArea) chartArea.remove();
      chartArea = document.createElement('div');
      chartArea.id = 'chartArea';
      chartArea.style.cssText = 'margin-top:20px;';
      container.appendChild(chartArea);
      chartArea.innerHTML = `
        <h3 style="margin:20px 0 10px;">نمودارهای تحلیلی</h3>
        <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px;">
          <div style="background:#fff;padding:16px;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><h4 style="margin-bottom:12px;font-size:14px;">توزیع وضعیت تسک‌ها</h4><canvas id="chartStatus" height="200"></canvas></div>
          <div style="background:#fff;padding:16px;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><h4 style="margin-bottom:12px;font-size:14px;">تسک‌ها به ازای شرکت</h4><canvas id="chartCompany" height="200"></canvas></div>
          <div style="background:#fff;padding:16px;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><h4 style="margin-bottom:12px;font-size:14px;">بار کاری کارمندان</h4><canvas id="chartWorkload" height="200"></canvas></div>
          <div style="background:#fff;padding:16px;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><h4 style="margin-bottom:12px;font-size:14px;">توزیع اولویت</h4><canvas id="chartPriority" height="200"></canvas></div>
        </div>`;
      Object.values(charts).forEach(c => c?.destroy?.()); charts = {};
      const sl = {ASSIGNED:'واگذار شده',IN_PROGRESS:'در حال انجام',SUBMITTED:'ارسال شده',NEEDS_REVIEW:'نیازمند بررسی',RETURNED:'برگشتی',APPROVED:'تأیید شده',APPROVED_WITH_EXCEPTION:'تأیید با ارفاق',CANCELLED:'لغو شده'};
      const sd = data.status_distribution || {};
      if (typeof Chart !== 'undefined' && Object.keys(sd).length) {
        charts.status = new Chart(document.getElementById('chartStatus'), {type:'doughnut',data:{labels:Object.keys(sd).map(k=>sl[k]||k),datasets:[{data:Object.values(sd),backgroundColor:CHART_COLORS}]},options:{responsive:true,plugins:{legend:{position:'bottom'}}}});
      }
      const ct = data.company_tasks || [];
      if (typeof Chart !== 'undefined' && ct.length) {
        charts.company = new Chart(document.getElementById('chartCompany'), {type:'bar',data:{labels:ct.map(c=>c.name),datasets:[{label:'تعداد تسک',data:ct.map(c=>c.count),backgroundColor:'#0b8f89'}]},options:{responsive:true,plugins:{legend:{display:false}}}});
      }
      const wl = data.employee_workload || [];
      if (typeof Chart !== 'undefined' && wl.length) {
        charts.workload = new Chart(document.getElementById('chartWorkload'), {type:'bar',data:{labels:wl.map(w=>w.name),datasets:[{label:'باز',data:wl.map(w=>w.open),backgroundColor:'#f59e0b'},{label:'تکمیل',data:wl.map(w=>w.done),backgroundColor:'#10b981'}]},options:{responsive:true,scales:{x:{stacked:true},y:{stacked:true}}}});
      }
      const pd = data.priority_distribution || {};
      const pl = {NORMAL:'عادی',IMPORTANT:'مهم',CRITICAL:'بحرانی'};
      if (typeof Chart !== 'undefined' && Object.keys(pd).length) {
        charts.priority = new Chart(document.getElementById('chartPriority'), {type:'doughnut',data:{labels:Object.keys(pd).map(k=>pl[k]||k),datasets:[{data:Object.values(pd),backgroundColor:CHART_COLORS}]},options:{responsive:true,plugins:{legend:{position:'bottom'}}}});
      }
    } catch(e) { console.error('Chart error:', e); }
  }

  // ============ Kanban ============
  async function renderKanban() {
    const section = document.getElementById('view-kanban');
    if (!section) return;
    try {
      const data = await api('/tasks');
      const tasks = data.tasks || data || [];
      const columns = [{status:'ASSIGNED',label:'واگذار شده',color:'#3b82f6'},{status:'IN_PROGRESS',label:'در حال انجام',color:'#f59e0b'},{status:'SUBMITTED',label:'ارسال شده',color:'#06b6d4'},{status:'NEEDS_REVIEW',label:'نیازمند بررسی',color:'#f97316'},{status:'APPROVED',label:'تأیید شده',color:'#10b981'},{status:'RETURNED',label:'برگشتی',color:'#ef4444'}];
      section.innerHTML = `<h1>کانبان تسک‌ها</h1><p class="hint">برای جابجایی تسک، روی آن کلیک کنید و شماره ستون مقصد را وارد کنید.</p><div style="display:flex;gap:12px;overflow-x:auto;padding-bottom:16px;">${columns.map(col=>{const colTasks=tasks.filter(t=>t.status===col.status);return `<div style="min-width:260px;flex-shrink:0;background:#f1f5f9;border-radius:12px;padding:12px;"><div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;"><span style="width:10px;height:10px;border-radius:50%;background:${col.color};"></span><strong>${col.label}</strong><span style="margin-right:auto;background:#e2e8f0;padding:2px 10px;border-radius:12px;font-size:12px;">${colTasks.length}</span></div>${colTasks.map(t=>`<div style="background:#fff;padding:12px;border-radius:8px;margin-bottom:8px;cursor:pointer;border-right:3px solid ${col.color};" onclick="window.__moveTask('${t.id}','${esc(t.title)}')"><div style="font-size:13px;font-weight:600;margin-bottom:4px;">${esc(t.title)}</div><div style="font-size:11px;color:#64748b;">${esc(t.company_name||'')} • ${esc(t.assignee_name||'')}</div>${t.weight?`<span style="display:inline-block;background:#fef3c7;color:#92400e;padding:1px 8px;border-radius:8px;font-size:10px;margin-top:4px;">وزن: ${t.weight}</span>`:''}</div>`).join('')}</div>`}).join('')}</div>`;
      window.__moveTask = async (taskId, title) => {
        const labels = ['واگذار شده','در حال انجام','ارسال شده','نیازمند بررسی','تأیید شده','برگشتی'];
        const statuses = ['ASSIGNED','IN_PROGRESS','SUBMITTED','NEEDS_REVIEW','APPROVED','RETURNED'];
        const c = prompt(`جابجایی «${title}» به:\n${labels.map((l,i)=>`${i+1}. ${l}`).join('\n')}\n\nشماره:`);
        if (!c) return; const idx = parseInt(c)-1; if (idx<0||idx>=statuses.length) return;
        try { await api('/kanban/order',{method:'POST',body:JSON.stringify({task_id:taskId,column_status:statuses[idx],sort_order:0})}); toast(`به «${labels[idx]}» منتقل شد`); renderKanban(); } catch(e) { toast(e.message,true); }
      };
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // ============ Time Tracking ============
  async function renderTimeTracking() {
    const section = document.getElementById('view-time');
    if (!section) return;
    try {
      const [entries, timesheet] = await Promise.all([api('/time/entries'), api('/time/timesheet')]);
      const isAdmin = typeof state !== 'undefined' && (state.me?.role==='ADMIN'||state.me?.role==='CEO');
      section.innerHTML = `<h1>تایم ترکینگ</h1><p class="hint">زمان صرف‌شده روی هر تسک را ثبت و گزارش بگیرید.</p><h3 style="margin-top:20px;">سوابق زمان</h3><div class="table-card"><table class="data-table"><thead><tr><th>کارمند</th><th>تسک</th><th>شرکت</th><th>شروع</th><th>پایان</th><th>مدت</th></tr></thead><tbody>${(entries||[]).map(e=>{const d=e.duration_seconds>0?`${Math.floor(e.duration_seconds/3600)}س ${Math.floor((e.duration_seconds%3600)/60)}د`:'—';return `<tr><td>${esc(e.user_name||'')}</td><td>${esc(e.task_title||'—')}</td><td>${esc(e.company_name||'—')}</td><td>${timeFmt(e.start_at)}</td><td>${e.end_at?timeFmt(e.end_at):'<span style="color:#10b981;">در حال اجرا</span>'}</td><td>${d}</td></tr>`}).join('')}</tbody></table></div>${isAdmin?`<h3 style="margin-top:20px;">گزارش تایم‌شیت</h3><div class="table-card"><table class="data-table"><thead><tr><th>کارمند</th><th>تسک</th><th>مجموع زمان</th><th>تعداد</th></tr></thead><tbody>${(timesheet||[]).map(t=>`<tr><td>${esc(t.user_name||'')}</td><td>${esc(t.task_title||'—')}</td><td>${Math.floor(t.total_seconds/3600)}س ${Math.floor((t.total_seconds%3600)/60)}د</td><td>${t.entry_count}</td></tr>`).join('')}</tbody></table></div>`:''}`;
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // ============ Chat ============
  async function renderChat() {
    const section = document.getElementById('view-chat');
    if (!section) return;
    try {
      const channels = await api('/chat/channels');
      section.innerHTML = `<h1>گفتگو</h1><div style="display:flex;gap:16px;height:calc(100vh - 220px);"><div style="width:240px;flex-shrink:0;background:#f1f5f9;border-radius:12px;padding:12px;overflow-y:auto;"><button class="btn primary small" style="width:100%;margin-bottom:12px;" onclick="window.__newChannel()">＋ کانال جدید</button>${(channels||[]).map(ch=>`<div onclick="window.__openChannel('${ch.id}','${esc(ch.name)}')" style="padding:10px;border-radius:8px;cursor:pointer;margin-bottom:4px;background:#fff;"><strong>${esc(ch.name)}</strong><div style="font-size:11px;color:#64748b;">${ch.message_count||0} پیام</div></div>`).join('')}</div><div style="flex:1;display:flex;flex-direction:column;background:#fff;border-radius:12px;overflow:hidden;"><div id="chatMessages" style="flex:1;overflow-y:auto;padding:16px;"><p style="text-align:center;color:#94a3b8;padding-top:40px;">یک کانال را انتخاب کنید</p></div><div style="padding:12px;border-top:1px solid #e2e8f0;"><div style="display:flex;gap:8px;"><input id="chatInput" class="field" placeholder="پیام بنویسید..." style="flex:1;" onkeydown="if(event.key==='Enter')window.__sendChatMsg()"><button class="btn primary" onclick="window.__sendChatMsg()">ارسال</button></div></div></div></div>`;
      window.__newChannel = () => { const n=prompt('نام کانال:'); if(!n) return; api('/chat/channels',{method:'POST',body:JSON.stringify({name:n,member_ids:[]})}).then(()=>{toast('کانال ایجاد شد');renderChat()}).catch(e=>toast(e.message,true)); };
      window.__openChannel = async (chId) => { currentChannel=chId; try { const msgs=await api(`/chat/channels/${chId}/messages`); const c=document.getElementById('chatMessages'); if(!c) return; c.innerHTML=(msgs||[]).map(m=>`<div style="margin-bottom:12px;${m.user_id===state.me.id?'text-align:left;':''}"><div style="display:inline-block;max-width:70%;padding:10px 16px;border-radius:12px;background:${m.user_id===state.me.id?'#0b8f89':'#f1f5f9'};color:${m.user_id===state.me.id?'#fff':'#0f172a'};"><div style="font-size:11px;opacity:0.7;margin-bottom:4px;">${esc(m.user_name)}</div><div>${esc(m.body)}</div><div style="font-size:10px;opacity:0.5;margin-top:4px;">${timeFmt(m.created_at)}</div></div></div>`).join(''); c.scrollTop=c.scrollHeight; } catch(e) { toast(e.message,true); } };
      window.__sendChatMsg = async () => { if(!currentChannel) return toast('کانال را انتخاب کنید',true); const i=document.getElementById('chatInput'); const b=i.value.trim(); if(!b) return; i.value=''; try { await api(`/chat/channels/${currentChannel}/messages`,{method:'POST',body:JSON.stringify({channel_id:currentChannel,body:b})}); window.__openChannel(currentChannel); } catch(e) { toast(e.message,true); } };
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // ============ Automations ============
  async function renderAutomations() {
    const section = document.getElementById('view-automations');
    if (!section) return;
    try {
      const autos = await api('/automations');
      const tl = {TASK_OVERDUE:'تسک عقب‌افتاده',TASK_SUBMITTED:'تسک ارسال شده',TASK_RETURNED:'تسک برگشتی',TASK_ASSIGNED:'تسک ارجاع شده'};
      const al = {NOTIFY_USER:'اطلاع به کارمند',NOTIFY_MANAGER:'اطلاع به مدیر'};
      section.innerHTML = `<h1>اتوماسیون گردش کار</h1><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><p class="hint">قوانین خودکار برای اعلان و یادآوری</p><div style="display:flex;gap:8px;"><button class="btn soft small" onclick="window.__runAuto()">▶ اجرا</button><button class="btn primary small" onclick="window.__newAuto()">＋ قانون جدید</button></div></div><div class="table-card"><table class="data-table"><thead><tr><th>نام</th><th>تریگر</th><th>اکشن</th><th>وضعیت</th><th>آخرین اجرا</th></tr></thead><tbody>${(autos||[]).map(a=>`<tr><td><strong>${esc(a.name)}</strong></td><td>${tl[a.trigger_type]||a.trigger_type}</td><td>${al[a.action_type]||a.action_type}</td><td><button class="btn small" style="background:${a.enabled?'#d1fae5':'#fee2e2'}" onclick="window.__toggleAuto('${a.id}')">${a.enabled?'✓ فعال':'✗ غیرفعال'}</button></td><td>${a.last_fired_at?timeFmt(a.last_fired_at):'—'}</td></tr>`).join('')||'<tr><td colspan="5" style="text-align:center;padding:20px;color:#64748b;">هیچ اتوماسیونی تعریف نشده</td></tr>'}</tbody></table></div>`;
      window.__newAuto = () => { const n=prompt('نام قانون:'); if(!n) return; const ts=['TASK_OVERDUE','TASK_ASSIGNED']; const tl=['تسک عقب‌افتاده','تسک ارجاع شده']; const t=prompt(`تریگر:\n${tl.map((l,i)=>`${i+1}. ${l}`).join('\n')}`); if(!t) return; const ti=parseInt(t)-1; if(ti<0||ti>=ts.length) return; api('/automations',{method:'POST',body:JSON.stringify({name:n,trigger_type:ts[ti],action_type:'NOTIFY_USER',enabled:true})}).then(()=>{toast('اتوماسیون ایجاد شد');renderAutomations()}).catch(e=>toast(e.message,true)); };
      window.__toggleAuto = (id) => api(`/automations/${id}`,{method:'PATCH'}).then(()=>renderAutomations()).catch(e=>toast(e.message,true));
      window.__runAuto = () => api('/automations/run',{method:'POST'}).then(r=>toast(`${r.results.length} اتوماسیون اجرا شد`)).catch(e=>toast(e.message,true));
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // ============ ISO 30414 ============
  async function renderISO30414() {
    const section = document.getElementById('view-iso30414');
    if (!section) return;
    try {
      const m = await api('/iso30414/report');
      const areas = [{k:'area_1_composition',t:'۱. ترکیب نیروی کار',i:'👥'},{k:'area_2_costs',t:'۲. هزینه‌ها',i:'💰'},{k:'area_4_leadership',t:'۴. رهبری',i:'👔'},{k:'area_5_culture',t:'۵. فرهنگ',i:'🏛'},{k:'area_6_health_safety',t:'۶. سلامت و ایمنی',i:'🛡'},{k:'area_7_productivity',t:'۷. بهره‌وری',i:'📈'},{k:'area_10_turnover',t:'۱۰. خروج',i:'🚪'},{k:'area_11_other',t:'۱۱. سایر',i:'📋'}];
      section.innerHTML = `<h1>گزارش ISO ۳۰۴۱۴ — سرمایه انسانی</h1><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><p class="hint">تاریخ: ${m.snapshot_date}</p><button class="btn primary small" onclick="window.__saveSnap()">📷 ثبت لحظه‌ای</button></div><div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:16px;">${areas.map(a=>{const d=m[a.k]||{};const entries=Object.entries(d).filter(([k,v])=>k!=='note');return `<div style="background:#fff;border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,0.1);"><h4 style="margin-bottom:12px;font-size:14px;">${a.i} ${a.t}</h4>${entries.map(([k,v])=>{const l=k.replace(/_/g,' ');let val=typeof v==='object'?JSON.stringify(v):v!==null?v:'—';if(typeof val==='number'&&val%1!==0)val=val.toFixed(1);return `<div style="display:flex;justify-content:space-between;padding:6px 0;border-bottom:1px solid #f1f5f9;"><span style="color:#64748b;font-size:13px;">${l}</span><strong style="font-size:13px;">${val}</strong></div>`}).join('')}${d.note?`<p style="font-size:12px;color:#94a3b8;margin-top:8px;font-style:italic;">${d.note}</p>`:''}</div>`}).join('')}</div>`;
      window.__saveSnap = () => api('/iso30414/snapshot',{method:'POST'}).then(()=>toast('تصویر لحظه‌ای ذخیره شد')).catch(e=>toast(e.message,true));
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // Expose for task detail
  window.__startTimer = startTimer;
  window.__stopTimer = stopTimer;
  window.__enhancedShowView = showView;

  // ============ USER MANAGEMENT (edit, access, deactivate) ============
  async function renderUserManagement() {
    const section = document.getElementById('view-users');
    if (!section) return;
    try {
      const users = await api('/users');
      const roleLabels = {ADMIN:'مدیر سامانه',CEO:'مدیرعامل',EMPLOYEE:'کارمند'};
      section.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
          <h1>مدیریت کاربران</h1>
          <button class="btn primary small" onclick="window.__addUser()">＋ کاربر جدید</button>
        </div>
        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>نام</th><th>نام کاربری</th><th>نقش</th><th>وضعیت</th><th>شرکت‌ها</th><th>تسک‌ها</th><th>عملیات</th></tr></thead>
            <tbody>
              ${(users||[]).map(u => `
                <tr>
                  <td><strong>${esc(u.name)}</strong></td>
                  <td class="font-mono">${esc(u.username)}</td>
                  <td><span class="tag">${roleLabels[u.role]||u.role}</span></td>
                  <td>${u.active?'<span style="color:#10b981;">✓ فعال</span>':'<span style="color:#ef4444;">✗ غیرفعال</span>'}</td>
                  <td><button class="btn soft small" onclick="window.__manageAccess('${u.id}','${esc(u.name)}')">مدیریت دسترسی</button></td>
                  <td>${u.task_count||0}</td>
                  <td style="display:flex;gap:4px;">
                    <button class="btn soft small" onclick="window.__editUser('${u.id}','${esc(u.name)}','${u.role}',${u.active})">✎ ویرایش</button>
                    ${u.active?`<button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__deactivateUser('${u.id}','${esc(u.name)}')">✗ غیرفعال</button>`:`<button class="btn small" style="background:#d1fae5;color:#065f46;" onclick="window.__activateUser('${u.id}')">✓ فعال</button>`}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      window.__addUser = () => {
        const name = prompt('نام و نام خانوادگی:');
        if (!name) return;
        const username = prompt('نام کاربری (انگلیسی):');
        if (!username) return;
        const password = prompt('رمز عبور (حداقل ۱۲ نویسه):');
        if (!password || password.length < 12) { toast('رمز باید حداقل ۱۲ نویسه باشد', true); return; }
        const role = prompt('نقش (EMPLOYEE/CEO/ADMIN):', 'EMPLOYEE');
        api('/users', {method:'POST', body: JSON.stringify({name, username, password, role, company_ids:[]})})
          .then(() => { toast('کاربر ایجاد شد'); renderUserManagement(); })
          .catch(e => toast(e.message, true));
      };
      window.__editUser = (id, name, role, active) => {
        const newName = prompt('نام جدید:', name);
        if (newName === null) return;
        const newRole = prompt('نقش جدید (EMPLOYEE/CEO/ADMIN):', role);
        if (newRole === null) return;
        const resetPass = confirm('رمز عبور را تغییر دهید؟');
        let body = {name: newName || name, role: newRole || role};
        if (resetPass) {
          const pass = prompt('رمز جدید (حداقل ۱۲ نویسه):');
          if (pass && pass.length >= 12) body.password = pass;
        }
        api(`/users/${id}`, {method:'PATCH', body: JSON.stringify(body)})
          .then(() => { toast('کاربر ویرایش شد'); renderUserManagement(); })
          .catch(e => toast(e.message, true));
      };
      window.__deactivateUser = (id, name) => {
        if (!confirm(`غیرفعال کردن «${name}»؟ تمام نشست‌های فعال حذف می‌شوند.`)) return;
        api(`/users/${id}`, {method:'DELETE'})
          .then(() => { toast('کاربر غیرفعال شد'); renderUserManagement(); })
          .catch(e => toast(e.message, true));
      };
      window.__activateUser = (id) => {
        api(`/users/${id}`, {method:'PATCH', body: JSON.stringify({active: true})})
          .then(() => { toast('کاربر فعال شد'); renderUserManagement(); })
          .catch(e => toast(e.message, true));
      };
      window.__manageAccess = async (userId, userName) => {
        try {
          const [detail, companies] = await Promise.all([
            api(`/users/${userId}`),
            api('/companies'),
          ]);
          const accessIds = new Set((detail.companies||[]).map(c => c.id));
          const available = (companies||[]).filter(c => !accessIds.has(c.id));
          let html = `<div style="margin-bottom:16px;"><h3>دسترسی «${esc(userName)}» به شرکت‌ها</h3>`;
          if ((detail.companies||[]).length > 0) {
            html += `<div style="margin-top:12px;"><strong>دسترسی فعلی:</strong><div style="margin-top:8px;">${detail.companies.map(c => `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px;background:rgba(11,143,137,0.05);border-radius:8px;margin-bottom:4px;"><span>${esc(c.name)} (${esc(c.code)})</span><button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__revokeAccess('${userId}','${c.id}')">حذف</button></div>`).join('')}</div></div>`;
          } else {
            html += `<p class="hint" style="margin-top:8px;">هیچ دسترسی فعلی وجود ندارد.</p>`;
          }
          if (available.length > 0) {
            html += `<div style="margin-top:16px;"><strong>افزودن دسترسی جدید:</strong><div style="display:flex;gap:8px;margin-top:8px;align-items:center;"><select id="accessSelect" class="field" style="flex:1;">${available.map(c => `<option value="${c.id}">${esc(c.name)} (${esc(c.code)})</option>`).join('')}</select><button class="btn primary small" onclick="window.__grantAccess('${userId}')">افزودن</button></div></div>`;
          } else if ((detail.companies||[]).length > 0) {
            html += `<p class="hint" style="margin-top:12px;">تمام شرکت‌ها در دسترسی این کاربر هستند.</p>`;
          } else {
            html += `<p class="hint" style="margin-top:12px;">هیچ شرکت فعالی برای اختصاص وجود ندارد.</p>`;
          }
          html += `</div>`;
          modal('مدیریت دسترسی', '', html);
        } catch(e) { toast(e.message, true); }
      };
      window.__grantAccess = (userId) => {
        const select = document.getElementById('accessSelect');
        if (!select || !select.value) return;
        api(`/users/${userId}/company-access`, {method:'POST', body: JSON.stringify({company_ids: [select.value]})})
          .then(r => { toast(`${r.added} دسترسی اضافه شد`); window.__manageAccess(userId, ''); })
          .catch(e => toast(e.message, true));
      };
      window.__revokeAccess = (userId, companyId) => {
        api(`/users/${userId}/company-access/${companyId}`, {method:'DELETE'})
          .then(() => { toast('دسترسی حذف شد'); window.__manageAccess(userId, ''); })
          .catch(e => toast(e.message, true));
      };
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // Hook into existing users nav
  const origUsersNav = document.querySelector('[data-view="users"]');
  if (origUsersNav) {
    origUsersNav.addEventListener('click', () => setTimeout(renderUserManagement, 200));
  }

  // ============ COMPANY MANAGEMENT (edit, deactivate) ============
  async function renderCompanyManagement() {
    const section = document.getElementById('view-companies');
    if (!section) return;
    try {
      const companies = await api('/companies');
      section.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
          <h1>شرکت‌ها</h1>
          <button class="btn primary small" onclick="window.__addCompany()">＋ شرکت جدید</button>
        </div>
        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>کد</th><th>نام</th><th>وضعیت</th><th>کارمندان</th><th>عملیات</th></tr></thead>
            <tbody>
              ${(companies||[]).map(c => `
                <tr>
                  <td class="font-mono"><strong>${esc(c.code)}</strong></td>
                  <td>${esc(c.name)}</td>
                  <td>${c.active?'<span style="color:#10b981;">✓ فعال</span>':'<span style="color:#ef4444;">✗ غیرفعال</span>'}</td>
                  <td><button class="btn soft small" onclick="window.__companyEmployees('${c.id}','${esc(c.name)}')">مشاهده</button></td>
                  <td style="display:flex;gap:4px;">
                    <button class="btn soft small" onclick="window.__editCompany('${c.id}','${esc(c.name)}','${esc(c.code)}')">✎ ویرایش</button>
                    ${c.active?`<button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__deactivateCompany('${c.id}','${esc(c.name)}')">✗ غیرفعال</button>`:''}
                  </td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        </div>
      `;
      window.__addCompany = () => {
        const code = prompt('کد شرکت:');
        if (!code) return;
        const name = prompt('نام شرکت:');
        if (!name) return;
        api('/companies', {method:'POST', body: JSON.stringify({code, name})})
          .then(() => { toast('شرکت ایجاد شد'); renderCompanyManagement(); })
          .catch(e => toast(e.message, true));
      };
      window.__editCompany = (id, name, code) => {
        const newName = prompt('نام جدید:', name);
        if (newName === null) return;
        const newCode = prompt('کد جدید:', code);
        if (newCode === null) return;
        api(`/companies/${id}`, {method:'PATCH', body: JSON.stringify({name: newName || name, code: newCode || code})})
          .then(() => { toast('شرکت ویرایش شد'); renderCompanyManagement(); })
          .catch(e => toast(e.message, true));
      };
      window.__deactivateCompany = (id, name) => {
        if (!confirm(`غیرفعال کردن «${name}»؟`)) return;
        api(`/companies/${id}`, {method:'DELETE'})
          .then(() => { toast('شرکت غیرفعال شد'); renderCompanyManagement(); })
          .catch(e => toast(e.message, true));
      };
      window.__companyEmployees = async (companyId, companyName) => {
        try {
          const employees = await api(`/companies/${companyId}/employees`);
          modal(`کارمندان ${esc(companyName)}`, '', employees.length > 0 ?
            `<div class="table-card"><table class="data-table"><thead><tr><th>نام</th><th>نام کاربری</th><th>نقش</th><th>وضعیت</th></tr></thead><tbody>${employees.map(e => `<tr><td>${esc(e.name)}</td><td>${esc(e.username)}</td><td>${roleLabels[e.role]||e.role}</td><td>${e.active?'فعال':'غیرفعال'}</td></tr>`).join('')}</tbody></table></div>` :
            '<p class="hint">هیچ کارمندی به این شرکت اختصاص ندارد.</p>');
        } catch(e) { toast(e.message, true); }
      };
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  const roleLabels = {ADMIN:'مدیر سامانه',CEO:'مدیرعامل',EMPLOYEE:'کارمند'};

  // Hook into existing companies nav
  const origCompaniesNav = document.querySelector('[data-view="companies"]');
  if (origCompaniesNav) {
    origCompaniesNav.addEventListener('click', () => setTimeout(renderCompanyManagement, 200));
  }

  // ============ CHANGE PASSWORD (in sidebar) ============
  function addChangePasswordButton() {
    const nav = document.getElementById('nav');
    if (!nav) return;
    const btn = document.createElement('button');
    btn.className = 'nav-item';
    btn.innerHTML = '<span class="nav-icon">🔑</span> تغییر رمز';
    btn.addEventListener('click', () => {
      const oldPass = prompt('رمز فعلی:');
      if (!oldPass) return;
      const newPass = prompt('رمز جدید (حداقل ۱۲ نویسه):');
      if (!newPass || newPass.length < 12) { toast('رمز باید حداقل ۱۲ نویسه باشد', true); return; }
      const confirmPass = prompt('تکرار رمز جدید:');
      if (newPass !== confirmPass) { toast('رمزها مطابقت ندارند', true); return; }
      api('/auth/change-password', {method:'POST', body: JSON.stringify({old_password: oldPass, new_password: newPass})})
        .then(() => { toast('رمز تغییر یافت؛ دوباره وارد شوید'); setTimeout(() => location.reload(), 2000); })
        .catch(e => toast(e.message, true));
    });
    nav.appendChild(btn);
  }
  setTimeout(addChangePasswordButton, 500);

  function modal(title, desc, body) {
    const root = document.getElementById('modalRoot');
    if (!root) { alert(body); return; }
    root.innerHTML = `<div class="modal-overlay" onclick="if(event.target===this)document.getElementById('modalRoot').innerHTML=''" style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:9999;display:flex;align-items:center;justify-content:center;padding:20px;"><div class="modal" style="background:#fff;border-radius:16px;max-width:600px;width:100%;max-height:80vh;overflow-y:auto;padding:24px;box-shadow:0 25px 50px rgba(0,0,0,0.3);"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;"><h2>${title}</h2><button onclick="document.getElementById('modalRoot').innerHTML=''" style="background:none;border:none;font-size:24px;cursor:pointer;">✕</button></div>${desc?`<p class="hint" style="margin-bottom:12px;">${desc}</p>`:''}${body}</div></div>`;
  }

  // ============ KPI REPORT VIEW (گزارش عملکرد تیم) ============
  // This view replaces the old simple/weighted performance report.
  // It computes total_score (0-100) per employee using active KPI weights
  // defined in settings → KPIs tab.
  let kpiReportPeriod = '';
  let kpiReportRole = 'EMPLOYEE';

  async function renderKPIReport() {
    // Try to render into #view-performance first (managed by app.js nav)
    // If user clicked on the dedicated KPI nav-item, render into #view-kpi-report
    let section = document.getElementById('view-performance');
    if (!section) section = document.getElementById('view-kpi-report');
    if (!section) return;
    const isAdmin = typeof state !== 'undefined' && (state.me?.role === 'ADMIN' || state.me?.role === 'CEO');
    if (!isAdmin) {
      // For non-admin users: show personal KPI breakdown
      return renderMyKPIs(section);
    }
    try {
      const qs = new URLSearchParams();
      if (kpiReportPeriod) qs.set('period', kpiReportPeriod);
      if (kpiReportRole) qs.set('role', kpiReportRole);
      const data = await api(`/performance/kpi-report${qs.toString()?'?'+qs.toString():''}`);
      const KPI_CAT_LABELS = {
        quality: 'کیفیت', ontime: 'به‌موقعی', volume: 'حجم کار',
        collaboration: 'همکاری', satisfaction: 'رضایت', custom: 'سفارشی',
      };
      const GRADE_COLORS = {'عالی':'#10b981','خوب':'#0b8f89','متوسط':'#f59e0b','ضعیف':'#ef4444'};
      const STATUS_COLORS = {PASS:'#10b981', FAIL:'#ef4444', PENDING:'#94a3b8'};
      section.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;flex-wrap:wrap;gap:8px;">
          <div>
            <h1>🎯 گزارش عملکرد تیم (مبتنی بر KPI)</h1>
            <p class="hint" style="margin-top:4px;">امتیاز هر کارمند از مجموع وزن‌دار شاخص‌های فعال محاسبه می‌شود. شاخص‌ها در تب تنظیمات قابل ویرایش هستند.</p>
          </div>
          <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
            <input id="kpiPeriod" placeholder="دوره (۱۴۰۵/۰۷)" value="${esc(kpiReportPeriod)}" style="padding:6px 10px;border:1px solid #cbd5e1;border-radius:8px;width:120px;font-size:13px;" />
            <select id="kpiRole" style="padding:6px 10px;border:1px solid #cbd5e1;border-radius:8px;font-size:13px;">
              <option value="EMPLOYEE" ${kpiReportRole==='EMPLOYEE'?'selected':''}>کارمندان</option>
              <option value="ADMIN" ${kpiReportRole==='ADMIN'?'selected':''}>مدیران</option>
              <option value="CEO" ${kpiReportRole==='CEO'?'selected':''}>مدیران‌عامل</option>
            </select>
            <button class="btn primary small" onclick="window.__refreshKPI()">به‌روزرسانی</button>
            <button class="btn soft small" onclick="window.__exportKPI()">⬇ خروجی CSV</button>
          </div>
        </div>

        <div class="stats-grid" style="margin-bottom:16px;">
          <div class="stat-card">
            <div class="stat-top"><span>تعداد افراد</span></div>
            <div class="stat-value">${data.employees.length}</div>
            <div class="stat-caption">در نقش ${esc(kpiReportRole)}</div>
          </div>
          <div class="stat-card">
            <div class="stat-top"><span>میانگین امتیاز</span></div>
            <div class="stat-value">${data.employees.length?Math.round(data.employees.reduce((s,e)=>s+e.total_score,0)/data.employees.length):0}<small style="font-size:14px;color:#64748b;">/۱۰۰</small></div>
            <div class="stat-caption">کل تیم</div>
          </div>
          <div class="stat-card">
            <div class="stat-top"><span>بهترین امتیاز</span></div>
            <div class="stat-value">${data.employees.length?Math.round(Math.max(...data.employees.map(e=>e.total_score))):0}<small style="font-size:14px;color:#64748b;">/۱۰۰</small></div>
            <div class="stat-caption">${data.employees.length?esc(data.employees[0].name):'—'}</div>
          </div>
          <div class="stat-card">
            <div class="stat-top"><span>شاخص‌های فعال</span></div>
            <div class="stat-value">${data.kpis.length}</div>
            <div class="stat-caption">مجموع وزن: ${data.total_weight}</div>
          </div>
        </div>

        <p class="hint" style="margin:8px 0;color:${data.total_weight===100?'#10b981':'#f59e0b'};font-size:13px;">
          ${data.total_weight===100?'✓ مجموع وزن شاخص‌ها ۱۰۰ است — امتیاز استاندارد':'⚠ مجموع وزن شاخص‌ها '+data.total_weight+' است. در تنظیمات وزن‌ها را به ۱۰۰ برسانید.'}
        </p>

        <div class="panel" style="margin-bottom:16px;">
          <div class="panel-head">
            <div><h3>📌 خلاصه شاخص‌ها در سطح تیم</h3><p>میانگین/کمینه/بیشینه مقدار هر شاخص در بین کارکنان</p></div>
          </div>
          <div class="table-card">
            <table class="data-table">
              <thead><tr><th>شاخص</th><th>دسته</th><th>هدف</th><th>وزن</th><th>میانگین تیم</th><th>کمینه</th><th>بیشینه</th></tr></thead>
              <tbody>
                ${(data.summary||[]).map(s => `
                  <tr>
                    <td><b>${esc(s.name)}</b></td>
                    <td><span class="pill" style="background:#e0f2fe;color:#0c4a6e;padding:2px 8px;border-radius:6px;font-size:11px;">${esc(KPI_CAT_LABELS[s.category]||s.category)}</span></td>
                    <td>${s.target_value} ${esc(s.unit)}</td>
                    <td><b>${s.weight}</b></td>
                    <td><b style="color:#0b8f89;">${s.avg_value} ${esc(s.unit)}</b></td>
                    <td style="color:#ef4444;">${s.min_value}</td>
                    <td style="color:#10b981;">${s.max_value}</td>
                  </tr>
                `).join('') || '<tr><td colspan="7" style="text-align:center;padding:20px;color:#64748b;">شاخص فعالی وجود ندارد — در تنظیمات اضافه کنید</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>

        <div class="panel">
          <div class="panel-head">
            <div><h3>👥 امتیاز کارکنان</h3><p>برای جزئیات شاخص‌های هر کارمند روی نام او کلیک کنید</p></div>
          </div>
          <div class="table-card">
            <table class="data-table">
              <thead><tr>
                <th>#</th><th>کارمند</th><th>امتیاز کل</th><th>پایه</th><th>شاخص‌های تحقق‌یافته</th><th>عملیات</th>
              </tr></thead>
              <tbody>
                ${data.employees.map((e, idx) => `
                  <tr>
                    <td>${idx+1}</td>
                    <td><b>${esc(e.name)}</b><div style="font-size:11px;color:#64748b;">@${esc(e.username)}</div></td>
                    <td>
                      <div style="display:flex;align-items:center;gap:8px;">
                        <div style="width:80px;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden;">
                          <div style="width:${Math.min(100,e.total_score)}%;height:100%;background:${GRADE_COLORS[e.grade]||'#94a3b8'};"></div>
                        </div>
                        <b style="color:${GRADE_COLORS[e.grade]||'#64748b'};font-size:16px;">${e.total_score}</b>
                        <small style="color:#64748b;">/۱۰۰</small>
                      </div>
                    </td>
                    <td><span class="pill" style="background:${GRADE_COLORS[e.grade]||'#94a3b8'};color:#fff;padding:4px 10px;border-radius:999px;font-size:11px;">${esc(e.grade)}</span></td>
                    <td><b style="color:#10b981;">${e.passed}</b><span style="color:#64748b;"> / ${e.total_kpis}</span></td>
                    <td>
                      <button class="btn soft small" onclick="window.__userKPIDetail('${e.user_id}')">🔍 جزئیات</button>
                    </td>
                  </tr>
                `).join('') || '<tr><td colspan="6" style="text-align:center;padding:20px;color:#64748b;">کارمندی در این نقش ثبت نشده است</td></tr>'}
              </tbody>
            </table>
          </div>
        </div>
        <p class="hint" style="margin-top:16px;font-size:13px;color:#64748b;">
          💡 برای ویرایش شاخص‌ها به تب «تنظیمات → شاخص‌های کلیدی (KPI)» بروید. تغییر وزن یا هدف شاخص بلافاصله در این گزارش اعمال می‌شود.
        </p>
      `;
      window.__refreshKPI = () => {
        const p = document.getElementById('kpiPeriod')?.value || '';
        const r = document.getElementById('kpiRole')?.value || 'EMPLOYEE';
        kpiReportPeriod = p.trim();
        kpiReportRole = r;
        renderKPIReport();
      };
      window.__exportKPI = () => exportKPIReportCSV(data);
      window.__userKPIDetail = (uid) => userKPIDetail(uid);
    } catch(e) {
      section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`;
    }
  }

  // For non-admin users: show personal KPI breakdown
  async function renderMyKPIs(section) {
    if (!section) return;
    try {
      const me = state.me || await api('/me');
      const data = await api(`/performance/kpi-report/${me.id}`);
      const GRADE_COLORS = {'عالی':'#10b981','خوب':'#0b8f89','متوسط':'#f59e0b','ضعیف':'#ef4444'};
      const STATUS_COLORS = {PASS:'#10b981', FAIL:'#ef4444', PENDING:'#94a3b8'};
      section.innerHTML = `
        <div style="margin-bottom:16px;">
          <h1>🎯 عملکرد شما (KPI)</h1>
          <p class="hint" style="margin-top:4px;">این امتیاز بر اساس شاخص‌های تعریف‌شده توسط مدیران محاسبه می‌شود.</p>
        </div>
        <div class="stats-grid" style="margin-bottom:16px;">
          <div class="stat-card">
            <div class="stat-top"><span>امتیاز کل</span></div>
            <div class="stat-value" style="color:${GRADE_COLORS[data.grade]||'#64748b'};">${data.total_score}<small style="font-size:14px;color:#64748b;">/۱۰۰</small></div>
            <div class="stat-caption"><span class="pill" style="background:${GRADE_COLORS[data.grade]||'#94a3b8'};color:#fff;padding:3px 10px;border-radius:999px;font-size:11px;">${esc(data.grade)}</span></div>
          </div>
          <div class="stat-card">
            <div class="stat-top"><span>شاخص‌های تحقق‌یافته</span></div>
            <div class="stat-value">${data.passed}<small style="font-size:14px;color:#64748b;"> / ${data.total_kpis}</small></div>
            <div class="stat-caption">از کل شاخص‌های فعال</div>
          </div>
          <div class="stat-card">
            <div class="stat-top"><span>مجموع وزن</span></div>
            <div class="stat-value">${data.weight_total}</div>
            <div class="stat-caption">از ۱۰۰</div>
          </div>
        </div>
        <div class="panel">
          <div class="panel-head"><div><h3>🔍 جزئیات شاخص‌ها</h3><p>مقدار فعلی، هدف و درصد تحقق</p></div></div>
          <div class="table-card">
            <table class="data-table">
              <thead><tr><th>شاخص</th><th>توضیحات</th><th>هدف</th><th>مقدار فعلی</th><th>درصد تحقق</th><th>وزن</th><th>سهم در امتیاز</th><th>وضعیت</th></tr></thead>
              <tbody>
                ${data.kpis.map(k => `
                  <tr>
                    <td><b>${esc(k.name)}</b></td>
                    <td style="max-width:200px;"><small style="color:#64748b;">${esc(k.description||'').substring(0,80)}</small></td>
                    <td>${k.target_value} ${esc(k.unit)} <small>(${esc(k.operator)})</small></td>
                    <td><b style="color:#0b8f89;font-size:15px;">${k.current_value} ${esc(k.unit)}</b></td>
                    <td>
                      <div style="display:flex;align-items:center;gap:6px;">
                        <div style="width:60px;height:6px;background:#f1f5f9;border-radius:3px;overflow:hidden;">
                          <div style="width:${Math.round(k.ratio*100)}%;height:100%;background:${STATUS_COLORS[k.status]||'#94a3b8'};"></div>
                        </div>
                        <small>${Math.round(k.ratio*100)}%</small>
                      </div>
                    </td>
                    <td><b>${k.weight}</b></td>
                    <td><b style="color:${STATUS_COLORS[k.status]||'#94a3b8'};">${k.contribution}</b></td>
                    <td>
                      <span style="padding:3px 8px;border-radius:6px;font-size:11px;background:${k.status==='PASS'?'#dcfce7':'#fee2e2'};color:${k.status==='PASS'?'#166534':'#991b1b'};">
                        ${k.status==='PASS'?'✓ محقق':'✗ زیر هدف'}
                      </span>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
      `;
    } catch(e) {
      section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`;
    }
  }

  async function userKPIDetail(uid) {
    try {
      const data = await api(`/performance/kpi-report/${uid}`);
      const GRADE_COLORS = {'عالی':'#10b981','خوب':'#0b8f89','متوسط':'#f59e0b','ضعیف':'#ef4444'};
      const STATUS_COLORS = {PASS:'#10b981', FAIL:'#ef4444', PENDING:'#94a3b8'};
      const root = document.getElementById('modalRoot');
      if (!root) { alert('modalRoot not found'); return; }
      root.innerHTML = `
        <div style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px;" onclick="if(event.target===this)window.__closeKPIDetail()">
          <div style="background:#fff;border-radius:14px;padding:24px;max-width:780px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 50px rgba(0,0,0,0.25);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">
              <h2 style="margin:0;">🔍 ${esc(data.name)} <small style="color:#64748b;font-weight:normal;">@${esc(data.username)}</small></h2>
              <button class="icon-btn" onclick="window.__closeKPIDetail()" style="background:#f1f5f9;border:none;width:32px;height:32px;border-radius:8px;cursor:pointer;">✕</button>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:16px;">
              <div style="background:#f8fafc;border-radius:10px;padding:14px;text-align:center;">
                <small style="color:#64748b;">امتیاز کل</small>
                <div style="font-size:28px;font-weight:700;color:${GRADE_COLORS[data.grade]||'#64748b'};">${data.total_score}<small style="font-size:14px;color:#64748b;">/۱۰۰</small></div>
                <span class="pill" style="background:${GRADE_COLORS[data.grade]||'#94a3b8'};color:#fff;padding:3px 10px;border-radius:999px;font-size:11px;">${esc(data.grade)}</span>
              </div>
              <div style="background:#f8fafc;border-radius:10px;padding:14px;text-align:center;">
                <small style="color:#64748b;">شاخص‌های محقق</small>
                <div style="font-size:28px;font-weight:700;color:#10b981;">${data.passed}<small style="font-size:14px;color:#64748b;"> / ${data.total_kpis}</small></div>
              </div>
              <div style="background:#f8fafc;border-radius:10px;padding:14px;text-align:center;">
                <small style="color:#64748b;">مجموع وزن</small>
                <div style="font-size:28px;font-weight:700;color:#0b8f89;">${data.weight_total}</div>
                <small style="color:#64748b;">از ۱۰۰</small>
              </div>
            </div>
            <table class="data-table" style="width:100%;border-collapse:collapse;">
              <thead><tr style="background:#f1f5f9;">
                <th style="padding:8px;text-align:right;">شاخص</th>
                <th>هدف</th><th>مقدار فعلی</th><th>درصد تحقق</th><th>وزن</th><th>سهم</th><th>وضعیت</th>
              </tr></thead>
              <tbody>
                ${data.kpis.map(k => `
                  <tr style="border-bottom:1px solid #f1f5f9;">
                    <td style="padding:8px;text-align:right;"><b>${esc(k.name)}</b><br><small style="color:#64748b;">${esc(k.description||'').substring(0,60)}</small></td>
                    <td style="text-align:center;">${k.target_value} ${esc(k.unit)}</td>
                    <td style="text-align:center;color:#0b8f89;font-weight:bold;">${k.current_value} ${esc(k.unit)}</td>
                    <td style="text-align:center;">${Math.round(k.ratio*100)}%</td>
                    <td style="text-align:center;">${k.weight}</td>
                    <td style="text-align:center;color:${STATUS_COLORS[k.status]||'#94a3b8'};font-weight:bold;">${k.contribution}</td>
                    <td style="text-align:center;">
                      <span style="padding:3px 8px;border-radius:6px;font-size:11px;background:${k.status==='PASS'?'#dcfce7':'#fee2e2'};color:${k.status==='PASS'?'#166534':'#991b1b'};">
                        ${k.status==='PASS'?'✓':'✗'}
                      </span>
                    </td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
            <button class="btn primary full" style="margin-top:18px;" onclick="window.__closeKPIDetail()">بستن</button>
          </div>
        </div>
      `;
      window.__closeKPIDetail = () => { root.innerHTML = ''; };
    } catch(e) { toast(e.message, true); }
  }

  function exportKPIReportCSV(data) {
    try {
      let csv = '\uFEFF' + 'ردیف,نام,نام کاربری,امتیاز کل,پایه,شاخص‌های محقق,مجموع شاخص‌ها\n';
      data.employees.forEach((e, idx) => {
        csv += `${idx+1},"${e.name}","${e.username}",${e.total_score},"${e.grade}",${e.passed},${e.total_kpis}\n`;
      });
      csv += '\n\nجزئیات شاخص‌ها به ازای هر کارمند\n';
      csv += 'کارمند,شاخص,دسته,هدف,مقدار فعلی,درصد تحقق,وزن,سهم,وضعیت\n';
      data.employees.forEach(e => {
        e.kpis.forEach(k => {
          csv += `"${e.name}","${k.name}","${k.category}",${k.target_value},${k.current_value},${Math.round(k.ratio*100)}%,${k.weight},${k.contribution},${k.status}\n`;
        });
      });
      const blob = new Blob([csv], {type:'text/csv;charset=utf-8'});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `kpi-report-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
      toast('گزارش CSV دانلود شد');
    } catch(e) { toast(e.message, true); }
  }
})();

  // ============ PERFORMANCE VIEW (ثبت عملکرد) - LEGACY ============
  // (Removed — view-performance-entries is now managed by renderPerformanceEntries in performance.js.
  //  Score/delegate/history buttons can be added to that view in future if needed.)

  // ============ SETTINGS VIEW ============
  let settingsTab = 'task-types';
  async function renderSettings() {
    const section = document.getElementById('view-settings');
    if (!section) return;
    try {
      const data = await api('/settings');
      const tabs = [
        {key:'kpis', label:'شاخص‌های کلیدی (KPI)', icon:'🎯'},
        {key:'task_types', label:'انواع تسک', icon:'📋'},
        {key:'process_types', label:'انواع فرآیند', icon:'🔄'},
        {key:'role_types', label:'انواع نقش', icon:'👥'},
        {key:'performance_types', label:'انواع عملکرد', icon:'✎'},
      ];
      section.innerHTML = `
        <h1>تنظیمات</h1>
        <p class="hint" style="margin-bottom:16px;">مدیریت شاخص‌های کلیدی عملکرد، انواع تسک، فرآیند، نقش و عملکرد — افزودن، ویرایش و حذف</p>
        <div class="tabs" style="margin-bottom:16px;">
          ${tabs.map(t => `<button class="tab ${settingsTab===t.key?'active':''}" onclick="window.__setSettingsTab('${t.key}')">${t.icon} ${t.label}</button>`).join('')}
        </div>
        <div id="settingsContent"></div>
      `;
      window.__setSettingsTab = (key) => { settingsTab = key; renderSettings(); };
      if (settingsTab === 'kpis') {
        renderKPITab(data);
      } else {
        renderSettingsTab(data, tabs);
      }
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // ============ KPI TAB ============
  const KPI_CATEGORIES = [
    {value:'quality', label:'کیفیت'},
    {value:'ontime', label:'به‌موقعی'},
    {value:'volume', label:'حجم کار'},
    {value:'collaboration', label:'همکاری'},
    {value:'satisfaction', label:'رضایت'},
    {value:'custom', label:'سفارشی'},
  ];
  const KPI_OPERATORS = [
    {value:'>=', label:'بزرگ‌تر یا مساوی ≥'},
    {value:'<=', label:'کوچک‌تر یا مساوی ≤'},
    {value:'>', label:'بزرگ‌تر >'},
    {value:'<', label:'کوچک‌تر <'},
    {value:'==', label:'مساوی ='},
  ];
  const KPI_FREQUENCIES = [
    {value:'daily', label:'روزانه'},
    {value:'weekly', label:'هفتگی'},
    {value:'monthly', label:'ماهانه'},
    {value:'quarterly', label:'فصلی'},
    {value:'yearly', label:'سالانه'},
  ];
  const KPI_ROLES = [
    {value:'EMPLOYEE', label:'کارمند'},
    {value:'ADMIN', label:'مدیر سامانه'},
    {value:'CEO', label:'مدیرعامل'},
  ];

  function renderKPITab(data) {
    const content = document.getElementById('settingsContent');
    if (!content) return;
    const kpis = data.kpis || [];
    const totalWeight = kpis.reduce((s, k) => s + (k.weight||0), 0);
    const activeCount = kpis.filter(k => k.active).length;
    let html = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <h3>🎯 شاخص‌های کلیدی عملکرد (${kpis.length} — ${activeCount} فعال)</h3>
        <button class="btn primary small" onclick="window.__editKPI()">＋ شاخص جدید</button>
      </div>
      <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;">
        <span class="pill" style="background:#0b8f89;color:#fff;padding:4px 12px;border-radius:999px;font-size:12px;">مجموع وزن: ${totalWeight}</span>
        <span class="pill" style="background:${totalWeight===100?'#10b981':'#f59e0b'};color:#fff;padding:4px 12px;border-radius:999px;font-size:12px;">${totalWeight===100?'وزن‌دهی استاندارد':'وزن باید ۱۰۰ باشد'}</span>
      </div>
      <p class="hint" style="margin-bottom:12px;color:#64748b;font-size:13px;">شاخص‌های کلیدی عملکرد (KPI) معیارهای ارزیابی پرسنل هستند. وزن کل باید ۱۰۰ باشد. مدیر می‌تواند شاخص دلخواه بسازد.</p>
      <div class="table-card">
        <table class="data-table">
          <thead><tr>
            <th>نام شاخص</th><th>دسته</th><th>هدف</th><th>وزن</th><th>دوره</th><th>نقش هدف</th><th>وضعیت</th><th>عملیات</th>
          </tr></thead>
          <tbody>
            ${kpis.map(k => {
              const cat = (KPI_CATEGORIES.find(c=>c.value===k.category)||{label:k.category}).label;
              const op = (KPI_OPERATORS.find(o=>o.value===k.target_operator)||{label:k.target_operator}).label;
              const freq = (KPI_FREQUENCIES.find(f=>f.value===k.frequency)||{label:k.frequency}).label;
              const role = (KPI_ROLES.find(r=>r.value===k.owner_role)||{label:k.owner_role}).label;
              return `
              <tr>
                <td><b>${esc(k.name)}</b><div style="font-size:11px;color:#64748b;">${esc(k.description||'').substring(0,80)}</div></td>
                <td><span class="pill" style="background:#e0f2fe;color:#0c4a6e;padding:2px 8px;border-radius:6px;font-size:11px;">${esc(cat)}</span></td>
                <td><b>${op}</b> ${k.target_value} ${esc(k.unit)}</td>
                <td><b style="color:${k.weight>=20?'#0b8f89':'#64748b'};">${k.weight}</b></td>
                <td>${esc(freq)}</td>
                <td>${esc(role)}</td>
                <td>${k.active?('<span style="color:#10b981;">✓ فعال</span>'):('<span style="color:#ef4444;">✗ غیرفعال</span>')}</td>
                <td style="display:flex;gap:4px;flex-wrap:wrap;">
                  <button class="btn soft small" onclick="window.__editKPI('${k.id}')">✎ ویرایش</button>
                  <button class="btn small" style="background:#e0f2fe;color:#0369a1;" onclick="window.__evaluateKPI('${k.id}')">📊 ارزیابی</button>
                  <button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__deleteKPI('${k.id}')">✗ حذف</button>
                </td>
              </tr>`;
            }).join('') || '<tr><td colspan="8" style="text-align:center;padding:20px;color:#64748b;">شاخصی وجود ندارد — روی «شاخص جدید» کلیک کنید</td></tr>'}
          </tbody>
        </table>
      </div>
    `;
    content.innerHTML = html;
    window.__editKPI = (id) => kpiModal(id);
    window.__deleteKPI = (id) => deleteKPI(id);
    window.__evaluateKPI = (id) => evaluateKPI(id);
  }

  async function kpiModal(id) {
    let kpi = null;
    if (id) {
      const data = await api('/settings');
      kpi = (data.kpis||[]).find(k => k.id === id);
      if (!kpi) return toast('شاخص پیدا نشد', true);
    }
    const root = document.getElementById('modalRoot');
    const esc2 = (s) => String(s??'').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const sel = (opts, val) => opts.map(o => `<option value="${o.value}" ${o.value===val?'selected':''}>${o.label}</option>`).join('');
    root.innerHTML = `
      <div style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px;" onclick="if(event.target===this)window.__closeKPI()">
        <div style="background:#fff;border-radius:14px;padding:24px;max-width:620px;width:100%;max-height:90vh;overflow-y:auto;box-shadow:0 20px 50px rgba(0,0,0,0.25);">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">
            <h2 style="margin:0;">${kpi?'✎ ویرایش شاخص':'＋ شاخص جدید'}</h2>
            <button class="icon-btn" onclick="window.__closeKPI()" style="background:#f1f5f9;border:none;width:32px;height:32px;border-radius:8px;cursor:pointer;">✕</button>
          </div>
          <form id="kpiForm" style="display:grid;gap:12px;">
            <div>
              <label style="font-size:13px;font-weight:600;color:#334155;">نام شاخص *</label>
              <input name="name" required maxlength="120" value="${esc2(kpi?.name||'')}" placeholder="مثلاً: کیفیت کار" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;" />
            </div>
            <div>
              <label style="font-size:13px;font-weight:600;color:#334155;">توضیحات</label>
              <textarea name="description" maxlength="1000" placeholder="توضیح کوتاه از شاخص" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;min-height:60px;">${esc2(kpi?.description||'')}</textarea>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <label style="font-size:13px;font-weight:600;color:#334155;">دسته</label>
                <select name="category" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;">
                  ${sel(KPI_CATEGORIES, kpi?.category||'quality')}
                </select>
              </div>
              <div>
                <label style="font-size:13px;font-weight:600;color:#334155;">دوره ارزیابی</label>
                <select name="frequency" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;">
                  ${sel(KPI_FREQUENCIES, kpi?.frequency||'monthly')}
                </select>
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;">
              <div>
                <label style="font-size:13px;font-weight:600;color:#334155;">عملگر هدف</label>
                <select name="target_operator" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;">
                  ${sel(KPI_OPERATORS, kpi?.target_operator||'>=')}
                </select>
              </div>
              <div>
                <label style="font-size:13px;font-weight:600;color:#334155;">مقدار هدف</label>
                <input name="target_value" type="number" step="0.01" min="0" max="100000" value="${kpi?.target_value??100}" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;" />
              </div>
              <div>
                <label style="font-size:13px;font-weight:600;color:#334155;">واحد</label>
                <input name="unit" maxlength="20" value="${esc2(kpi?.unit||'%')}" placeholder="%, دقیقه, عدد" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;" />
              </div>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">
              <div>
                <label style="font-size:13px;font-weight:600;color:#334155;">وزن (۱ تا ۱۰۰)</label>
                <input name="weight" type="number" min="1" max="100" value="${kpi?.weight??10}" style="width:100%;padding:8px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;" />
                <small style="color:#64748b;font-size:11px;">مجموع وزن همه شاخص‌ها باید ۱۰۰ باشد</small>
              </div>
              <div>
                <label style="font-size:13px;font-weight:600;color:#334155;">نقش هدف</label>
                <select name="owner_role" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;">
                  ${sel(KPI_ROLES, kpi?.owner_role||'EMPLOYEE')}
                </select>
              </div>
            </div>
            <div>
              <label style="font-size:13px;font-weight:600;color:#334155;">فرمول محاسبه (اختیاری)</label>
              <input name="formula" maxlength="500" value="${esc2(kpi?.formula||'')}" placeholder="مثلاً: AVG(performance_scores_v2.score)" style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;margin-top:4px;font-family:monospace;font-size:12px;" />
              <small style="color:#64748b;font-size:11px;">برای شاخص‌های سفارشی — در نسخه فعلی دسته از پیش تعریف‌شده استفاده کنید</small>
            </div>
            <label style="display:flex;align-items:center;gap:8px;font-size:14px;">
              <input type="checkbox" name="active" ${(!kpi || kpi.active)?'checked':''} style="width:18px;height:18px;" />
              <span>فعال</span>
            </label>
            <div style="display:flex;gap:8px;justify-content:flex-end;margin-top:8px;">
              <button type="button" class="btn soft" onclick="window.__closeKPI()">انصراف</button>
              <button type="submit" class="btn primary">ذخیره شاخص</button>
            </div>
          </form>
        </div>
      </div>
    `;
    window.__closeKPI = () => { root.innerHTML = ''; };
    document.getElementById('kpiForm').addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const fd = new FormData(ev.target);
      const body = {
        name: fd.get('name'),
        category: fd.get('category'),
        description: fd.get('description'),
        target_value: parseFloat(fd.get('target_value')),
        target_operator: fd.get('target_operator'),
        unit: fd.get('unit'),
        weight: parseInt(fd.get('weight'), 10),
        frequency: fd.get('frequency'),
        owner_role: fd.get('owner_role'),
        formula: fd.get('formula'),
        active: fd.get('active') === 'on',
      };
      try {
        if (kpi) {
          await api(`/settings/kpis/${kpi.id}`, {method:'PATCH', body: JSON.stringify(body)});
          toast('شاخص ویرایش شد');
        } else {
          await api('/settings/kpis', {method:'POST', body: JSON.stringify(body)});
          toast('شاخص افزوده شد');
        }
        window.__closeKPI();
        renderSettings();
      } catch(e) { toast(e.message, true); }
    });
  }

  function deleteKPI(id) {
    if (!confirm('حذف این شاخص کلیدی؟ این عمل قابل بازگشت نیست.')) return;
    api(`/settings/kpis/${id}`, {method:'DELETE'})
      .then(()=>{toast('شاخص حذف شد');renderSettings()})
      .catch(e=>toast(e.message,true));
  }

  async function evaluateKPI(id) {
    let userId = prompt('شناسه کاربر (اختیاری — برای ارزیابی فردی):', '');
    const url = `/settings/kpis/${id}/evaluate` + (userId ? `?user_id=${encodeURIComponent(userId)}` : '');
    try {
      const r = await api(url);
      const root = document.getElementById('modalRoot');
      root.innerHTML = `
        <div style="position:fixed;inset:0;background:rgba(0,0,0,0.5);z-index:200;display:flex;align-items:center;justify-content:center;padding:16px;" onclick="if(event.target===this)window.__closeKPIEval()">
          <div style="background:#fff;border-radius:14px;padding:24px;max-width:480px;width:100%;box-shadow:0 20px 50px rgba(0,0,0,0.25);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:18px;">
              <h2 style="margin:0;">📊 ارزیابی: ${esc(r.name)}</h2>
              <button class="icon-btn" onclick="window.__closeKPIEval()" style="background:#f1f5f9;border:none;width:32px;height:32px;border-radius:8px;cursor:pointer;">✕</button>
            </div>
            <div style="display:grid;gap:10px;font-size:14px;">
              <div style="display:flex;justify-content:space-between;padding:10px;background:#f8fafc;border-radius:8px;"><span>دسته:</span><b>${esc(r.category)}</b></div>
              <div style="display:flex;justify-content:space-between;padding:10px;background:#f8fafc;border-radius:8px;"><span>مقدار هدف:</span><b>${r.target_value} ${esc(r.unit)} (${esc(r.operator)})</b></div>
              <div style="display:flex;justify-content:space-between;padding:10px;background:#f8fafc;border-radius:8px;"><span>مقدار فعلی:</span><b style="color:#0b8f89;font-size:18px;">${r.current_value.toFixed(2)} ${esc(r.unit)}</b></div>
              <div style="display:flex;justify-content:space-between;padding:12px;background:${r.status==='PASS'?'#dcfce7':'#fee2e2'};border-radius:8px;">
                <span>وضعیت:</span>
                <b style="color:${r.status==='PASS'?'#166534':'#991b1b'};font-size:16px;">${r.status==='PASS'?'✓ هدف محقق':'✗ زیر هدف'}</b>
              </div>
              ${r.period ? `<div style="display:flex;justify-content:space-between;padding:10px;background:#f8fafc;border-radius:8px;"><span>دوره:</span><b>${esc(r.period)}</b></div>` : ''}
            </div>
            <button class="btn primary full" style="margin-top:16px;" onclick="window.__closeKPIEval()">بستن</button>
          </div>
        </div>
      `;
      window.__closeKPIEval = () => { root.innerHTML = ''; };
    } catch(e) { toast(e.message, true); }
  }

  function renderSettingsTab(data, tabs) {
    const content = document.getElementById('settingsContent');
    if (!content) return;
    const current = data[settingsTab] || [];
    const tabInfo = tabs.find(t => t.key === settingsTab) || {};
    const fields = {
      task_types: ['name','description','icon'],
      process_types: ['name','description','default_steps'],
      role_types: ['name','description','permissions'],
      performance_types: ['name','category','description'],
    };
    const fieldLabels = {
      name: 'نام', description: 'توضیحات', icon: 'آیکن', default_steps: 'مراحل پیش‌فرض',
      permissions: 'دسترسی‌ها', category: 'دسته'
    };
    let html = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h3>${tabInfo.icon||''} ${tabInfo.label||''} (${current.length})</h3>
        <button class="btn primary small" onclick="window.__addSetting()">＋ افزودن</button>
      </div>
      <div class="table-card">
        <table class="data-table">
          <thead><tr>${(fields[settingsTab]||[]).map(f => `<th>${fieldLabels[f]||f}</th>`).join('')}<th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${current.map(item => `
              <tr>
                ${(fields[settingsTab]||[]).map(f => `<td>${esc(String(item[f]||'—')).substring(0,60)}</td>`).join('')}
                <td>${item.active?'<span style="color:#10b981;">✓ فعال</span>':'<span style="color:#ef4444;">✗ غیرفعال</span>'}</td>
                <td style="display:flex;gap:4px;">
                  <button class="btn soft small" onclick="window.__editSetting('${item.id}','${settingsTab}')">✎ ویرایش</button>
                  <button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__deleteSetting('${item.id}','${settingsTab}')">✗ حذف</button>
                </td>
              </tr>
            `).join('') || '<tr><td colspan="10" style="text-align:center;padding:20px;color:#64748b;">موردی وجود ندارد</td></tr>'}
          </tbody>
        </table>
      </div>
    `;
    content.innerHTML = html;

    window.__addSetting = () => {
      const f = fields[settingsTab] || [];
      const body = {};
      f.forEach(field => {
        const val = prompt(`${fieldLabels[field]||field}:`, field === 'icon' ? '📋' : field === 'default_steps' ? '3' : field === 'permissions' ? '[]' : field === 'category' ? 'general' : '');
        if (val !== null) body[field] = val;
      });
      body.active = true;
      api(`/settings/${settingsTab}`, {method:'POST', body: JSON.stringify(body)})
        .then(()=>{toast('افزوده شد');renderSettings()})
        .catch(e=>toast(e.message,true));
    };
    window.__editSetting = async (id, tab) => {
      const data = await api('/settings');
      const item = (data[tab]||[]).find(i => i.id === id);
      if (!item) return;
      const f = fields[tab] || [];
      const body = {};
      f.forEach(field => {
        const val = prompt(`${fieldLabels[field]||field}:`, String(item[field]||''));
        if (val !== null) body[field] = val;
      });
      body.active = item.active === 1 || item.active === true;
      api(`/settings/${tab}/${id}`, {method:'PATCH', body: JSON.stringify(body)})
        .then(()=>{toast('ویرایش شد');renderSettings()})
        .catch(e=>toast(e.message,true));
    };
    window.__deleteSetting = (id, tab) => {
      if (!confirm('حذف این مورد؟')) return;
      api(`/settings/${tab}/${id}`, {method:'DELETE'})
        .then(()=>{toast('حذف شد');renderSettings()})
        .catch(e=>toast(e.message,true));
    };
  }
