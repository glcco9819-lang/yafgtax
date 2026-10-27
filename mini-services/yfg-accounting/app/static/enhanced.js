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
      {view: 'performance', icon: '✎', label: 'ثبت عملکرد', admin: false},
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
    ['kanban','performance','time','chat','automations','iso30414','settings'].forEach(v => {
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
      case 'performance': renderPerformance(); break;
      case 'time': renderTimeTracking(); break;
      case 'chat': renderChat(); break;
      case 'automations': renderAutomations(); break;
      case 'iso30414': renderISO30414(); break;
      case 'settings': renderSettings(); break;
    }
  }

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
})();

  // ============ PERFORMANCE VIEW (ثبت عملکرد) ============
  async function renderPerformance() {
    const section = document.getElementById('view-performance');
    if (!section) return;
    try {
      const entries = await api('/performance-entries/v2');
      const isAdmin = typeof state !== 'undefined' && (state.me?.role === 'ADMIN' || state.me?.role === 'CEO');
      const perfTypes = await api('/settings/performance-types').catch(() => []);
      section.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px;">
          <h1>ثبت عملکرد</h1>
          <button class="btn primary small" onclick="window.__newPerf()">＋ ثبت عملکرد جدید</button>
        </div>
        <p class="hint" style="margin-bottom:12px;">هر کاربر می‌تواند عملکرد خود را ثبت و به مدیر ارجاع دهد. مدیر می‌تواند نمره ۰-۱۰۰ بدهد.</p>
        <div class="table-card">
          <table class="data-table">
            <thead><tr><th>عنوان</th><th>نوع</th><th>تاریخ</th><th>مدت</th><th>کاربر</th><th>وضعیت</th><th>نمره</th><th>عملیات</th></tr></thead>
            <tbody>
              ${(entries||[]).map(e => `
                <tr>
                  <td><strong>${esc(e.title)}</strong></td>
                  <td><span class="tag">${esc(e.category)}</span></td>
                  <td>${esc(e.work_date)}</td>
                  <td>${Math.floor(e.duration_minutes/60)}س ${e.duration_minutes%60}د</td>
                  <td>${esc(e.user_name||'—')}</td>
                  <td>${e.status==='APPROVED'?'<span style="color:#10b981;">✓ تأیید</span>':e.status==='NEEDS_EDIT'?'<span style="color:#ef4444;">✗ اصلاح</span>':'<span style="color:#f59e0b;">○ در انتظار</span>'}</td>
                  <td>${e.latest_score!==null&&e.latest_score!==undefined?`<strong>${e.latest_score}/۱۰۰</strong>`:'—'}</td>
                  <td style="display:flex;gap:4px;">
                    <button class="btn soft small" onclick="window.__perfHistory('${e.id}')">تاریخچه</button>
                    ${isAdmin?`<button class="btn soft small" onclick="window.__scorePerf('${e.id}')">امتیاز</button>`:''}
                    <button class="btn soft small" onclick="window.__delegatePerf('${e.id}')">ارجاع</button>
                  </td>
                </tr>
              `).join('') || '<tr><td colspan="8" style="text-align:center;padding:20px;color:#64748b;">هنوز عملکردی ثبت نشده</td></tr>'}
            </tbody>
          </table>
        </div>
      `;
      window.__newPerf = () => {
        const title = prompt('عنوان عملکرد:');
        if (!title) return;
        const category = prompt('نوع (حسابداری/مالیاتی/حسابرسی/اداری/مشاوره/سایر):', 'حسابداری');
        if (!category) return;
        const duration = prompt('مدت (دقیقه):', '60');
        if (!duration) return;
        const date = prompt('تاریخ (۱۴۰۵/۰۸/۰۱):', new Intl.DateTimeFormat('fa-IR-u-ca-persian').format(new Date()));
        const stepsStr = prompt('مراحل چک‌لیست (با کاما جدا کنید، حداکثر ۵):', 'جمع‌آوری, ثبت, کنترل');
        const steps = stepsStr ? stepsStr.split(',').map(s=>s.trim()).filter(Boolean) : [];
        api('/performance-entries/v2', {method:'POST', body: JSON.stringify({
          work_date: date || '1405/08/01', category, title, description: '', duration_minutes: parseInt(duration)||60, checklist_steps: steps
        })}).then(()=>{toast('عملکرد ثبت شد');renderPerformance()}).catch(e=>toast(e.message,true));
      };
      window.__scorePerf = (id) => {
        const score = prompt('نمره (۰-۱۰۰):', '80');
        if (score === null) return;
        const reason = prompt('دلیل:', '');
        api(`/performance-entries/${id}/score`, {method:'POST', body: JSON.stringify({score: parseInt(score)||0, reason: reason||''})})
          .then(()=>{toast('امتیاز ثبت شد');renderPerformance()}).catch(e=>toast(e.message,true));
      };
      window.__delegatePerf = (id) => {
        const userId = prompt('شناسه کاربر هدف:');
        if (!userId) return;
        const scope = prompt('محدوده ارجاع:', '');
        api(`/performance-entries/${id}/delegate`, {method:'POST', body: JSON.stringify({to_user: userId, scope: scope||''})})
          .then(()=>{toast('ارجاع شد');renderPerformance()}).catch(e=>toast(e.message,true));
      };
      window.__perfHistory = async (id) => {
        try {
          const h = await api(`/performance-entries/${id}/history`);
          let html = '<div style="max-height:400px;overflow-y:auto;">';
          if (h.events && h.events.length) {
            html += '<h4 style="margin-bottom:8px;">رویدادها</h4>';
            h.events.forEach(e => html += `<div style="padding:6px 0;border-bottom:1px solid #f1f5f9;"><b>${esc(e.actor_name)}</b> → ${esc(e.action)} <small style="color:#94a3b8;">${timeFmt(e.created_at)}</small></div>`);
          }
          if (h.scores && h.scores.length) {
            html += '<h4 style="margin:12px 0 8px;">امتیازها</h4>';
            h.scores.forEach(s => html += `<div style="padding:6px 0;border-bottom:1px solid #f1f5f9;"><b>${esc(s.manager_name)}</b>: ${s.score}/۱۰۰ <small>${esc(s.reason||'')}</small></div>`);
          }
          if (h.checklist && h.checklist.length) {
            html += '<h4 style="margin:12px 0 8px;">چک‌لیست</h4>';
            h.checklist.forEach(c => html += `<div style="padding:4px 0;">${c.is_done?'✓':'○'} مرحله ${c.step_number}: ${esc(c.title)}</div>`);
          }
          if (h.delegations && h.delegations.length) {
            html += '<h4 style="margin:12px 0 8px;">ارجاع‌ها</h4>';
            h.delegations.forEach(d => html += `<div style="padding:4px 0;">→ ${esc(d.to_name)} — ${esc(d.scope||'')}</div>`);
          }
          html += '</div>';
          modal('تاریخچه عملکرد', '', html);
        } catch(e) { toast(e.message, true); }
      };
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // ============ SETTINGS VIEW ============
  let settingsTab = 'task-types';
  async function renderSettings() {
    const section = document.getElementById('view-settings');
    if (!section) return;
    try {
      const data = await api('/settings');
      const tabs = [
        {key:'task_types', label:'انواع تسک', icon:'📋'},
        {key:'process_types', label:'انواع فرآیند', icon:'🔄'},
        {key:'role_types', label:'انواع نقش', icon:'👥'},
        {key:'performance_types', label:'انواع عملکرد', icon:'✎'},
      ];
      section.innerHTML = `
        <h1>تنظیمات</h1>
        <p class="hint" style="margin-bottom:16px;">مدیریت انواع تسک، فرآیند، نقش و عملکرد — افزودن، ویرایش و حذف</p>
        <div class="tabs" style="margin-bottom:16px;">
          ${tabs.map(t => `<button class="tab ${settingsTab===t.key?'active':''}" onclick="window.__setSettingsTab('${t.key}')">${t.icon} ${t.label}</button>`).join('')}
        </div>
        <div id="settingsContent"></div>
      `;
      window.__setSettingsTab = (key) => { settingsTab = key; renderSettings(); };
      renderSettingsTab(data, tabs);
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
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
