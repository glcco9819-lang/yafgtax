// YFG Enhanced Features v2.0 - Fixed version
// Adds: Dashboard Charts, Kanban View, Time Tracking, Chat, Automations, ISO 30414

(function() {
  'use strict';
  
  const CHART_COLORS = ['#0b8f89','#f59e0b','#ef4444','#8b5cf6','#3b82f6','#10b981','#ec4899','#f97316'];
  let charts = {};
  let timerInterval = null;
  let timerStart = null;
  let currentChannel = null;

  // Retry mechanism - runs immediately (defer scripts run after DOM parse), with fallback retries
  let retries = 0;
  const tryInit = setInterval(() => {
    retries++;
    if (retries > 50) { clearInterval(tryInit); return; }
    const nav = document.getElementById('nav');
    const main = document.querySelector('main');
    if (nav && main) {
      // Check if already initialized
      if (nav.querySelector('[data-init-enhanced]')) { clearInterval(tryInit); return; }
      clearInterval(tryInit);
      nav.setAttribute('data-init-enhanced', '1');
      init();
    }
  }, 120);
  if (document.readyState !== 'loading') {
    const nav = document.getElementById('nav');
    const main = document.querySelector('main');
    if (nav && main && !nav.querySelector('[data-init-enhanced]')) {
      clearInterval(tryInit);
      nav.setAttribute('data-init-enhanced', '1');
      setTimeout(init, 0);
    }
  }

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
  // All primary nav items now live statically in index.html (so they always show,
  // even if this file is served stale from cache). Only safety-net additions remain.
  function addNavItems() {
    const nav = document.getElementById('nav');
    if (!nav) return;
    const items = [
      {view: 'kpi-report', icon: '🎯', label: 'گزارش KPI', admin: true},
    ];
    items.forEach(item => {
      if (nav.querySelector(`[data-view="${item.view}"]`)) return;
      const btn = document.createElement('button');
      btn.className = 'nav-item' + (item.admin ? ' admin-only' : '');
      btn.dataset.view = item.view;
      btn.style.display = 'none'; // reports live under the گزارشات tab now
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
    ['customers'].forEach(v => {
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

  // Also override app.js renderPerformance to keep legacy view working (score cards)
  // The گزارشات tab renders its own richer sub-reports; no override needed here.

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

  // ============ Chat — Full In-App Messenger ============
  let chatPollTimer = null;
  let chatCurrentChannel = null;
  let chatCurrentMessages = [];
  async function renderChat() {
    const section = document.getElementById('view-chat');
    if (!section) return;
    try {
      // Stop any previous polling
      if (chatPollTimer) { clearInterval(chatPollTimer); chatPollTimer = null; }
      const isAdmin = state.me?.role === 'ADMIN' || state.me?.role === 'CEO';
      const channels = await api('/chat/channels');
      const allUsers = await api('/chat/users');
      const renderChannelList = () => (channels||[]).map(ch=>{
        const isDirect = ch.kind === 'DIRECT';
        const icon = isDirect ? '👤' : '👥';
        const unread = ch.unread_count > 0 ? `<span style="background:#ef4444;color:#fff;font-size:10px;padding:1px 7px;border-radius:10px;margin-right:6px;">${ch.unread_count}</span>` : '';
        return `<div onclick="window.__chatOpen('${ch.id}')" id="chatItem-${ch.id}" style="padding:11px 12px;border-radius:10px;cursor:pointer;margin-bottom:6px;background:#fff;transition:all .15s;${chatCurrentChannel===ch.id?'border-right:3px solid #0b8f89;background:#f0fdfa;':''}">
          <div style="display:flex;align-items:center;gap:8px;font-size:13px;font-weight:600;">
            <span style="font-size:14px;">${icon}</span>
            <span style="flex:1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">${esc(ch.display_name||ch.name||'گفتگو')}</span>
            ${unread}
          </div>
          <div style="font-size:11px;color:#64748b;margin-top:4px;">${ch.message_count||0} پیام</div>
        </div>`;
      }).join('') || '<p style="text-align:center;color:#94a3b8;font-size:12px;padding:16px 8px;">گفتگویی وجود ندارد</p>';
      section.innerHTML = `
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
          <h1 style="margin:0;">💬 گفتگو</h1>
          <div style="display:flex;gap:8px;">
            <button class="btn primary small" onclick="window.__chatNewDM()">＋ گفتگو مستقیم</button>
            <button class="btn soft small" onclick="window.__chatNewGroup()">👥 گروه جدید</button>
          </div>
        </div>
        <div style="display:flex;gap:14px;height:calc(100vh - 240px);border:1px solid #e2e8f0;border-radius:14px;overflow:hidden;background:#fff;">
          <div style="width:260px;flex-shrink:0;background:#f8fafc;border-left:1px solid #e2e8f0;overflow-y:auto;padding:10px;">
            ${renderChannelList()}
          </div>
          <div style="flex:1;display:flex;flex-direction:column;min-width:0;">
            <div id="chatHeader" style="padding:12px 16px;border-bottom:1px solid #e2e8f0;display:flex;justify-content:space-between;align-items:center;background:#fff;">
              <div id="chatHeaderTitle" style="font-weight:600;font-size:14px;">یک گفتگو را انتخاب کنید</div>
              <div id="chatHeaderActions" style="display:flex;gap:6px;"></div>
            </div>
            <div id="chatMessages" style="flex:1;overflow-y:auto;padding:14px 16px;background:#fafbfc;">
              <p style="text-align:center;color:#94a3b8;padding-top:60px;font-size:13px;">برای شروع گفتگو، یک مکالمه را از لیست کناری انتخاب کنید یا گفتگوی جدید بسازید.</p>
            </div>
            <div id="chatComposer" style="padding:10px 14px;border-top:1px solid #e2e8f0;background:#fff;display:flex;gap:8px;align-items:flex-end;">
              <label id="chatAttachBtn" style="cursor:pointer;padding:8px 10px;background:#f1f5f9;border-radius:8px;font-size:18px;color:#475569;" title="ضمیمه فایل">📎<input type="file" id="chatFileInput" style="display:none;" onchange="window.__chatUpload(this)"></label>
              <textarea id="chatInput" class="field" placeholder="پیام بنویسید... (Enter برای ارسال، Shift+Enter برای سطر جدید)" rows="1" style="flex:1;resize:none;max-height:100px;font-size:13px;padding:8px 12px;" onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();window.__chatSend()}"></textarea>
              <button class="btn primary" onclick="window.__chatSend()" style="padding:8px 16px;">➤</button>
            </div>
          </div>
        </div>
        <p class="hint" style="margin-top:10px;font-size:11px;color:#94a3b8;">فایل‌های مجاز: تصویر، PDF، اکسل، ورد، فشرده — حداکثر ۲۵ مگابایت</p>
      `;

      // Channel open
      window.__chatOpen = async (chId) => {
        chatCurrentChannel = chId;
        // Update selected styling
        $$('[id^="chatItem-"]').forEach(e=>e.style.background='#fff');
        const item = document.getElementById(`chatItem-${chId}`);
        if (item) { item.style.background='#f0fdfa'; item.style.borderRight='3px solid #0b8f89'; }
        try {
          const ch = await api(`/chat/channels/${chId}`);
          const msgs = await api(`/chat/channels/${chId}/messages`);
          chatCurrentMessages = msgs || [];
          // Header
          const isGroup = ch.kind === 'GROUP';
          const isOwner = isAdmin || ch.created_by === state.me.id;
          $('#chatHeaderTitle').innerHTML = `${isGroup?'👥':'👤'} ${esc(ch.display_name||ch.name||'گفتگو مستقیم')}`;
          $('#chatHeaderActions').innerHTML = isGroup ? `
            ${isOwner?`<button class="btn small soft" onclick="window.__chatRename('${chId}','${esc(ch.name)}')">✎ نام</button>`:''}
            ${isOwner?`<button class="btn small soft" onclick="window.__chatAddMember('${chId}')">＋ عضو</button>`:''}
            <button class="btn small soft" onclick="window.__chatShowMembers('${chId}')" title="اعضای گروه">👥 ${ch.members?.length||0}</button>
          ` : `<span style="font-size:12px;color:#64748b;">گفتگو مستقیم</span>`;
          // Render messages
          renderChatMessages(msgs || []);
          // Mark as read
          api(`/chat/channels/${chId}/read`, {method:'POST'}).then(()=>renderChat()).catch(()=>{});
        } catch(e) { toast(e.message, true); }
      };

      // Send message
      window.__chatSend = async () => {
        if (!chatCurrentChannel) return toast('ابتدا یک گفتگو را انتخاب کنید', true);
        const i = document.getElementById('chatInput');
        const body = i.value.trim();
        if (!body) return;
        i.value = '';
        i.style.height = 'auto';
        try {
          await api(`/chat/channels/${chatCurrentChannel}/messages`, {method:'POST', body:JSON.stringify({body})});
          await window.__chatOpen(chatCurrentChannel);
        } catch(e) { toast(e.message, true); }
      };

      // Upload file
      window.__chatUpload = async (input) => {
        if (!input.files || !input.files[0]) return;
        if (!chatCurrentChannel) {
          toast('ابتدا یک گفتگو را انتخاب کنید', true);
          input.value = '';
          return;
        }
        const fd = new FormData();
        fd.append('file', input.files[0]);
        try {
          const up = await api('/chat/upload', {method:'POST', body: fd});
          // Send a message with attachment_id and empty body
          await api(`/chat/channels/${chatCurrentChannel}/messages`, {
            method:'POST', body: JSON.stringify({body: '', attachment_id: up.attachment_id})
          });
          await window.__chatOpen(chatCurrentChannel);
        } catch(e) { toast(e.message, true); }
        input.value = '';
      };

      // New DM
      window.__chatNewDM = () => openChatUserPicker('گفتگو مستقیم جدید', 'انتخاب کاربر برای گفتگو مستقیم', allUsers, (uid)=>{
        api('/chat/channels', {method:'POST', body: JSON.stringify({member_ids:[uid]})})
          .then(r => { toast('گفتگو ایجاد شد'); renderChat().then(()=>window.__chatOpen(r.id)); })
          .catch(e => toast(e.message, true));
      });

      // New group
      window.__chatNewGroup = () => openChatGroupModal(allUsers, isAdmin, (name, memberIds) => {
        api('/chat/channels', {method:'POST', body: JSON.stringify({name, member_ids: memberIds})})
          .then(r => { toast('گروه ایجاد شد'); renderChat().then(()=>window.__chatOpen(r.id)); })
          .catch(e => toast(e.message, true));
      });

      // Rename group
      window.__chatRename = (chId, oldName) => {
        const n = prompt('نام جدید گروه:', oldName);
        if (!n) return;
        api(`/chat/channels/${chId}`, {method:'PATCH', body: JSON.stringify({name: n})})
          .then(()=>{toast('نام تغییر یافت'); window.__chatOpen(chId);})
          .catch(e=>toast(e.message,true));
      };

      // Add member
      window.__chatAddMember = (chId) => {
        // Filter out users already in the channel — simplest: pass allUsers to picker and let user pick
        openChatUserMultiPicker('افزودن عضو به گروه', 'کاربران برای افزودن', allUsers, (selected)=>{
          api(`/chat/channels/${chId}/members`, {method:'POST', body: JSON.stringify({member_ids: selected})})
            .then(r=>{toast(`${r.added} عضو اضافه شد`); window.__chatOpen(chId);})
            .catch(e=>toast(e.message,true));
        });
      };

      // Show members
      window.__chatShowMembers = async (chId) => {
        try {
          const ch = await api(`/chat/channels/${chId}`);
          const items = (ch.members||[]).map(m=>{
            const roleLbl = labels[m.role]||m.role||'';
            return `<div style="display:flex;justify-content:space-between;padding:10px 14px;border-bottom:1px solid #f1f5f9;">
              <div><strong>${esc(m.name)}</strong><div style="font-size:11px;color:#94a3b8;">${roleLbl}</div></div>
              <div style="font-size:11px;color:#64748b;">عضو از ${dateFmt(m.joined_at)}</div>
            </div>`;
          }).join('');
          modal(`اعضای گروه «${esc(ch.name)}»`, '', `<div style="max-height:400px;overflow-y:auto;border:1px solid #e2e8f0;border-radius:8px;">
              ${items || '<p style="padding:20px;text-align:center;color:#94a3b8;">عضوی وجود ندارد</p>'}
            </div>
            <div style="display:flex;justify-content:flex-end;margin-top:14px;"><button class="btn soft" onclick="document.getElementById('modalRoot').innerHTML=''">بستن</button></div>`);
        } catch(e) { toast(e.message, true); }
      };

      // Poll for new messages every 5s
      chatPollTimer = setInterval(async () => {
        if (!chatCurrentChannel) return;
        try {
          const fresh = await api(`/chat/channels/${chatCurrentChannel}/messages`);
          // Re-render only if message count changed
          if (JSON.stringify(fresh.map(m=>m.id)) !== JSON.stringify(chatCurrentMessages.map(m=>m.id))) {
            chatCurrentMessages = fresh || [];
            renderChatMessages(chatCurrentMessages);
          }
        } catch(e) {/* silent */}
      }, 5000);

      function renderChatMessages(msgs) {
        const c = document.getElementById('chatMessages');
        if (!c) return;
        if (!msgs.length) {
          c.innerHTML = '<p style="text-align:center;color:#94a3b8;padding-top:60px;font-size:13px;">این گفتگو خالی است. اولین پیام را ارسال کنید!</p>';
          return;
        }
        c.innerHTML = msgs.map(m => {
          const mine = m.user_id === state.me.id;
          const att = m.attachment_name ? `<a href="/api/chat/attachments/${m.attachment_id}" target="_blank" style="display:inline-flex;align-items:center;gap:6px;background:rgba(255,255,255,0.18);padding:6px 10px;border-radius:6px;font-size:12px;text-decoration:none;color:inherit;margin-top:6px;">📎 ${esc(m.attachment_name)} <span style="opacity:0.6;">(${m.attachment_size?(m.attachment_size/1024).toFixed(1)+'KB':''})</span></a>` : '';
          return `<div style="margin-bottom:14px;display:flex;justify-content:${mine?'flex-end':'flex-start'};">
            <div style="max-width:70%;padding:10px 14px;border-radius:14px;background:${mine?'#0b8f89':'#ffffff'};color:${mine?'#fff':'#0f172a'};box-shadow:0 1px 2px rgba(0,0,0,0.06);border:1px solid ${mine?'transparent':'#e2e8f0'};">
              <div style="font-size:11px;opacity:${mine?0.8:0.6};margin-bottom:4px;font-weight:600;">${mine?'شما':esc(m.user_name)}</div>
              ${m.body?`<div style="font-size:13px;line-height:1.6;white-space:pre-wrap;word-wrap:break-word;">${esc(m.body)}</div>`:''}
              ${att}
              <div style="font-size:10px;opacity:0.6;margin-top:4px;text-align:${mine?'left':'right'};">${timeFmt(m.created_at)}</div>
            </div>
          </div>`;
        }).join('');
        c.scrollTop = c.scrollHeight;
      }
    } catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }

  // Helper: chat user picker (single user)
  function openChatUserPicker(title, sub, users, onPick) {
    const list = (users||[]).map(u=>`
      <div onclick="window.__pickUser('${u.id}','${esc(u.name)}')" style="padding:10px 12px;border-radius:8px;background:#fff;border:1px solid #e2e8f0;margin-bottom:6px;cursor:pointer;display:flex;align-items:center;gap:10px;">
        <div style="width:34px;height:34px;border-radius:50%;background:#0b8f89;color:#fff;display:flex;align-items:center;justify-content:center;font-weight:600;font-size:13px;">${esc(u.name?.charAt(0))}</div>
        <div><div style="font-size:13px;font-weight:600;">${esc(u.name)}</div><div style="font-size:11px;color:#94a3b8;">${labels[u.role]||u.role}</div></div>
      </div>`).join('');
    window.__pickUser = (uid, uname) => { document.getElementById('modalRoot').innerHTML=''; onPick(uid); };
    modal(`${title}`, `${sub}`, `${list || '<p style="color:#94a3b8;text-align:center;padding:20px;">کاربری برای انتخاب وجود ندارد</p>'}<div style="display:flex;justify-content:flex-end;margin-top:14px;"><button class="btn soft" onclick="document.getElementById('modalRoot').innerHTML=''">انصراف</button></div>`);
  }

  // Helper: chat multi-user picker
  function openChatUserMultiPicker(title, sub, users, onPick) {
    const list = (users||[]).map(u=>`
      <label style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:6px;cursor:pointer;">
        <input type="checkbox" value="${u.id}" class="chat-pick-user" style="width:18px;height:18px;">
        <div style="flex:1;">
          <div style="font-size:13px;font-weight:600;">${esc(u.name)}</div>
          <div style="font-size:11px;color:#94a3b8;">${labels[u.role]||u.role}</div>
        </div>
      </label>`).join('');
    modal(`${title}`, `${sub}`, `${list || '<p style="color:#94a3b8;text-align:center;padding:20px;">کاربری برای انتخاب وجود ندارد</p>'}<div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px;"><button class="btn soft" onclick="document.getElementById('modalRoot').innerHTML=''">انصراف</button><button class="btn primary" onclick="window.__confirmMultiPick()">تأیید</button></div>`);
    window.__confirmMultiPick = () => {
      const ids = [...document.querySelectorAll('.chat-pick-user:checked')].map(c=>c.value);
      if (!ids.length) return toast('حداقل یک کاربر را انتخاب کنید', true);
      document.getElementById('modalRoot').innerHTML='';
      onPick(ids);
    };
  }

  // Helper: new group modal (name + members)
  function openChatGroupModal(users, isAdmin, onConfirm) {
    const list = (users||[]).map(u=>`
      <label style="display:flex;align-items:center;gap:10px;padding:9px 12px;background:#fff;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:6px;cursor:pointer;">
        <input type="checkbox" value="${u.id}" class="chat-group-member" style="width:18px;height:18px;">
        <div style="flex:1;">
          <div style="font-size:13px;font-weight:600;">${esc(u.name)}</div>
          <div style="font-size:11px;color:#94a3b8;">${labels[u.role]||u.role}</div>
        </div>
      </label>`).join('');
    modal(`ایجاد گروه جدید`, '', `<div style="margin:12px 0;">
        <label style="font-size:13px;display:block;margin-bottom:6px;">نام گروه <span style="color:#ef4444;">*</span></label>
        <input id="chatGroupName" class="field" placeholder="مثلاً تیم حسابداری" maxlength="60">
      </div>
      <p class="muted" style="font-size:12px;margin:8px 0;">اعضای گروه (حداقل یک نفر):</p>
      <div style="max-height:260px;overflow-y:auto;margin-bottom:12px;">${list}</div>
      <div style="display:flex;justify-content:flex-end;gap:8px;"><button class="btn soft" onclick="document.getElementById('modalRoot').innerHTML=''">انصراف</button><button class="btn primary" onclick="window.__confirmGroup()">ایجاد گروه</button></div>`);
    window.__confirmGroup = () => {
      const name = document.getElementById('chatGroupName')?.value.trim();
      const ids = [...document.querySelectorAll('.chat-group-member:checked')].map(c=>c.value);
      if (!name) return toast('نام گروه را وارد کنید', true);
      if (!ids.length) return toast('حداقل یک عضو را انتخاب کنید', true);
      document.getElementById('modalRoot').innerHTML='';
      onConfirm(name, ids);
    };
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

  // Expose for task detail + global-scope reports hub
  window.__startTimer = startTimer;
  window.__stopTimer = stopTimer;
  window.__enhancedShowView = showView;
  window.__renderKPIReport = renderKPIReport;
  window.__userKPIDetail = (uid) => userKPIDetail(uid);

  // ============ USER MANAGEMENT (edit, access, deactivate) ============
  async function renderUserManagement() {
    const section = document.getElementById('view-users');
    if (!section) return;
    try { return await renderUsersRich(section); }
    catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
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
    try { return await renderCompaniesRich(section); }
    catch(e) { section.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
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
      const newPass = prompt('رمز جدید (حداقل ۴ نویسه):');
      if (!newPass || newPass.length < 4) { toast('رمز باید حداقل ۴ نویسه باشد', true); return; }
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
  let kpiReportTarget = null;

  async function renderKPIReport(target) {
    // target: optional container (e.g. the گزارشات sub-tab content div)
    if (target) kpiReportTarget = target;
    let section = kpiReportTarget;
    if (!section || !section.isConnected) {
      kpiReportTarget = null;
      section = document.getElementById('view-kpi-report') || document.getElementById('view-performance');
    }
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
            <h1>🎯 گزارش KPI</h1>
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

  // ============ Customers Tab (مشتریان) ============
  let customersTab = 'persons';
  const CUSTOMER_TABS = [
    {key:'persons', label:'اشخاص', icon:'👤'},
    {key:'companies', label:'شرکت‌ها', icon:'🏢'},
    {key:'portal', label:'پورتال مشتریان', icon:'🌐', soon:true},
    {key:'contracts', label:'قراردادها', icon:'📜', soon:true},
    {key:'proforma', label:'پیش فاکتور', icon:'🧾', soon:true},
    {key:'invoices', label:'فاکتورها', icon:'💳', soon:true},
  ];

  async function renderCustomers() {
    const section = document.getElementById('view-customers');
    if (!section) return;
    const isAdmin = state.me?.role === 'ADMIN' || state.me?.role === 'CEO';
    section.innerHTML = `
      <h1>🤝 مشتریان</h1>
      <p class="hint" style="margin-bottom:16px;">مدیریت اشخاص حقیقی، شرکت‌های مشتری و اسناد مرتبط — قراردادها، پیش‌فاکتور و فاکتور به‌زودی فعال می‌شوند.</p>
      <div class="tabs" style="margin-bottom:16px;flex-wrap:wrap;">
        ${CUSTOMER_TABS.map(t => `<button class="tab ${customersTab===t.key?'active':''}" data-ctab="${t.key}" ${t.soon?'disabled style="opacity:0.5;cursor:not-allowed;"':''}>${t.icon} ${t.label}${t.soon?' <small style="font-size:9px;color:#94a3b8;">به‌زودی</small>':''}</button>`).join('')}
      </div>
      <div id="customersContent"></div>`;
    section.querySelectorAll('[data-ctab]').forEach(b => b.addEventListener('click', () => {
      if (b.disabled) return;
      customersTab = b.dataset.ctab;
      renderCustomers();
    }));
    const content = document.getElementById('customersContent');
    if (!content) return;
    try {
      if (customersTab === 'persons') await renderPersonsList(content, isAdmin);
      else if (customersTab === 'companies') await renderCompaniesListForCustomers(content, isAdmin);
      else content.innerHTML = `<div class="empty-state" style="text-align:center;padding:40px 20px;color:#94a3b8;">
        <div style="font-size:48px;margin-bottom:12px;">🚧</div>
        <h3 style="margin:0 0 8px;">این بخش به‌زودی فعال خواهد شد</h3>
        <p style="font-size:13px;max-width:400px;margin:0 auto;">این ویژگی در نسخه‌های بعدی اضافه خواهد شد. اکنون می‌توانید با تعریف اشخاص و شرکت‌های مشتری، زیرساخت اولیه را فراهم کنید.</p>
      </div>`;
    } catch(e) { content.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }
  window.__renderCustomers = renderCustomers;

  // اشخاص (Persons)
  async function renderPersonsList(content, isAdmin) {
    const [persons, companies] = await Promise.all([
      api('/persons'),
      api('/companies').catch(()=>[]),
    ]);
    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div><h3 style="margin:0;">👤 اشخاص مشتری</h3><p class="hint" style="margin-top:2px;">اشخاص حقیقی که به‌عنوان مشتری دفتر ثبت می‌شوند — مجزا از کاربران داخلی.</p></div>
        <div style="display:flex;gap:8px;">
          <input id="personSearch" class="field" placeholder="🔍 جستجوی نام/کد/کدملی/تلفن" style="width:240px;" oninput="window.__searchPersons()">
          ${isAdmin ? '<button class="btn primary small" onclick="window.__newPerson()">＋ شخص جدید</button>' : ''}
        </div>
      </div>
      <div class="table-card" style="overflow-x:auto;">
        <table class="data-table">
          <thead><tr><th>کد</th><th>نام و نام خانوادگی</th><th>کد ملی</th><th>تلفن</th><th>ایمیل</th><th>شرکت مرتبط</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody id="personsBody">
            ${persons.length ? persons.map(p => personRow(p, isAdmin)).join('') : `<tr><td colspan="8" style="text-align:center;padding:20px;color:#64748b;">شخصی ثبت نشده — با دکمه «شخص جدید» شروع کنید.</td></tr>`}
          </tbody>
        </table>
      </div>`;

    window.__searchPersons = async () => {
      const q = document.getElementById('personSearch').value.trim();
      try {
        const list = await api('/persons' + (q ? `?q=${encodeURIComponent(q)}` : ''));
        document.getElementById('personsBody').innerHTML = list.length ? list.map(p=>personRow(p, isAdmin)).join('') : `<tr><td colspan="8" style="text-align:center;padding:20px;color:#64748b;">نتیجه‌ای یافت نشد</td></tr>`;
      } catch(e) { toast(e.message, true); }
    };

    window.__newPerson = () => openPersonForm(null, companies, () => renderCustomers());
    window.__editPerson = (id) => openPersonForm(id, companies, () => renderCustomers());
    window.__deletePerson = async (id, name) => {
      if (!confirm(`حذف شخص «${name}»؟ این عمل بازگشت‌ناپذیر است.`)) return;
      try {
        await api(`/persons/${id}`, {method:'DELETE'});
        toast('شخص حذف شد');
        renderCustomers();
      } catch(e) { toast(e.message, true); }
    };

    function personRow(p, isAdmin) {
      const fullName = `${p.first_name} ${p.last_name}`;
      return `<tr>
        <td><code>${esc(p.code)}</code></td>
        <td><b>${esc(fullName)}</b></td>
        <td>${esc(p.national_id || '—')}</td>
        <td>${esc(p.phone || '—')}</td>
        <td>${esc(p.email || '—')}</td>
        <td>${p.linked_company_name ? `<span class="tag" style="background:#f0fdfa;color:#0b8f89;">${esc(p.linked_company_name)}</span>` : '—'}</td>
        <td>${p.active ? '<span style="color:#10b981;">● فعال</span>' : '<span style="color:#94a3b8;">○ غیرفعال</span>'}</td>
        <td>
          ${isAdmin ? `
            <button class="btn soft small" onclick="window.__editPerson('${p.id}')">✎ ویرایش</button>
            <button class="btn small" style="background:#fee2e2;color:#9f413d;" onclick="window.__deletePerson('${p.id}','${esc(fullName)}')">حذف</button>
          ` : '<span style="color:#94a3b8;font-size:11px;">فقط مشاهده</span>'}
        </td>
      </tr>`;
    }
  }

  function openPersonForm(id, companies, onDone) {
    if (id) {
      api(`/persons/${id}`).then(p => showForm(p)).catch(e=>toast(e.message, true));
    } else {
      showForm(null);
    }
    function showForm(p) {
      const isNew = !p;
      const companyOpts = (companies||[]).map(c=>`<option value="${esc(c.id)}" ${p && p.linked_company_id===c.id?'selected':''}>${esc(c.name)}</option>`).join('');
      const body = `
        <form id="personForm" class="stack">
          <div class="form-grid">
            <label>کد شخص <span style="color:#ef4444;">*</span><input class="field" name="code" required value="${p?esc(p.code):''}" ${p?'readonly':''} placeholder="مثلاً P001"></label>
            <label>نام <span style="color:#ef4444;">*</span><input class="field" name="first_name" required value="${p?esc(p.first_name):''}" placeholder="نام"></label>
            <label>نام خانوادگی <span style="color:#ef4444;">*</span><input class="field" name="last_name" required value="${p?esc(p.last_name):''}" placeholder="نام خانوادگی"></label>
            <label>کد ملی<input class="field" name="national_id" value="${p?esc(p.national_id):''}" placeholder="کد ملی"></label>
            <label>تلفن<input class="field" name="phone" value="${p?esc(p.phone):''}" placeholder="09..."></label>
            <label>ایمیل<input class="field" name="email" type="email" value="${p?esc(p.email):''}" placeholder="name@example.com"></label>
            <label>کد پستی<input class="field" name="postal_code" value="${p?esc(p.postal_code):''}"></label>
            <label>شرکت مرتبط<select class="field" name="linked_company_id"><option value="">— انتخاب —</option>${companyOpts}</select></label>
            <label class="wide-field">آدرس<input class="field" name="address" value="${p?esc(p.address):''}" placeholder="نشانی کامل"></label>
            <label class="wide-field">یادداشت<textarea name="notes" rows="3" placeholder="یادداشت داخلی">${p?esc(p.notes||''):''}</textarea></label>
            <label class="wide-field">
              <label class="check-row"><input type="checkbox" name="active" ${(!p || p.active)?'checked':''}> شخص فعال</label>
            </label>
          </div>
          <p class="hint">کد شخص پس از ایجاد قابل ویرایش نیست. هر شخص می‌تواند به یک شرکت مرتبط باشد.</p>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:12px;">
            <button type="button" class="btn soft" onclick="document.getElementById('modalRoot').innerHTML=''">انصراف</button>
            <button type="submit" class="btn primary">${isNew?'ایجاد':'ذخیره تغییرات'}</button>
          </div>
        </form>`;
      modal(`${isNew?'＋ شخص جدید':'✎ ویرایش شخص'}`, 'اشخاص حقیقی مشتری — مجزا از کاربران داخلی سامانه.', body);
      const form = document.getElementById('personForm');
      if (form) form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const fd = new FormData(form);
        const data = {
          code: fd.get('code').trim(),
          first_name: fd.get('first_name').trim(),
          last_name: fd.get('last_name').trim(),
          national_id: fd.get('national_id').trim(),
          phone: fd.get('phone').trim(),
          email: fd.get('email').trim(),
          postal_code: fd.get('postal_code').trim(),
          linked_company_id: fd.get('linked_company_id') || null,
          address: fd.get('address').trim(),
          notes: fd.get('notes').trim(),
          active: fd.get('active') ? 1 : 0,
        };
        try {
          if (isNew) {
            await api('/persons', {method:'POST', body:JSON.stringify(data)});
            toast('شخص جدید ایجاد شد');
          } else {
            const {code, ...update} = data;
            await api(`/persons/${id}`, {method:'PATCH', body:JSON.stringify(update)});
            toast('تغییرات ذخیره شد');
          }
          document.getElementById('modalRoot').innerHTML = '';
          onDone();
        } catch(err) { toast(err.message, true); }
      });
    }
  }

  // شرکت‌ها (Companies — full management inside Customers tab)
  async function renderCompaniesListForCustomers(content, isAdmin) {
    if (!content) return;
    const canManage = isAdmin && (state.me?.permissions?.['companies.manage'] ?? (state.me?.role === 'ADMIN' || state.me?.role === 'CEO'));
    const companies = await api('/companies').catch(()=>[]);
    const rows = companies.map(c => `
      <tr>
        <td><code><strong>${esc(c.code)}</strong></code></td>
        <td><strong>${esc(c.kind==='REAL' ? `${c.first_name} ${c.last_name}`.trim() || c.name : c.name)}</strong></td>
        <td>${c.kind==='REAL'?'<span class="tag" style="background:#fef3c7;color:#92400e;">حقیقی</span>':'<span class="tag" style="background:#dbeafe;color:#1e40af;">حقوقی</span>'}</td>
        <td style="font-size:12px;">${esc(c.national_id || '—')}</td>
        <td style="font-size:12px;">${esc(c.manager_name || '—')}${c.manager_phone ? `<div style="font-size:11px;color:#64748b;">${esc(c.manager_phone)}</div>` : ''}</td>
        <td style="font-size:12px;">${esc(c.phone || '—')}</td>
        <td>${c.active?'<span style="color:#10b981;">● فعال</span>':'<span style="color:#94a3b8;">○ غیرفعال</span>'}</td>
        <td style="display:flex;gap:4px;flex-wrap:wrap;">
          ${canManage ? `<button class="btn soft small" onclick="window.__custCompanyForm('${c.id}')">✎ ویرایش</button>` : ''}
          ${canManage ? (c.active
            ? `<button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__custToggleCompany('${c.id}',false)">✗ غیرفعال</button>`
            : `<button class="btn small" style="background:#d1fae5;color:#065f46;" onclick="window.__custToggleCompany('${c.id}',true)">✓ فعال</button>`) : ''}
          <button class="btn small" style="background:#e0f2fe;color:#0369a1;" onclick="window.__custCompanyDetails('${c.id}')">👁 جزئیات</button>
          ${!canManage ? '<span style="color:#94a3b8;font-size:11px;">فقط مشاهده</span>' : ''}
        </td>
      </tr>`).join('');
    content.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div><h3 style="margin:0;">🏢 شرکت‌های مشتری (${companies.length})</h3><p class="hint" style="margin-top:2px;">فهرست شرکت‌های حقوقی و حقیقی — دکمه «شرکت جدید» برای افزودن مستقیم.</p></div>
        ${canManage ? '<button class="btn primary small" onclick="window.__custCompanyForm()">＋ شرکت جدید</button>' : ''}
      </div>
      <div class="table-card" style="overflow-x:auto;">
        <table class="data-table">
          <thead><tr><th>کد</th><th>نام</th><th>نوع</th><th>شناسه ملی</th><th>مدیر</th><th>تلفن</th><th>وضعیت</th><th>عملیات</th></tr></thead>
          <tbody>
            ${rows || `<tr><td colspan="8" style="text-align:center;padding:20px;color:#64748b;">شرکتی ثبت نشده — با دکمه «شرکت جدید» شروع کنید.</td></tr>`}
          </tbody>
        </table>
      </div>`;

    // Customer-context toggle company active/inactive
    window.__custToggleCompany = async (id, active) => {
      try {
        await api(`/companies/${id}`, { method:'PATCH', body: JSON.stringify({ active }) });
        toast(active ? 'شرکت فعال شد' : 'شرکت غیرفعال شد');
        renderCustomers();
      } catch(e) { toast(e.message, true); }
    };

    // Customer-context company details
    window.__custCompanyDetails = async (id) => {
      try {
        const c = (await api('/companies')).find(x => x.id === id);
        if (!c) return toast('شرکت پیدا نشد', true);
        const item = (label, val) => `<div style="display:flex;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #f1f5f9;font-size:13px;"><span style="color:#64748b;">${label}</span><b>${esc(val) || '—'}</b></div>`;
        const body = `<div style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
          ${item('نوع', c.kind==='REAL' ? 'حقیقی' : 'حقوقی')}
          ${item('کد', c.code)}
          ${c.kind === 'LEGAL' ? item('نام شرکت', c.name) : item('نام', `${c.first_name} ${c.last_name}`)}
          ${item('شناسه ملی', c.national_id)}
          ${item('تماس', c.phone)}
          ${item('کد پستی', c.postal_code)}
          ${item('آدرس', c.address)}
          ${item('نام مدیر', c.manager_name)}
          ${item('تماس مدیر', c.manager_phone)}
        </div>`;
        modal(`جزئیات ${esc(c.name)}`, 'مشخصات کامل شرکت', body);
      } catch(e) { toast(e.message, true); }
    };

    // Customer-context company form (new/edit) — uses same rich modal as Settings,
    // but after submit, re-renders the Customers tab instead of the Settings tab.
    window.__custCompanyForm = (id) => {
      (async () => {
        let c = null;
        if (id) c = (await api('/companies')).find(x => x.id === id);
        const kind = c?.kind || 'LEGAL';
        const field = (label, name, val, opts={}) => `<label>${label}${opts.required?' <span style="color:#ef4444;">*</span>':''}<input class="field" name="${name}" ${opts.required?'required':''} value="${esc(val ?? '')}" placeholder="${opts.placeholder||''}"></label>`;
        const body = `
        <form id="custCompanyForm" style="display:grid;gap:12px;">
          <div style="display:flex;gap:8px;">
            <label class="check-row" style="flex:1;padding:10px;border:2px solid ${kind === 'LEGAL' ? '#0b8f89' : '#cbd5e1'};border-radius:10px;cursor:pointer;">
              <input type="radio" name="kind" value="LEGAL" ${kind === 'LEGAL' ? 'checked' : ''}> 🏢 شخص حقوقی (شرکت)</label>
            <label class="check-row" style="flex:1;padding:10px;border:2px solid ${kind === 'REAL' ? '#0b8f89' : '#cbd5e1'};border-radius:10px;cursor:pointer;">
              <input type="radio" name="kind" value="REAL" ${kind === 'REAL' ? 'checked' : ''}> 👤 شخص حقیقی</label>
          </div>
          <div id="custLegalRow" style="display:grid;gap:12px;">
            ${field('نام شرکت *', 'name', c?.name, { required: true, placeholder: 'مثلاً: شرکت بازرگانی پارس' })}
          </div>
          <div id="custRealRow" class="form-grid" style="display:none;">
            ${field('نام *', 'first_name', c?.first_name, { required: true })}
            ${field('نام خانوادگی *', 'last_name', c?.last_name, { required: true })}
          </div>
          <div class="form-grid">
            ${field('کد شرکت *', 'code', c?.code, { required: true, placeholder: 'کد یکتا — مثلاً 1001' })}
            ${field('شناسه ملی / کد ملی', 'national_id', c?.national_id, { placeholder: '۱۱ رقمی برای حقوقی / ۱۰ رقمی برای حقیقی' })}
          </div>
          <div class="form-grid">
            ${field('تماس', 'phone', c?.phone, { placeholder: '021-12345678' })}
            ${field('کد پستی', 'postal_code', c?.postal_code, { placeholder: '۱۰ رقمی' })}
          </div>
          ${field('آدرس', 'address', c?.address, { placeholder: 'آدرس کامل دفتر/شرکت' })}
          <div class="form-grid">
            ${field('نام مدیر', 'manager_name', c?.manager_name)}
            ${field('تماس مدیر', 'manager_phone', c?.manager_phone)}
          </div>
          <div style="display:flex;justify-content:flex-end;gap:8px;margin-top:6px;">
            <button type="button" class="btn soft" onclick="document.getElementById('modalRoot').innerHTML=''">انصراف</button>
            <button type="submit" class="btn primary">${id ? 'ذخیره تغییرات' : 'ثبت شرکت'}</button>
          </div>
        </form>`;
        modal(id ? '✎ ویرایش شرکت' : '＋ شرکت جدید', 'نوع شخص (حقیقی/حقوقی) فیلدهای نام را تعیین می‌کند. کد پس از ثبت قابل تغییر نیست.', body);
        const form = document.getElementById('custCompanyForm');
        const syncKind = () => {
          const k = form.querySelector('[name=kind]:checked')?.value;
          const legalRow = document.getElementById('custLegalRow');
          const realRow = document.getElementById('custRealRow');
          legalRow.style.display = k === 'LEGAL' ? 'grid' : 'none';
          realRow.style.display = k === 'REAL' ? 'grid' : 'none';
          // Toggle required-ness on the kind-specific name fields so HTML5 validation doesn't block submit when one row is hidden
          const legalName = legalRow.querySelector('[name=name]');
          const realFirst = realRow.querySelector('[name=first_name]');
          const realLast = realRow.querySelector('[name=last_name]');
          if (legalName) legalName.required = (k === 'LEGAL');
          if (realFirst) realFirst.required = (k === 'REAL');
          if (realLast) realLast.required = (k === 'REAL');
        };
        form.querySelectorAll('[name=kind]').forEach(r => r.addEventListener('change', syncKind));
        syncKind();
        form.addEventListener('submit', async e => {
          e.preventDefault();
          const fd = new FormData(form);
          const payload = Object.fromEntries(fd.entries());
          if (payload.kind === 'REAL' && !payload.name) {
            payload.name = `${payload.first_name || ''} ${payload.last_name || ''}`.trim();
          }
          try {
            if (id) await api(`/companies/${id}`, { method:'PATCH', body: JSON.stringify(payload) });
            else await api('/companies', { method:'POST', body: JSON.stringify(payload) });
            document.getElementById('modalRoot').innerHTML = '';
            toast(id ? 'شرکت ویرایش شد' : 'شرکت ثبت شد');
            renderCustomers();
          } catch(err) { toast(err.message, true); }
        });
      })();
    };
  }


  // ============ REPORTS HUB (تب گزارشات) ============
  // همه گزارش‌های مدیریتی: عملکرد تیم، عملکرد کارکنان، ممیزی و KPI
  let reportsTab = 'team';
  const REPORT_TABS = [
    {key:'team', label:'گزارش عملکرد تیم', icon:'▥'},
    {key:'employees', label:'عملکرد کارکنان', icon:'♙'},
    {key:'audit', label:'گزارش ممیزی', icon:'⌁'},
    {key:'kpi', label:'گزارش KPI', icon:'🎯'},
  ];

  // ============ Reports (گزارشات) ============
  async function renderReports() {
    const section = document.getElementById('view-reports');
    if (!section) return;
    section.innerHTML = `
      <h1>گزارشات</h1>
      <p class="hint" style="margin-bottom:16px;">همه گزارش‌های مدیریتی دفتر در یک‌جا — عملکرد تیم، عملکرد کارکنان، ممیزی و شاخص‌های کلیدی عملکرد.</p>
      <div class="tabs" style="margin-bottom:16px;flex-wrap:wrap;">
        ${REPORT_TABS.map(t => `<button class="tab ${reportsTab===t.key?'active':''}" data-rtab="${t.key}">${t.icon} ${t.label}</button>`).join('')}
      </div>
      <div id="reportsContent"></div>`;
    section.querySelectorAll('[data-rtab]').forEach(b => b.addEventListener('click', () => { reportsTab = b.dataset.rtab; renderReports(); }));
    const content = document.getElementById('reportsContent');
    if (!content) return;
    try {
      if (reportsTab === 'team') await renderTeamPerf(content);
      else if (reportsTab === 'employees') await renderEmployeesPerf(content);
      else if (reportsTab === 'audit') await renderAuditReport(content);
      else if (reportsTab === 'kpi') await window.__renderKPIReport(content);
    } catch(e) { content.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
  }
  window.__renderReports = renderReports;

  // --- زیرگزارش ۱: گزارش عملکرد تیم (نمره تسک‌ها: ساده/وزنی) ---
  async function renderTeamPerf(container) {
    const rows = await api('/performance');
    container.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div><h3 style="margin:0;">▥ گزارش عملکرد تیم</h3><p class="hint" style="margin-top:2px;">نمره‌های ثبت‌شده در «تصمیم مدیر» همراه با حجم کار و تأخیر — میانگین‌ها فقط از تسک‌های دارای نمره محاسبه شده‌اند.</p></div>
        <span class="tag">نمره‌ها تصمیم خودکار نیستند</span>
      </div>
      <div class="panel">
        <div class="score-card header"><span>کارمند</span><span>تسک</span><span>تکمیل</span><span>عقب‌افتاده</span><span>میانگین ساده / وزنی</span></div>
        ${rows.length?rows.map(r=>`<div class="score-card"><b>${esc(r.name)}</b><span>${num(r.total)}</span><span>${num(r.completed)}</span><span>${num(r.late)}</span><span class="score">${r.simple_score??'—'} <small style="font-size:9px;color:#819196">/ ${r.weighted_score??'—'}</small></span></div>`).join(''):empty('کارمندی ثبت نشده است','با واگذاری تسک و ثبت نمره، گزارش ساخته می‌شود.')}
      </div>
      <p class="hint" style="margin-top:12px;">گزارش فعلی بر اساس نمره‌های واردشده در تصمیم مدیر است. نمرهٔ عملکرد خودکار از تعداد اختلاف‌های Excel ساخته نمی‌شود. برای ارزیابی وزن‌دار به زیرگزارش «گزارش KPI» بروید.</p>`;
  }

  // --- زیرگزارش ۲: عملکرد کارکنان (ترکیب تسک‌ها + امتیاز KPI) ---
  async function renderEmployeesPerf(container) {
    const [perfRows, kpiData] = await Promise.all([
      api('/performance'),
      api('/performance/kpi-report?role=EMPLOYEE').catch(() => ({employees: []})),
    ]);
    const kpiByUser = {};
    (kpiData.employees || []).forEach(e => { kpiByUser[e.user_id] = e; });
    const merged = perfRows.map(r => {
      const k = kpiByUser[r.id];
      const taskPart = r.simple_score != null ? r.simple_score : (r.weighted_score != null ? r.weighted_score : 0);
      const kpiPart = k ? k.total_score : null;
      const combined = kpiPart != null ? Math.round(taskPart * 0.5 + kpiPart * 0.5) : (r.simple_score != null ? Math.round(taskPart) : null);
      return {...r, kpi_score: kpiPart, kpi_grade: k?.grade || null, combined};
    }).sort((a, b) => (b.combined ?? -1) - (a.combined ?? -1));
    const GRADE_COLORS = {'عالی':'#10b981','خوب':'#0b8f89','متوسط':'#f59e0b','ضعیف':'#ef4444'};
    container.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div><h3 style="margin:0;">♙ عملکرد کارکنان</h3><p class="hint" style="margin-top:2px;">ترکیب نمرهٔ تسک‌ها (۵۰٪) و امتیاز KPI (۵۰٪) برای هر کارمند — مرتب‌شده بر اساس امتیاز کل.</p></div>
        <span class="tag">${merged.length} کارمند</span>
      </div>
      <div class="table-card" style="overflow-x:auto;">
        <table class="data-table">
          <thead><tr><th>#</th><th>کارمند</th><th>تسک‌ها</th><th>تکمیل‌شده</th><th>عقب‌افتاده</th><th>نمره تسک</th><th>امتیاز KPI</th><th>امتیاز کل</th><th>عملیات</th></tr></thead>
          <tbody>
            ${merged.map((r, i) => `
              <tr>
                <td>${num(i + 1)}</td>
                <td><b>${esc(r.name)}</b></td>
                <td>${num(r.total)}</td>
                <td><span style="color:#10b981;">${num(r.completed)}</span></td>
                <td><span style="color:${r.late > 0 ? '#ef4444' : '#64748b'};">${num(r.late)}</span></td>
                <td>${r.simple_score ?? '—'} <small style="color:#819196;">/ ${r.weighted_score ?? '—'}</small></td>
                <td>${r.kpi_score != null ? `<b style="color:${GRADE_COLORS[r.kpi_grade] || '#64748b'};">${r.kpi_score}</b><small style="color:#64748b;"> /۱۰۰</small> ${r.kpi_grade ? `<span class="pill" style="background:${GRADE_COLORS[r.kpi_grade] || '#94a3b8'};color:#fff;padding:1px 8px;border-radius:999px;font-size:10px;">${esc(r.kpi_grade)}</span>` : ''}` : '<span style="color:#94a3b8;">—</span>'}</td>
                <td>
                  ${r.combined != null ? `<div style="display:flex;align-items:center;gap:8px;">
                    <div style="width:70px;height:8px;background:#f1f5f9;border-radius:4px;overflow:hidden;"><div style="width:${Math.min(100, r.combined)}%;height:100%;background:#0b8f89;"></div></div>
                    <b>${num(r.combined)}</b><small style="color:#64748b;">/۱۰۰</small></div>` : '<span style="color:#94a3b8;">—</span>'}
                </td>
                <td>
                  <div style="display:flex;gap:4px;flex-wrap:wrap;">
                    ${r.kpi_score != null ? `<button class="btn soft small" onclick="window.__userKPIDetail('${r.id}')">🎯 KPI</button>` : ''}
                    <button class="btn soft small" onclick="window.__empTaskHistory('${r.id}', '${esc(r.name)}')">✓ تسک‌ها</button>
                  </div>
                </td>
              </tr>`).join('') || '<tr><td colspan="9" style="text-align:center;padding:20px;color:#64748b;">کارمندی ثبت نشده است</td></tr>'}
          </tbody>
        </table>
      </div>
      <p class="hint" style="margin-top:12px;">💡 امتیاز کل = میانگین نمره تسک‌ها × ۵۰٪ + امتیاز KPI × ۵۰٪. اگر شاخصی تعریف نشده باشد، امتیاز کل برابر نمره تسک‌ها است. جزئیات شاخص‌ها در زیرگزارش «گزارش KPI».</p>`;
    window.__empTaskHistory = async (userId, name) => {
      try {
        const tasks = (state.tasks || []).filter(t => t.assignee_id === userId);
        const rows = tasks.slice(0, 20).map(t => `<tr><td><b>${esc(t.title)}</b><div class="task-sub">${esc(t.company_name)}</div></td><td>${statusTag(t.status)}</td><td>${num(t.progress)}٪</td><td>${dateFmt(t.due_date)}</td></tr>`).join('');
        modal(`تسک‌های ${name}`, 'آخرین تسک‌های واگذارشده به این کارمند', `<div class="table-card"><table class="data-table"><thead><tr><th>عنوان</th><th>وضعیت</th><th>پیشرفت</th><th>مهلت</th></tr></thead><tbody>${rows || '<tr><td colspan="4" style="text-align:center;padding:16px;color:#64748b;">تسکی یافت نشد</td></tr>'}</tbody></table></div>`, {wide:true});
      } catch (e) { toast(e.message, true); }
    };
  }

  // --- زیرگزارش ۳: گزارش ممیزی ---
  async function renderAuditReport(container) {
    const rows = await api('/audit');
    container.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
        <div><h3 style="margin:0;">⌁ گزارش ممیزی</h3><p class="hint" style="margin-top:2px;">ردیابی تغییرات حساس و عملیات کاربران — آخرین ۲۰۰ رویداد.</p></div>
        <button class="btn soft small" onclick="window.__refreshAuditReport()">↺ به‌روزرسانی</button>
      </div>
      <div class="table-card" style="overflow-x:auto;">
        <table class="data-table">
          <thead><tr><th>زمان</th><th>کاربر</th><th>عملیات</th><th>نوع رکورد</th><th>شناسه</th><th>جزئیات</th></tr></thead>
          <tbody>${rows.length?rows.map(r=>`<tr><td>${timeFmt(r.created_at)}</td><td>${esc(r.actor_name||'سیستم')}</td><td><span class="tag">${esc(r.action)}</span></td><td>${esc(r.entity_type)}</td><td class="task-sub">${esc(r.entity_id||'—')}</td><td style="max-width:320px;font-size:11px;word-break:break-word;">${esc(JSON.stringify(r.details))}</td></tr>`).join(''):`<tr><td colspan="6">${empty('رویدادی ثبت نشده است')}</td></tr>`}</tbody>
        </table>
      </div>`;
    window.__refreshAuditReport = () => renderAuditReport(container);
  }

  // ============ SETTINGS VIEW ============
  let settingsTab = 'companies2';
  async function renderSettings() {
    const section = document.getElementById('view-settings');
    if (!section) return;
    try {
      const data = await api('/settings');
      const tabs = [
        {key:'companies2', label:'تعریف شرکت', icon:'🏢'},
        {key:'users2', label:'کاربران', icon:'👤'},
        {key:'perms', label:'نقش‌ها و دسترسی‌ها', icon:'🔐'},
        {key:'kpis', label:'شاخص‌های کلیدی (KPI)', icon:'🎯'},
        {key:'task_types', label:'انواع تسک', icon:'📋'},
        {key:'process_types', label:'انواع فرآیند', icon:'🔄'},
        {key:'role_types', label:'انواع نقش', icon:'👥'},
        {key:'performance_types', label:'انواع عملکرد', icon:'✎'},
      ];
      section.innerHTML = `
        <h1>تنظیمات</h1>
        <p class="hint" style="margin-bottom:16px;">تعریف شرکت (حقیقی/حقوقی)، مدیریت کاربران و شرکت‌های واگذارشده، نقش‌ها و دسترسی‌های ریزفیلد، شاخص‌ها و انواع</p>
        <div class="tabs" style="margin-bottom:16px;flex-wrap:wrap;">
          ${tabs.map(t => `<button class="tab ${settingsTab===t.key?'active':''}" onclick="window.__setSettingsTab('${t.key}')">${t.icon} ${t.label}</button>`).join('')}
        </div>
        <div id="settingsContent"></div>
      `;
      window.__setSettingsTab = (key) => { settingsTab = key; renderSettings(); };
      if (settingsTab === 'companies2') {
        await renderCompaniesRich(document.getElementById('settingsContent'));
      } else if (settingsTab === 'users2') {
        await renderUsersRich(document.getElementById('settingsContent'));
      } else if (settingsTab === 'perms') {
        await renderPermsRich(document.getElementById('settingsContent'));
      } else if (settingsTab === 'kpis') {
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

// ==================================================================
// ============ SETTINGS PRO v2 — تعریف شرکت / کاربران / دسترسی‌ها ====
// (Global scope — uses app.js globals: esc, api, toast, modal, state)
// ==================================================================

const KIND_LABELS = { LEGAL: 'حقوقی', REAL: 'حقیقی' };

function __field(label, name, value, opts = {}) {
  const type = opts.type || 'text';
  const req = opts.required ? 'required' : '';
  const ph = opts.placeholder ? `placeholder="${esc(opts.placeholder)}"` : '';
  return `<label style="display:flex;flex-direction:column;gap:4px;font-size:13px;font-weight:600;color:#334155;">${label}
    <input class="field" name="${name}" type="${type}" value="${esc(value ?? '')}" ${req} ${ph}
      style="width:100%;padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;font-weight:400;"></label>`;
}

function __permCan(key) {
  return !state.me || !state.me.permissions || state.me.permissions[key] !== false;
}

// ---------------- تعریف شرکت (rich) ----------------
async function renderCompaniesRich(container) {
  if (!container) return;
  const canManage = __permCan('companies.manage');
  const companies = await api('/companies');
  const rows = companies.map(c => `
    <tr>
      <td class="font-mono"><strong>${esc(c.code)}</strong></td>
      <td><span class="pill" style="background:${c.kind === 'REAL' ? '#fef3c7;color:#92400e' : '#e0f2fe;color:#0c4a6e'};padding:2px 10px;border-radius:999px;font-size:11px;">${KIND_LABELS[c.kind] || 'حقوقی'}</span></td>
      <td><strong>${esc(c.name)}</strong>${c.kind === 'REAL' && (c.first_name || c.last_name) ? `<div style="font-size:11px;color:#64748b;">${esc(c.first_name)} ${esc(c.last_name)}</div>` : ''}</td>
      <td class="font-mono" style="font-size:12px;">${esc(c.national_id) || '—'}</td>
      <td style="font-size:12px;">${esc(c.phone) || '—'}</td>
      <td style="font-size:12px;">${esc(c.manager_name) || '—'}${c.manager_phone ? `<div style="font-size:11px;color:#64748b;">${esc(c.manager_phone)}</div>` : ''}</td>
      <td>${c.active ? '<span style="color:#10b981;">✓ فعال</span>' : '<span style="color:#ef4444;">✗ غیرفعال</span>'}</td>
      <td style="display:flex;gap:4px;flex-wrap:wrap;">
        ${canManage ? `<button class="btn soft small" onclick="window.__companyForm('${c.id}')">✎ ویرایش</button>` : ''}
        ${canManage ? (c.active
          ? `<button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__toggleCompany('${c.id}',false)">✗ غیرفعال</button>`
          : `<button class="btn small" style="background:#d1fae5;color:#065f46;" onclick="window.__toggleCompany('${c.id}',true)">✓ فعال</button>`) : ''}
        <button class="btn small" style="background:#e0f2fe;color:#0369a1;" onclick="window.__companyDetails('${c.id}')">👁 جزئیات</button>
      </td>
    </tr>`).join('');
  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
      <h3 style="margin:0;">🏢 تعریف شرکت (${companies.length})</h3>
      ${canManage ? '<button class="btn primary small" onclick="window.__companyForm()">＋ شرکت جدید</button>' : ''}
    </div>
    <p class="hint" style="margin-bottom:12px;color:#64748b;font-size:13px;">مشخصات کامل شرکت‌های حقیقی و حقوقی دفتر — شماره ملی، تماس، آدرس، کد پستی و اطلاعات مدیر. نوع شرکت (حقیقی/حقوقی) هنگام ثبت انتخاب می‌شود.</p>
    <div class="table-card" style="overflow-x:auto;">
      <table class="data-table">
        <thead><tr><th>کد</th><th>نوع</th><th>نام</th><th>شماره ملی</th><th>تماس</th><th>مدیر</th><th>وضعیت</th><th>عملیات</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="8" style="text-align:center;padding:20px;color:#64748b;">شرکتی ثبت نشده است</td></tr>'}</tbody>
      </table>
    </div>`;
  window.__toggleCompany = async (id, active) => {
    try {
      await api(`/companies/${id}`, { method: 'PATCH', body: JSON.stringify({ active }) });
      toast(active ? 'شرکت فعال شد' : 'شرکت غیرفعال شد');
      renderCompaniesRich(container);
    } catch (e) { toast(e.message, true); }
  };
  window.__companyDetails = async (id) => {
    try {
      const c = (await api('/companies')).find(x => x.id === id);
      if (!c) return toast('شرکت پیدا نشد', true);
      const item = (label, val) => `<div style="display:flex;justify-content:space-between;padding:8px 12px;border-bottom:1px solid #f1f5f9;font-size:13px;"><span style="color:#64748b;">${label}</span><b>${esc(val) || '—'}</b></div>`;
      const body = `<div style="border:1px solid #e2e8f0;border-radius:10px;overflow:hidden;">
        ${item('نوع', KIND_LABELS[c.kind] || 'حقوقی')}${item('نام', c.name)}${item('کد', c.code)}
        ${c.kind === 'REAL' ? item('نام', c.first_name) + item('نام خانوادگی', c.last_name) : ''}
        ${item('شماره ملی', c.national_id)}${item('تماس', c.phone)}${item('آدرس', c.address)}
        ${item('کد پستی', c.postal_code)}${item('نام مدیر', c.manager_name)}${item('تماس مدیر', c.manager_phone)}
      </div>`;
      modal(`جزئیات ${c.name}`, 'مشخصات کامل شرکت', body);
    } catch (e) { toast(e.message, true); }
  };
}

function __companyForm(id) {
  (async () => {
    let c = null;
    if (id) c = (await api('/companies')).find(x => x.id === id);
    const v = (f) => esc(c?.[f] ?? '');
    const kind = c?.kind || 'LEGAL';
    const body = `
    <form id="companyForm2" style="display:grid;gap:12px;">
      <div style="display:flex;gap:8px;">
        <label class="check-row" style="flex:1;padding:10px;border:2px solid ${kind === 'LEGAL' ? '#0b8f89' : '#cbd5e1'};border-radius:10px;cursor:pointer;">
          <input type="radio" name="kind" value="LEGAL" ${kind === 'LEGAL' ? 'checked' : ''}> 🏢 شخص حقوقی (شرکت)</label>
        <label class="check-row" style="flex:1;padding:10px;border:2px solid ${kind === 'REAL' ? '#0b8f89' : '#cbd5e1'};border-radius:10px;cursor:pointer;">
          <input type="radio" name="kind" value="REAL" ${kind === 'REAL' ? 'checked' : ''}> 👤 شخص حقیقی</label>
      </div>
      <div id="legalNameRow" style="display:grid;gap:12px;">
        ${__field('نام شرکت *', 'name', c?.name, { required: true, placeholder: 'مثلاً: شرکت بازرگانی پارس' })}
      </div>
      <div id="realNameRow" class="form-grid" style="display:none;">
        ${__field('نام *', 'first_name', c?.first_name, { required: true })}
        ${__field('نام خانوادگی *', 'last_name', c?.last_name, { required: true })}
      </div>
      <div class="form-grid">
        ${__field('کد شرکت *', 'code', c?.code, { required: true, placeholder: 'کد یکتا — مثلاً 1001' })}
        ${__field('شماره ملی / شناسه ملی', 'national_id', c?.national_id, { placeholder: '۱۱ رقمی برای حقوقی / ۱۰ رقمی برای حقیقی' })}
      </div>
      <div class="form-grid">
        ${__field('تماس', 'phone', c?.phone, { placeholder: '021-12345678' })}
        ${__field('کد پستی', 'postal_code', c?.postal_code, { placeholder: '۱۰ رقمی' })}
      </div>
      ${__field('آدرس', 'address', c?.address, { placeholder: 'آدرس کامل دفتر/شرکت' })}
      <div class="form-grid">
        ${__field('نام مدیر', 'manager_name', c?.manager_name)}
        ${__field('تماس مدیر', 'manager_phone', c?.manager_phone)}
      </div>
      <button class="btn primary">${id ? 'ذخیره تغییرات' : 'ثبت شرکت'}</button>
    </form>`;
    modal(id ? '✎ ویرایش شرکت' : '＋ تعریف شرکت جدید', 'نوع شخص (حقیقی/حقوقی) فیلدهای نام را تعیین می‌کند.', body);
    const form = document.getElementById('companyForm2');
    const syncKind = () => {
      const k = form.querySelector('[name=kind]:checked')?.value;
      const legalRow = document.getElementById('legalNameRow');
      const realRow = document.getElementById('realNameRow');
      legalRow.style.display = k === 'LEGAL' ? 'grid' : 'none';
      realRow.style.display = k === 'REAL' ? 'grid' : 'none';
      // Toggle required-ness on the kind-specific name fields so HTML5 validation doesn't block submit when one row is hidden
      const legalName = legalRow.querySelector('[name=name]');
      const realFirst = realRow.querySelector('[name=first_name]');
      const realLast = realRow.querySelector('[name=last_name]');
      if (legalName) legalName.required = (k === 'LEGAL');
      if (realFirst) realFirst.required = (k === 'REAL');
      if (realLast) realLast.required = (k === 'REAL');
    };
    form.querySelectorAll('[name=kind]').forEach(r => r.addEventListener('change', syncKind));
    syncKind();
    form.addEventListener('submit', async e => {
      e.preventDefault();
      const fd = new FormData(form);
      const payload = Object.fromEntries(fd.entries());
      if (payload.kind === 'REAL' && !payload.name) {
        payload.name = `${payload.first_name || ''} ${payload.last_name || ''}`.trim();
      }
      try {
        if (id) await api(`/companies/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
        else await api('/companies', { method: 'POST', body: JSON.stringify(payload) });
        document.getElementById('modalRoot').innerHTML = '';
        toast(id ? 'شرکت ویرایش شد' : 'شرکت ثبت شد');
        renderCompaniesRich(document.getElementById('settingsContent') || document.getElementById('view-companies'));
      } catch (err) { toast(err.message, true); }
    });
  })();
}
window.__companyForm = __companyForm;

// ---------------- کاربران (rich) ----------------
const ROLE_LABELS2 = { ADMIN: 'مدیر سامانه', CEO: 'مدیرعامل', EMPLOYEE: 'کارمند' };

async function renderUsersRich(container) {
  if (!container) return;
  const canManage = __permCan('users.manage');
  const [users, companies] = await Promise.all([api('/users'), api('/companies')]);
  const accessMap = {};
  await Promise.all(users.map(async u => {
    try {
      const d = await api(`/users/${u.id}`);
      accessMap[u.id] = (d.companies || []).map(c => c.name);
    } catch { accessMap[u.id] = []; }
  }));
  const rows = users.map(u => `
    <tr>
      <td><strong>${esc(u.name)}</strong>${(u.first_name || u.last_name) ? `<div style="font-size:11px;color:#64748b;">${esc(u.first_name)} ${esc(u.last_name)}</div>` : ''}</td>
      <td class="font-mono">${esc(u.username)}</td>
      <td style="font-size:12px;">${esc(u.phone) || '—'}</td>
      <td><span class="tag">${ROLE_LABELS2[u.role] || u.role}</span></td>
      <td style="max-width:220px;font-size:12px;">${accessMap[u.id]?.length
        ? `<span class="pill" style="background:#0b8f89;color:#fff;padding:2px 10px;border-radius:999px;font-size:11px;">${accessMap[u.id].length} شرکت</span> <span style="color:#64748b;">${esc(accessMap[u.id].slice(0, 3).join('، '))}${accessMap[u.id].length > 3 ? ' …' : ''}</span>`
        : '<span style="color:#ef4444;font-size:12px;">بدون دسترسی</span>'}</td>
      <td>${u.active ? '<span style="color:#10b981;">✓ فعال</span>' : '<span style="color:#ef4444;">✗ غیرفعال</span>'}</td>
      <td style="display:flex;gap:4px;flex-wrap:wrap;">
        ${canManage ? `<button class="btn soft small" onclick="window.__userForm('${u.id}')">✎ ویرایش</button>` : ''}
        ${__permCan('users.permissions') ? `<button class="btn small" style="background:#ede9fe;color:#5b21b6;" onclick="window.__openPerms('${u.id}')">🔐 دسترسی‌ها</button>` : ''}
        ${canManage ? (u.active
          ? `<button class="btn small" style="background:#fee2e2;color:#991b1b;" onclick="window.__toggleUser('${u.id}',false)">✗ غیرفعال</button>`
          : `<button class="btn small" style="background:#d1fae5;color:#065f46;" onclick="window.__toggleUser('${u.id}',true)">✓ فعال</button>`) : ''}
      </td>
    </tr>`).join('');
  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
      <h3 style="margin:0;">👤 کاربران (${users.length})</h3>
      ${canManage ? '<button class="btn primary small" onclick="window.__userForm()">＋ کاربر جدید</button>' : ''}
    </div>
    <p class="hint" style="margin-bottom:12px;color:#64748b;font-size:13px;">برای هر کارمند حساب مستقل بسازید و شرکت‌های واگذارشده را مشخص کنید — کاربر فقط اطلاعات همان شرکت‌ها را می‌بیند. دسترسی ریزفیلد در تب «نقش‌ها و دسترسی‌ها».</p>
    <div class="table-card" style="overflow-x:auto;">
      <table class="data-table">
        <thead><tr><th>نام و نام خانوادگی</th><th>نام کاربری</th><th>تماس</th><th>نقش</th><th>شرکت‌های واگذارشده</th><th>وضعیت</th><th>عملیات</th></tr></thead>
        <tbody>${rows || '<tr><td colspan="7" style="text-align:center;padding:20px;color:#64748b;">کاربری ثبت نشده است</td></tr>'}</tbody>
      </table>
    </div>`;
  window.__toggleUser = async (id, active) => {
    try {
      if (!active && !confirm('غیرفعال کردن کاربر؟ تمام نشست‌های فعال او حذف می‌شود.')) return;
      await api(`/users/${id}`, { method: active ? 'PATCH' : 'DELETE', body: active ? JSON.stringify({ active: true }) : undefined });
      toast(active ? 'کاربر فعال شد' : 'کاربر غیرفعال شد');
      renderUsersRich(container);
    } catch (e) { toast(e.message, true); }
  };
}

async function __userForm(id) {
  let u = null;
  if (id) u = await api(`/users/${id}`);
  const companies = await api('/companies');
  const accessIds = new Set((u?.companies || []).map(c => c.id));
  const companyChecks = companies.map(c => `
    <label class="check-row" style="display:flex;align-items:center;gap:8px;padding:8px 10px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:4px;cursor:pointer;font-size:13px;font-weight:400;">
      <input type="checkbox" name="company_ids" value="${esc(c.id)}" ${accessIds.has(c.id) ? 'checked' : ''}>
      <span>${esc(c.name)} <small style="color:#64748b;">(${esc(c.code)})</small></span></label>`).join('');
  const body = `
  <form id="userForm2" style="display:grid;gap:12px;">
    <div class="form-grid">
      ${__field('نام *', 'first_name', u?.first_name, { required: true })}
      ${__field('نام خانوادگی *', 'last_name', u?.last_name, { required: true })}
    </div>
    <div class="form-grid">
      ${__field('نام کاربری *', 'username', u?.username, { required: true, placeholder: 'حروف انگلیسی، عدد و . _ -' })}
      ${__field('تماس', 'phone', u?.phone, { placeholder: '09121234567' })}
    </div>
    ${id ? `
    <div class="form-grid">
      ${__field('رمز عبور جدید (اختیاری)', 'password', '', { type: 'password', placeholder: 'حداقل ۴ نویسه' })}
      ${__field('تایید رمز عبور', 'password2', '', { type: 'password' })}
    </div>` : `
    <div class="form-grid">
      ${__field('رمز عبور *', 'password', '', { type: 'password', required: true, placeholder: 'حداقل ۴ نویسه' })}
      ${__field('تایید رمز *', 'password2', '', { type: 'password', required: true })}
    </div>`}
    <label style="display:flex;flex-direction:column;gap:4px;font-size:13px;font-weight:600;color:#334155;">نقش
      <select name="role" class="field" style="padding:8px 12px;border:1px solid #cbd5e1;border-radius:8px;font-weight:400;">
        <option value="EMPLOYEE" ${!u || u.role === 'EMPLOYEE' ? 'selected' : ''}>کارمند</option>
        <option value="CEO" ${u?.role === 'CEO' ? 'selected' : ''}>مدیرعامل</option>
        <option value="ADMIN" ${u?.role === 'ADMIN' ? 'selected' : ''}>مدیر سامانه</option>
      </select></label>
    <div>
      <p class="section-title" style="margin-bottom:6px;">شرکت‌های واگذارشده</p>
      <p class="hint" style="margin-bottom:8px;font-size:12px;">⚠ هر کاربر فقط اطلاعات (تسک‌ها، اسناد، عملکرد) شرکت‌های انتخاب‌شده را می‌بیند.</p>
      <div style="max-height:180px;overflow-y:auto;">${companyChecks || '<span class="hint">ابتدا از تب «تعریف شرکت» شرکت بسازید.</span>'}</div>
    </div>
    <button class="btn primary">${id ? 'ذخیره تغییرات' : 'ایجاد کاربر'}</button>
  </form>`;
  modal(id ? '✎ ویرایش کاربر' : '＋ کاربر جدید', 'رمز حداقل ۴ نویسه. نام کاربری یکتا باشد.', body);
  document.getElementById('userForm2').addEventListener('submit', async e => {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const payload = Object.fromEntries(fd.entries());
    payload.company_ids = fd.getAll('company_ids');
    if (!payload.password) { delete payload.password; delete payload.password2; }
    if (payload.password && payload.password !== payload.password2) return toast('رمز عبور و تکرار آن یکسان نیستند', true);
    try {
      if (id) await api(`/users/${id}`, { method: 'PATCH', body: JSON.stringify(payload) });
      else await api('/users', { method: 'POST', body: JSON.stringify(payload) });
      document.getElementById('modalRoot').innerHTML = '';
      toast(id ? 'کاربر ویرایش شد' : 'کاربر ایجاد شد');
      renderUsersRich(document.getElementById('settingsContent') || document.getElementById('view-users'));
    } catch (err) { toast(err.message, true); }
  });
}
window.__userForm = __userForm;

// ---------------- نقش‌ها و دسترسی‌ها (ماتریس ریزفیلد) ----------------
let __permsSelectedUser = null;

async function renderPermsRich(container) {
  if (!container) return;
  const users = await api('/users');
  if (!users.length) { container.innerHTML = '<div class="alert error">کاربری وجود ندارد.</div>'; return; }
  if (!__permsSelectedUser || !users.find(u => u.id === __permsSelectedUser)) __permsSelectedUser = users[0].id;
  container.innerHTML = `
    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;flex-wrap:wrap;gap:8px;">
      <h3 style="margin:0;">🔐 نقش‌ها و دسترسی‌ها</h3>
      <span class="pill" style="background:#ede9fe;color:#5b21b6;padding:4px 12px;border-radius:999px;font-size:12px;">دسترسی ریزفیلد + محدودیت شرکت</span>
    </div>
    <p class="hint" style="margin-bottom:12px;color:#64748b;font-size:13px;">
      💡 هر کاربر علاوه بر نقش پایه، دسترسی‌های ریز جداگانه دارد. تیک هر مورد یعنی کاربر به آن بخش دسترسی دارد.
      در بخش «شرکت‌های قابل مشاهده» مشخص می‌شود هر کاربر اطلاعات کدام شرکت‌ها را می‌بیند.
      تغییر دسترسی، نشست کاربر را فوراً به‌روزرسانی می‌کند.</p>
    <div style="display:grid;grid-template-columns:220px 1fr;gap:16px;align-items:start;" id="permsLayout">
      <div class="table-card" style="padding:8px;">
        <p class="section-title" style="padding:4px 8px;">کاربران</p>
        ${users.map(u => `
          <button class="perms-user ${u.id === __permsSelectedUser ? 'active' : ''}" data-user="${esc(u.id)}"
            style="display:flex;flex-direction:column;align-items:flex-start;width:100%;padding:10px;border:none;border-radius:8px;background:${u.id === __permsSelectedUser ? '#0b8f89' : 'transparent'};color:${u.id === __permsSelectedUser ? '#fff' : 'inherit'};cursor:pointer;text-align:right;margin-bottom:2px;">
            <b style="font-size:13px;">${esc(u.name)}</b>
            <small style="opacity:.8;">${ROLE_LABELS2[u.role] || u.role} · ${esc(u.username)}</small>
          </button>`).join('')}
      </div>
      <div id="permsMatrix"><p class="hint">در حال بارگذاری…</p></div>
    </div>`;
  container.querySelectorAll('.perms-user').forEach(btn => {
    btn.addEventListener('click', () => { __permsSelectedUser = btn.dataset.user; renderPermsRich(container); });
  });
  await __renderPermsMatrix(document.getElementById('permsMatrix'), __permsSelectedUser);
}

async function __renderPermsMatrix(el, userId) {
  try {
    const [permData, companies] = await Promise.all([
      api(`/users/${userId}/permissions`),
      api('/companies'),
    ]);
    const u = permData.user;
    const effective = permData.effective || {};
    const accessIds = new Set((permData.companies || []).map(c => c.id));
    const canEdit = __permCan('users.permissions');
    const groups = (await api('/permissions/catalog')).catalog;
    let idx = 0;
    const groupsHtml = groups.map(g => `
      <div style="border:1px solid #e2e8f0;border-radius:10px;padding:12px 14px;margin-bottom:10px;">
        <p class="section-title" style="margin-bottom:8px;">${esc(g.group)}</p>
        ${g.items.map(it => { idx++; const on = !!effective[it.key];
          return `<label style="display:flex;align-items:center;gap:10px;padding:6px 4px;cursor:${canEdit ? 'pointer' : 'default'};font-size:13px;font-weight:400;border-radius:6px;">
            <input type="checkbox" class="perm-check" data-key="${esc(it.key)}" ${on ? 'checked' : ''} ${canEdit ? '' : 'disabled'}
              style="width:16px;height:16px;accent-color:#0b8f89;">
            <span>${esc(it.label)}</span>
            ${permData.override && it.key in permData.override ? '<span class="pill" style="background:#fef3c7;color:#92400e;padding:1px 8px;border-radius:999px;font-size:10px;">سفارشی</span>' : ''}
          </label>`; }).join('')}
      </div>`).join('');
    const companiesHtml = companies.map(c => `
      <label style="display:flex;align-items:center;gap:8px;padding:8px 10px;border:1px solid ${accessIds.has(c.id) ? '#0b8f89' : '#e2e8f0'};border-radius:8px;margin-bottom:4px;cursor:${canEdit ? 'pointer' : 'default'};font-size:13px;font-weight:400;background:${accessIds.has(c.id) ? 'rgba(11,143,137,.06)' : 'transparent'};">
        <input type="checkbox" class="company-vis-check" data-company="${esc(c.id)}" ${accessIds.has(c.id) ? 'checked' : ''} ${canEdit ? '' : 'disabled'} style="accent-color:#0b8f89;">
        <span>${esc(c.name)} <small style="color:#64748b;">(${esc(c.code)}) · ${KIND_LABELS[c.kind] || 'حقوقی'}</small></span></label>`).join('');
    el.innerHTML = `
      <div class="table-card" style="padding:14px;margin-bottom:12px;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">
        <div><b style="font-size:15px;">${esc(u.name)}</b> <span class="tag">${ROLE_LABELS2[u.role] || u.role}</span>
          <div style="font-size:12px;color:#64748b;margin-top:2px;">نام کاربری: ${esc(u.username)} · ${u.active ? 'فعال' : 'غیرفعال'}</div></div>
        <div style="display:flex;gap:6px;flex-wrap:wrap;">
          ${canEdit ? `
            <button class="btn primary small" id="permsSave">💾 ذخیره دسترسی‌ها</button>
            <button class="btn soft small" id="permsReset">↺ بازگشت به پیش‌فرض نقش</button>` : ''}
        </div>
      </div>
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;align-items:start;" class="perms-two-col">
        <div>
          <p class="section-title">دسترسی‌های ریز (به ریز فیلد)</p>
          ${groupsHtml}
        </div>
        <div>
          <p class="section-title">شرکت‌های قابل مشاهده</p>
          <div class="alert" style="background:#fffbeb;border:1px solid #fde68a;color:#92400e;font-size:12px;margin-bottom:10px;">
            ⚠ این لیست تعیین می‌کند کاربر اطلاعات چه شرکت‌هایی را ببیند: تسک‌ها، اسناد، عملکرد و مرجع‌ها فقط برای شرکت‌های تیک‌خورده نمایش داده می‌شود.
          </div>
          ${companiesHtml || '<p class="hint">شرکتی ثبت نشده است.</p>'}
          <div class="alert" style="background:#eff6ff;border:1px solid #bfdbfe;color:#1e40af;font-size:12px;margin-top:10px;">
            ℹ مدیرعامل و مدیر سامانه به‌صورت پیش‌فرض همه شرکت‌ها را می‌بینند. محدود کردن فهرست بالا روی کارکنان اثر مستقیم دارد.
          </div>
        </div>
      </div>`;
    if (canEdit) {
      document.getElementById('permsSave').addEventListener('click', async () => {
        const perms = {};
        el.querySelectorAll('.perm-check').forEach(cb => perms[cb.dataset.key] = cb.checked);
        const companyIds = [...el.querySelectorAll('.company-vis-check:checked')].map(cb => cb.dataset.company);
        try {
          await api(`/users/${userId}/permissions`, { method: 'PUT', body: JSON.stringify({ permissions: perms }) });
          await api(`/users/${userId}`, { method: 'PATCH', body: JSON.stringify({ company_ids: companyIds }) });
          toast('دسترسی‌ها ذخیره و اعمال شد');
          __renderPermsMatrix(el, userId);
        } catch (e) { toast(e.message, true); }
      });
      document.getElementById('permsReset').addEventListener('click', async () => {
        if (!confirm('بازگشت دسترسی‌ها به پیش‌فرض نقش؟')) return;
        try {
          await api(`/users/${userId}/permissions`, { method: 'PUT', body: JSON.stringify({ permissions: null }) });
          toast('دسترسی‌ها به پیش‌فرض نقش بازگشت');
          __renderPermsMatrix(el, userId);
        } catch (e) { toast(e.message, true); }
      });
    }
  } catch (e) { el.innerHTML = `<div class="alert error">${esc(e.message)}</div>`; }
}

window.__openPerms = (userId) => {
  __permsSelectedUser = userId;
  // اگر در تب تنظیمات هستیم، به تب دسترسی‌ها برو؛ وگرنه مودال ساده
  const settingsContent = document.getElementById('settingsContent');
  if (settingsContent && document.getElementById('view-settings') && !document.getElementById('view-settings').classList.contains('hidden')) {
    if (typeof window.__setSettingsTab === 'function') { window.__setSettingsTab('perms'); return; }
  }
  modal('🔐 نقش‌ها و دسترسی‌ها', 'مدیریت دسترسی کاربر', '<div id="permsMatrixModal"><p class="hint">در حال بارگذاری…</p></div>', { wide: true });
  __renderPermsMatrix(document.getElementById('permsMatrixModal'), userId);
};

// ---------------- nav overrides + permission gating ----------------
window.renderUsers = function() { return renderUserManagement(); };
window.renderCompanies = function() { return renderCompanyManagement(); };
window.__renderSettings = renderSettings;

const __NAV_PERMS = {
  audit: 'audit.view',
  users: 'users.view',
  companies: 'companies.view',
  performance: 'reports.kpi',
  reports: 'audit.view',
  'kpi-report': 'reports.kpi',
  iso30414: 'reports.iso',
  automations: 'automations.manage',
  settings: 'settings.view',
};

function __applyNavPermGating() {
  if (!state.me || !state.me.permissions) return false;
  Object.entries(__NAV_PERMS).forEach(([view, perm]) => {
    const btn = document.querySelector(`.nav-item[data-view="${view}"]`);
    if (btn) btn.classList.toggle('hidden', state.me.permissions[perm] === false);
  });
  return true;
}
window.__applyNavPermGating = __applyNavPermGating;

(function __gatingLoop() {
  let tries = 0;
  const t = setInterval(() => {
    tries++;
    if (__applyNavPermGating() || tries > 60) clearInterval(t);
  }, 500);
})();
