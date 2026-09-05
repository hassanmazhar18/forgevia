/* Forgevia dashboard */
const $=s=>document.querySelector(s),$$=s=>[...document.querySelectorAll(s)];
const MEM={};
function _ck(k){try{const m=document.cookie.match(new RegExp('(?:^|; )fvs_'+k+'=([^;]*)'));return m?decodeURIComponent(m[1]):null}catch(e){return null}}
const store={
 get(k){if(MEM[k]!=null)return MEM[k];let v=null;try{v=localStorage.getItem(k)}catch(e){}if(v==null){try{v=sessionStorage.getItem(k)}catch(e){}}if(v==null)v=_ck(k);if(v!=null)MEM[k]=v;return v},
 set(k,v){MEM[k]=v;try{localStorage.setItem(k,v)}catch(e){}try{sessionStorage.setItem(k,v)}catch(e){}try{document.cookie='fvs_'+k+'='+encodeURIComponent(v)+'; path=/; max-age=2592000; SameSite=None; Secure'}catch(e){}},
 del(k){delete MEM[k];try{localStorage.removeItem(k)}catch(e){}try{sessionStorage.removeItem(k)}catch(e){}try{document.cookie='fvs_'+k+'=; path=/; max-age=0'}catch(e){}}};
(function(){try{let t=null;const q=new URLSearchParams(location.search);if(q.get('t'))t=q.get('t');
 const m=location.hash.match(/(?:^#|[#&?])t=([A-Za-z0-9_\-]+)/);if(m)t=m[1];
 if(t){store.set('fv_token',t);q.delete('t');const h=location.hash.replace(/([#&?])t=[A-Za-z0-9_\-]+&?/,'$1').replace(/[#&?]$/,'');window.__FV_URL_TOKEN=t;let keep=false;try{keep=!navigator.cookieEnabled||!document.cookie&&(document.cookie='_t=1',!document.cookie)}catch(e){keep=true}if(!keep)history.replaceState(null,'',location.pathname+(q.toString()?'?'+q:'')+(h.length>1?h:'#home'))}
 window.__FV_TOKEN_SRC=t?'url':(store.get('fv_token')?'storage':'none')}catch(e){}})();
let URLTOK=window.__FV_URL_TOKEN||(document.querySelector('meta[name=fv-token]')||{}).content||null;const TOK=()=>URLTOK||store.get('fv_token');
(function(){if(URLTOK){store.set('fv_token',URLTOK);let ck=false;try{document.cookie='_t=1; SameSite=None; Secure';ck=document.cookie.indexOf('_t=1')>-1}catch(e){}history.replaceState(null,'','/app'+(ck?'':'#t='+URLTOK))}})();
window.addEventListener('error',e=>{const b=document.getElementById('authErr');if(b&&!document.getElementById('auth').classList.contains('hidden'))b.textContent='Page error: '+(e.message||e.error)});
window.addEventListener('unhandledrejection',e=>{const b=document.getElementById('authErr');if(b&&!document.getElementById('auth').classList.contains('hidden'))b.textContent='Error: '+(e.reason&&e.reason.message||e.reason)});
const api=async(u,o={})=>{const hd={...(o.body&&!(o.body instanceof FormData)?{'Content-Type':'application/json'}:{}),...(TOK()?{'Authorization':'Bearer '+TOK()}:{})};let r;try{const tk=TOK();const uu='/api'+u+(tk?((u.indexOf('?')>-1?'&':'?')+'_fvt='+encodeURIComponent(tk)):'');if(tk)hd['X-FV-Token']=tk;r=await fetch(uu,{...o,headers:{...hd,...(o.headers||{})}})}catch(err){throw new Error('Cannot reach server ('+(err.message||err)+'). Reload the page, or open the app in a new tab.')}let j;try{j=await r.json()}catch{j={}}if(r.status===401){showAuth();throw new Error('Please sign in')}if(!r.ok)throw new Error(j.detail||r.statusText);return j};
const toast=(m,err)=>{const t=$('#toast');t.textContent=m;t.className='toast show'+(err?' err':'');clearTimeout(t._t);t._t=setTimeout(()=>t.classList.remove('show'),2800)};
const copy=t=>{navigator.clipboard.writeText(t||'');toast('Copied')};
const esc=s=>String(s??'').replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
const ago=ts=>{const d=(Date.now()/1000-ts);return d<60?'just now':d<3600?Math.floor(d/60)+'m ago':d<86400?Math.floor(d/3600)+'h ago':Math.floor(d/86400)+'d ago'};
const fmt=n=>n>=1e6?(n/1e6).toFixed(1)+'M':n>=1e3?(n/1e3).toFixed(1)+'k':String(n);
let me=null,projects=[],proj=null,files=[],openTabs=[],cur=null,editor=null,models={},dirty=new Set(),templates=[],last=null,tplSel='blank';


/* ─────────── ICONS ─────────── */
const ICONS={rocket:'M4.5 16.5c-1.5 1.3-2 5-2 5s3.7-.5 5-2c.7-.8.7-2 0-2.8-.8-.7-2-.7-3 .8zM12 15l-3-3 5-7c1.5-1.7 4-3 7-3 0 3-1.3 5.5-3 7l-6 6z M9 12H4l2.5-4H12 M12 15v5l4-2.5V10',eye:'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z',bot:'M12 8V4H8 M4 8h16v12H4z M2 14h2 M20 14h2 M15 13v2 M9 13v2',term:'M4 17l6-5-6-5 M12 19h8',save:'M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z M17 21v-8H7v8 M7 3v5h8',sparkle:'M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z M19 17l.8 2.2L22 20l-2.2.8L19 23l-.8-2.2L16 20l2.2-.8z',plus:'M12 5v14 M5 12h14',folder:'M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z',upload:'M12 16V4 M6 10l6-6 6 6 M4 20h16',search:'M11 18a7 7 0 1 0 0-14 7 7 0 0 0 0 14z M21 21l-4.5-4.5',camera:'M4 8h3l2-3h6l2 3h3v11H4z M12 16a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z',desktop:'M3 4h18v12H3z M8 20h8 M12 16v4',tablet:'M5 3h14v18H5z M12 18h.01',phone:'M7 2h10v20H7z M11 18h2',refresh:'M21 12a9 9 0 1 1-3-6.7 M21 3v6h-6',ext:'M14 4h6v6 M20 4l-9 9 M19 14v6H4V5h6',globe:'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M2 12h20 M12 2a15 15 0 0 1 0 20 15 15 0 0 1 0-20z',lock:'M5 11h14v10H5z M8 11V7a4 4 0 0 1 8 0v4',settings:'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-2.9 1.2V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-2.8-1.2l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1A1.7 1.7 0 0 0 4.6 15H4.5a2 2 0 1 1 0-4h.1A1.7 1.7 0 0 0 5.8 8.2l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1A1.7 1.7 0 0 0 11.5 4.6V4.5a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 2.9 1.2l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0 1.2 2.9h.1a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1 .4z',cpu:'M5 5h14v14H5z M9 9h6v6H9z M9 2v3 M15 2v3 M9 19v3 M15 19v3 M2 9h3 M2 15h3 M19 9h3 M19 15h3',mail:'M3 5h18v14H3z M3 6l9 7 9-7',zap:'M13 2L4 14h7l-1 8 9-12h-7z',shield:'M12 2l8 3v7c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V5z M9 12l2 2 4-4',dns:'M4 6a8 3 0 1 0 16 0 8 3 0 1 0-16 0 M4 6v12c0 1.7 3.6 3 8 3s8-1.3 8-3V6 M4 12c0 1.7 3.6 3 8 3s8-1.3 8-3',id:'M3 5h18v14H3z M7 15a3 3 0 0 1 6 0 M10 11a1.5 1.5 0 1 0 0-3 1.5 1.5 0 0 0 0 3 M15 9h3 M15 13h3',share:'M18 8a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M6 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M18 22a3 3 0 1 0 0-6 3 3 0 0 0 0 6z M8.6 13.5l6.8 4 M15.4 6.5l-6.8 4',flask:'M9 3h6 M10 3v6l-5 9a2 2 0 0 0 1.7 3h10.6a2 2 0 0 0 1.7-3l-5-9V3',play:'M6 4l14 8-14 8z',stop:'M6 6h12v12H6z',qr:'M3 3h7v7H3z M14 3h7v7h-7z M3 14h7v7H3z M14 14h3v3h-3z M18 18h3v3h-3z M14 20v1 M21 14v1',copy:'M9 9h11v11H9z M5 15H4V4h11v1',trash:'M4 7h16 M9 7V4h6v3 M6 7l1 14h10l1-14',download:'M12 4v12 M6 10l6 6 6-6 M4 20h16',check:'M5 12l5 5L20 7',bolt:'M13 2L4 14h7l-1 8 9-12h-7z',link:'M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1 M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1',x:'M6 6l12 12 M18 6L6 18',question:'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M9.5 9.5a2.5 2.5 0 1 1 3.5 2.3c-.7.3-1 .9-1 1.7 M12 17h.01',target:'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z M12 18a6 6 0 1 0 0-12 6 6 0 0 0 0 12z M12 14a2 2 0 1 0 0-4 2 2 0 0 0 0 4z',doc:'M14 3H6v18h12V7z M14 3v4h4 M9 13h6 M9 17h6',inbox:'M3 13l3-8h12l3 8v6H3z M3 13h5l1 2h6l1-2h5'};
const I=(n,sz=16)=>`<svg class="ic" width="${sz}" height="${sz}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.9" stroke-linecap="round" stroke-linejoin="round"><path d="${ICONS[n]||''}"/></svg>`;
function iconize(){document.querySelectorAll('[data-i]').forEach(el=>{if(el.dataset.done)return;el.dataset.done=1;el.insertAdjacentHTML('afterbegin',I(el.dataset.i,el.dataset.sz||16))})}

/* ─────────── AUTH ─────────── */
let signup=new URLSearchParams(location.search).has('signup');
function showAuth(){if(!/^\/app/.test(location.pathname)||location.search.indexOf('inline')>-1){$('#auth').classList.remove('hidden');$('#shell').classList.add('hidden');renderAuth();pingServer();return}location.replace('/login?'+(signup?'signup=1&':'')+'why='+encodeURIComponent('session '+(window.__FV_TOKEN_SRC||'?')+' | '+(window.__FV_BOOT_ERR||'')))}
async function pingServer(){const el=$('#srvStatus');if(!el)return;el.textContent='Connecting to server…';el.style.color='';try{const r=await fetch('/health?'+Date.now(),{cache:'no-store'});if(!r.ok)throw 0;el.textContent='● Server online';el.style.color='var(--ok)'}catch{el.textContent='● Cannot reach server — reload the page or ask to restart it';el.style.color='var(--bad)'}}
function renderAuth(){$('#authTitle').textContent=signup?'Create your account':'Welcome back';$('#authSub').textContent=signup?'Free forever. No credit card.':'Sign in to your workspace';$('#aName').classList.toggle('hidden',!signup);$('#authBtn').textContent=signup?'Create account':'Sign in';$('#authSwitch').innerHTML=signup?'Already have an account? <a href="#" onclick="toggleAuth();return false">Sign in</a>':'New here? <a href="#" onclick="toggleAuth();return false">Create a free account</a>'}
function toggleAuth(){signup=!signup;renderAuth()}
async function doAuth(){$('#authErr').textContent='';$('#srvStatus').textContent='Working…';const btn=$('#authBtn');btn.disabled=true;btn.textContent='Please wait…';try{const email=$('#aEmail').value.trim(),password=$('#aPw').value;if(!email||!password)throw new Error('Enter email and password');let r;try{r=await api(signup?'/auth/signup':'/auth/login',{method:'POST',body:JSON.stringify({email,password,name:$('#aName').value.trim()})})}catch(e){if(signup&&/already registered/i.test(e.message)){try{r=await api('/auth/login',{method:'POST',body:JSON.stringify({email,password})});toast('You already had an account — signed you in')}catch{throw new Error('This email is already registered. Please sign in (password didn\'t match).')}}else throw e}if(r.token){URLTOK=r.token;store.set('fv_token',r.token)}$('#srvStatus').textContent='Signed in ✓';await boot()}catch(e){$('#authErr').textContent=e.message||'Something went wrong';$('#srvStatus').textContent=''}finally{btn.disabled=false;renderAuth()}}
async function logout(){try{await api('/auth/logout',{method:'POST'})}catch{}store.del('fv_token');location.href='/'}

/* ─────────── BOOT ─────────── */
async function boot(){try{me=await api('/me')}catch(e){window.__FV_BOOT_ERR=String(e&&e.message||e);if(/401|sign in|expired/i.test(window.__FV_BOOT_ERR)){URLTOK=null;store.del('fv_token')}showAuth();return}
 $('#auth').classList.add('hidden');$('#shell').classList.remove('hidden');
 $('#uName').textContent=me.name;$('#avatar').textContent=me.name[0].toUpperCase();$('#acName').textContent=me.name;$('#acEmail').textContent=me.email;$('#acPlan').textContent=me.plan;
 const h=new Date().getHours();$('#tod').textContent=h<12?'morning':h<17?'afternoon':'evening';
 templates=await api('/templates');await loadProjects();renderActivity();
 if(proj)await openProject(proj);
 if(store.get('fv_hideStart')==='1')$('#startPanel')?.classList.add('hidden');
 updateSteps();
 iconize();
 const v=location.hash.slice(1);if(v)go(v)}
$$('.rail button[data-v]').forEach(b=>b.onclick=()=>go(b.dataset.v));
function go(v){$$('.rail button').forEach(b=>b.classList.toggle('on',b.dataset.v===v));$$('.view').forEach(s=>s.classList.toggle('on',s.dataset.view===v));location.hash=v;
 if(v==='account')loadConnections();
 if(v==='editor'){ensureEditor().then(()=>{editor&&editor.layout();if(cur)showModel(cur)})}if(v==='deploy')renderDeploy();if(v==='analytics')loadAnalytics();if(v==='forms')loadForms();if(v==='monitor')loadMon();if(v==='home'){loadProjects();renderActivity()}}

/* ─────────── PROJECTS ─────────── */
async function loadProjects(){projects=await api('/projects');
 $('#kProj').textContent=projects.length;$('#kPub').textContent=projects.filter(p=>p.published).length;$('#kHits').textContent=fmt(projects.reduce((s,p)=>s+p.hits,0));$('#kApps').textContent=projects.filter(p=>p.running).length;
 const opts=projects.map(p=>`<option value="${p.name}" ${p.name===proj?'selected':''}>${p.name}</option>`).join('');
 ['projSel','dpSel','anSel','fmSel','fixSel'].forEach(id=>$('#'+id).innerHTML=opts);
 renderProjects();if(!proj&&projects[0])proj=projects[0].name}
const TI={blank:'doc',landing:'rocket',portfolio:'target',blog:'doc',restaurant:'inbox',docs:'doc',shop:'inbox',flask:'cpu',node:'cpu','coming-soon':'zap',import:'upload',copy:'copy',github:'share'};
function renderProjects(){const q=($('#projFilter').value||'').toLowerCase();const icon=t=>I(TI[t]||'folder',22);
 $('#projCards').innerHTML=projects.filter(p=>p.name.includes(q)).map(p=>`<div class="pc" onclick="openProject('${p.name}');go('editor')">${p.published?'<span class="live" title="Live"></span>':''}<div class="ic">${icon(p.template)}</div><b>${p.name}</b><div class="meta">${p.kind} · ${p.files} files · ${(p.size/1024).toFixed(0)} KB · ${p.published?'published '+ago(p.published):'draft'}</div>
  <div class="foot"><span class="badge">${I('eye',12)} ${fmt(p.hits)}</span><span class="badge">24h: ${p.hits24}</span>${p.running?'<span class="badge ok">● running</span>':''}</div></div>`).join('')+`<div class="pc new" onclick="openNew()">+ New project</div>`}
async function renderActivity(){me=await api('/me');$('#activity').innerHTML=me.activity.map(a=>`<div><span>${a.project?`<b>${a.project}</b> `:''}${a.action}${a.detail?` <span class="mut">— ${esc(a.detail)}</span>`:''}</span><small>${ago(a.ts)}</small></div>`).join('')||'<p class="mut">No activity yet.</p>'}
function openNew(){$('#tpls').innerHTML=templates.map(t=>`<div class="tpl ${t.id===tplSel?'on':''}" onclick="tplSel='${t.id}';openNew()"><span>${I(TI[t.id]||'folder',26)}</span><b>${t.name}</b><small>${t.desc}</small></div>`).join('');newDlg.showModal();$('#npName').focus()}
async function createProject(){try{const r=await api('/projects',{method:'POST',body:JSON.stringify({name:$('#npName').value,template:tplSel})});newDlg.close();$('#npName').value='';await loadProjects();await openProject(r.name);go('editor');toast('Project created — edit, then press Publish');updateSteps()}catch(e){toast(e.message,1)}}
async function importZip(f){if(!f)return;const name=$('#npName').value||f.name.replace(/\.zip$/,'');const fd=new FormData();fd.append('file',f);try{const r=await api('/projects/import?name='+encodeURIComponent(name),{method:'POST',body:fd});newDlg.close();await loadProjects();openProject(r.name);go('editor');toast('Imported')}catch(e){toast(e.message,1)}}
async function openProject(n){if(!n)return;proj=n;openTabs=[];cur=null;dirty.clear();Object.values(models).forEach(m=>m.dispose());models={};
 ['projSel','dpSel','anSel','fmSel','fixSel'].forEach(id=>$('#'+id).value=n);
 await loadFiles();const idx=files.find(f=>f.path==='index.html')||files.find(f=>/\.(py|js|html)$/.test(f.path))||files[0];if(idx)openFile(idx.path);loadVersions();updateStatus()}
function pinfo(){return projects.find(p=>p.name===proj)||{}}

/* ─────────── FILES ─────────── */
async function loadFiles(){files=await api(`/projects/${proj}/files`);renderTree()}
const FC={html:'#f97316',css:'#38bdf8',js:'#facc15',mjs:'#facc15',ts:'#3b82f6',py:'#4ade80',json:'#a3a3a3',md:'#c084fc',txt:'#94a3b8',png:'#f472b6',jpg:'#f472b6',svg:'#f472b6',ico:'#f472b6',xml:'#fb923c'};const ficon=p=>{const e=p.split('.').pop();return `<span class="fdot" style="background:${FC[e]||'#64748b'}"></span>`};
function renderTree(){const dirs={};files.forEach(f=>{const parts=f.path.split('/');let node=dirs;parts.slice(0,-1).forEach(d=>node=node[d]=node[d]||{});(node._f=node._f||[]).push(f)});
 const walk=(node,pre,depth)=>Object.keys(node).filter(k=>k!=='_f').sort().map(k=>`<div class="fi dir" style="padding-left:${8+depth*12}px">📁 ${k}</div>`+walk(node[k],pre+k+'/',depth+1)).join('')+(node._f||[]).map(f=>`<div class="fi ${f.path===cur?'on':''}" style="padding-left:${8+depth*12}px" onclick="openFile('${f.path}')" oncontextmenu="event.preventDefault();renameFile('${f.path}')">${ficon(f.path)} ${f.path.split('/').pop()}<span class="x" onclick="event.stopPropagation();delFile('${f.path}')">✕</span></div>`).join('');
 $('#tree').innerHTML=walk(dirs,'',0)||'<p class="mut small" style="padding:10px">Drop files here</p>'}
async function newFile(dir){const n=prompt(dir?'Folder name (a placeholder .gitkeep will be created):':'File name (e.g. about.html or css/extra.css):');if(!n)return;const p=dir?n.replace(/\/$/,'')+'/.gitkeep':n;await api(`/projects/${proj}/files/${p}`,{method:'PUT',body:JSON.stringify({content:''})});await loadFiles();if(!dir)openFile(p)}
async function delFile(p){if(!confirm('Delete '+p+'?'))return;await api(`/projects/${proj}/files/${p}`,{method:'DELETE'});closeTab(p,true);await loadFiles()}
async function renameFile(p){const to=prompt('Rename/move to:',p);if(!to||to===p)return;await api(`/projects/${proj}/files/${p}/rename`,{method:'POST',body:JSON.stringify({to})});closeTab(p,true);await loadFiles();openFile(to)}
async function uploadFiles(fl){if(!fl.length)return;const fd=new FormData();[...fl].forEach(f=>fd.append('files',f));await api(`/projects/${proj}/upload`,{method:'POST',body:fd});await loadFiles();toast(fl.length+' file(s) uploaded')}
function toggleSearch(){$('#searchBox').classList.toggle('hidden');$('#searchQ').focus()}
let sT;function searchFiles(q){clearTimeout(sT);if(q.length<2)return $('#searchRes').innerHTML='';sT=setTimeout(async()=>{const r=await api(`/projects/${proj}/search?q=`+encodeURIComponent(q));$('#searchRes').innerHTML=r.map(x=>`<div onclick="openFile('${x.file}',${x.line})"><b>${x.file}:${x.line}</b> ${esc(x.text)}</div>`).join('')||'<div class="mut">No matches</div>'},250)}

/* ─────────── EDITOR (Monaco) ─────────── */
let edReady=null;function ensureEditor(){if(editor)return Promise.resolve();if(edReady)return edReady;if(!window.require)return Promise.resolve();edReady=new Promise(res=>{window._edRes=res});require.config({paths:{vs:'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs'}});
 require(['vs/editor/editor.main'],()=>{monaco.editor.defineTheme('fv',{base:'vs-dark',inherit:true,rules:[],colors:{'editor.background':'#07080c','editorLineNumber.foreground':'#3a4052','editor.lineHighlightBackground':'#ffffff06','editorIndentGuide.background':'#1c2030'}});
  editor=monaco.editor.create($('#monaco'),{theme:'fv',fontSize:13.5,fontFamily:'ui-monospace,Menlo,Consolas,monospace',minimap:{enabled:false},automaticLayout:true,tabSize:2,wordWrap:'on',smoothScrolling:true,cursorBlinking:'smooth',padding:{top:12},scrollBeyondLastLine:false,bracketPairColorization:{enabled:true}});
  editor.onDidChangeCursorPosition(e=>$('#stPos').textContent=`Ln ${e.position.lineNumber}, Col ${e.position.column}`);
  editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.KeyS,saveFile);
  editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.KeyP,quickOpen);
  editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyMod.Shift|monaco.KeyCode.KeyP,publish);
  editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.KeyI,toggleAi);
  editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.Backquote,toggleTerm);
  editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyCode.KeyB,()=>$('#filePane').classList.toggle('collapsed'));
  editor.addCommand(monaco.KeyMod.CtrlCmd|monaco.KeyMod.Shift|monaco.KeyCode.KeyF,toggleSearch);
  window._edRes&&window._edRes();if(cur)showModel(cur)})
 return edReady}
const langOf=p=>({html:'html',css:'css',js:'javascript',mjs:'javascript',ts:'typescript',py:'python',json:'json',md:'markdown',xml:'xml',txt:'plaintext',sh:'shell',yml:'yaml',yaml:'yaml'}[p.split('.').pop()]||'plaintext');
async function openFile(p,line){await ensureEditor();if(!openTabs.includes(p))openTabs.push(p);cur=p;renderTabs();renderTree();$('#crumb').textContent=proj+' / '+p;$('#stLang').textContent=langOf(p);
 if(!models[p]){const r=await api(`/projects/${proj}/files/${p}`);if(r.binary){$('#crumb').textContent+=' (binary, '+r.size+' bytes)';return}
  if(window.monaco){models[p]=monaco.editor.createModel(r.content,langOf(p));models[p].onDidChangeContent(()=>{dirty.add(p);renderTabs();schedulePreview()})}else{models[p]={_raw:r.content}}}
 showModel(p,line);refreshPreview()}
function showModel(p,line){if(!editor)return;let m=models[p];if(m&&m._raw!==undefined){m=models[p]=monaco.editor.createModel(m._raw,langOf(p));m.onDidChangeContent(()=>{dirty.add(p);renderTabs();schedulePreview()})}if(m){editor.setModel(m);if(line){editor.revealLineInCenter(line);editor.setPosition({lineNumber:line,column:1})}editor.focus()}}
function renderTabs(){$('#tabs').innerHTML=openTabs.map(t=>`<div class="tab ${t===cur?'on':''} ${dirty.has(t)?'dirty':''}" onclick="openFile('${t}')">${ficon(t)} ${t.split('/').pop()}<i onclick="event.stopPropagation();closeTab('${t}')"></i></div>`).join('')}
function closeTab(p,force){if(!force&&dirty.has(p)&&!confirm('Discard unsaved changes to '+p+'?'))return;openTabs=openTabs.filter(t=>t!==p);dirty.delete(p);if(models[p]){models[p].dispose?.();delete models[p]}if(cur===p){cur=openTabs[openTabs.length-1]||null;if(cur)openFile(cur);else if(editor)editor.setModel(null)}renderTabs()}
async function saveFile(all){const list=all?[...dirty]:(cur?[cur]:[]);for(const p of list){const m=models[p];if(!m||!m.getValue)continue;await api(`/projects/${proj}/files/${p}`,{method:'PUT',body:JSON.stringify({content:m.getValue()})});dirty.delete(p)}renderTabs();$('#stSave').textContent='Saved '+new Date().toLocaleTimeString();if(!all)toast('Saved');refreshPreview()}
function formatDoc(){editor?.getAction('editor.action.formatDocument').run()}
function quickOpen(){$('#quickQ').value='';quickFilter();quickDlg.showModal();$('#quickQ').focus()}
let qi=0;function quickFilter(){const q=$('#quickQ').value.toLowerCase();const l=files.filter(f=>f.path.toLowerCase().includes(q)).slice(0,12);qi=0;$('#quickList').innerHTML=l.map((f,i)=>`<div class="${i===0?'on':''}" data-p="${f.path}" onclick="openFile('${f.path}');quickDlg.close()">${ficon(f.path)} ${f.path}</div>`).join('')}
function quickKey(e){const items=$$('#quickList div');if(e.key==='ArrowDown')qi=Math.min(qi+1,items.length-1);else if(e.key==='ArrowUp')qi=Math.max(qi-1,0);else if(e.key==='Enter'){items[qi]?.click();return}else return;items.forEach((d,i)=>d.classList.toggle('on',i===qi))}

/* ─────────── PREVIEW ─────────── */
let pT;function schedulePreview(){clearTimeout(pT);pT=setTimeout(refreshPreview,600)}
function togglePrev(){$('#prevPane').classList.toggle('hidden');editor?.layout()}
function setDevice(w){$('#prev').style.width=w}
async function refreshPreview(){if(!proj||$('#prevPane').classList.contains('hidden'))return;const p=pinfo();
 if(p.kind&&p.kind!=='static'){$('#prev').srcdoc=`<body style="font-family:system-ui;padding:40px;color:#333"><h3>${p.kind} app</h3><p>Backend apps preview at their live URL after publishing.</p><p><a href="/sites/${proj}/" target="_blank">/sites/${proj}/</a></p></body>`;return}
 let htmlFile=cur&&cur.endsWith('.html')?cur:'index.html';const get=async f=>models[f]?.getValue?models[f].getValue():(await api(`/projects/${proj}/files/${f}`).catch(()=>({content:''}))).content;
 let html=await get(htmlFile);const dir=htmlFile.includes('/')?htmlFile.slice(0,htmlFile.lastIndexOf('/')+1):'';
 for(const f of files){const rel=f.path.startsWith(dir)?f.path.slice(dir.length):f.path;
  if(f.path.endsWith('.css')&&html.includes(rel)){const c=await get(f.path);html=html.replace(new RegExp(`<link[^>]*href=["'](\\./)?${rel.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}["'][^>]*>`),`<style>${c}</style>`)}
  if(f.path.endsWith('.js')&&html.includes(rel)){const c=await get(f.path);html=html.replace(new RegExp(`<script[^>]*src=["'](\\./)?${rel.replace(/[.*+?^${}()|[\]\\]/g,'\\$&')}["'][^>]*></script>`),`<script>${c.replace(/<\/script/g,'<\\/script')}<\/script>`)}}
 html=html.replace('<head>',`<head><base href="${location.origin}/sites/${proj}/${dir}">`);$('#prev').srcdoc=html;$('#prevUrl').textContent=htmlFile;$('#openLive').href=`/sites/${proj}/${htmlFile==='index.html'?'':htmlFile}`}

/* ─────────── PUBLISH / STATUS ─────────── */
async function publish(){if(!proj)return;await saveFile(true);try{const r=await api(`/projects/${proj}/publish`,{method:'POST'});toast(`Published ${r.pages} page(s)`);await loadProjects();updateStatus();loadVersions();if($('.view.on').dataset.view!=='deploy')go('deploy');await renderDeploy();showPublished(r.url)}catch(e){toast(e.message,1)}}
async function unpublish(){await api(`/projects/${proj}/unpublish`,{method:'POST'});await loadProjects();updateStatus();renderDeploy();toast('Unpublished')}
function updateStatus(){const p=pinfo();const st=$('#stPub');st.textContent=p.published?`● Live · /sites/${proj}/`:'● Not published';st.parentElement.classList.toggle('pub',!!p.published)}
async function loadVersions(){const v=await api(`/projects/${proj}/versions`);$('#versions').innerHTML=v.slice(0,15).map(x=>`<div><span>${esc(x.label)} <span class="mut">${ago(x.created)}</span></span><a onclick="restoreV(${x.id})">restore</a></div>`).join('')||'<div class="mut">No snapshots yet</div>'}
async function snap(){const l=prompt('Snapshot label (optional):')??'';await api(`/projects/${proj}/versions?label=`+encodeURIComponent(l),{method:'POST'});loadVersions();toast('Snapshot saved')}
async function restoreV(id){if(!confirm('Restore this version? Current state is snapshotted first.'))return;await api(`/projects/${proj}/versions/${id}/restore`,{method:'POST'});await openProject(proj);toast('Restored')}

/* ─────────── DEPLOY VIEW ─────────── */
async function renderDeploy(){if(!proj)return;ghLinkInfo();const p=await api(`/projects/${proj}/settings`);$('#dpName').textContent=proj;
 $('#dpStatus').innerHTML=p.published?`<span class="badge ok">● Live</span> published ${ago(p.published)}`:`<span class="badge">Draft</span> not published yet`;
 const box=$('#dpUrl');box.classList.toggle('hidden',!p.published);box.parentElement.querySelector('.pubOk')?.remove();const url=location.origin+`/sites/${proj}/`;box.querySelector('span').textContent=url;box.querySelector('a').href=url;$('#qrBox').innerHTML='';
 $('#sTitle').value=p.seo_title||'';$('#sDesc').value=p.seo_desc||'';$('#sGa').value=p.ga||'';$('#sPw').value=p.password||'';$('#sKind').value=p.kind;
 $('#domList').innerHTML=p.domains.map(d=>`<div class="row" style="margin-top:8px"><span class="mono">${d.domain}</span><span class="badge ${d.verified?'ok':'warn'}">${d.verified?'verified':'pending'}</span><button class="s" onclick="verifyDom('${d.domain}')">Verify</button><button class="s" onclick="showDns('${d.domain}','${d.token}')">DNS</button><button class="s danger" onclick="delDom('${d.domain}')">✕</button></div>`).join('')||'<p class="mut small">No custom domains yet.</p>';
 appLogs()}
function qr(){const u=$('#dpUrl span').textContent;$('#qrBox').innerHTML=`<img src="https://api.qrserver.com/v1/create-qr-code/?size=160x160&data=${encodeURIComponent(u)}" alt="QR">`}
async function exportZip(){location.href=`/api/projects/${proj}/export`}
async function saveSettings(){await api(`/projects/${proj}/settings`,{method:'PUT',body:JSON.stringify({seo_title:$('#sTitle').value,seo_desc:$('#sDesc').value,ga:$('#sGa').value,password:$('#sPw').value,kind:$('#sKind').value})});await loadProjects();toast('Settings saved')}
async function renameProj(){const to=prompt('New name:',proj);if(!to||to===proj)return;try{const r=await api(`/projects/${proj}/rename`,{method:'POST',body:JSON.stringify({to})});await loadProjects();openProject(r.name);renderDeploy()}catch(e){toast(e.message,1)}}
async function dupProj(){const r=await api(`/projects/${proj}/duplicate`,{method:'POST'});await loadProjects();openProject(r.name);renderDeploy();toast('Duplicated → '+r.name)}
async function delProj(){if(prompt(`Type "${proj}" to delete permanently:`)!==proj)return;await api(`/projects/${proj}`,{method:'DELETE'});proj=null;await loadProjects();if(projects[0])openProject(projects[0].name);go('home');toast('Deleted')}
async function appAct(a){try{await api(`/projects/${proj}/app/${a}`,{method:'POST'});toast(a==='start'?'App started':'App stopped');setTimeout(appLogs,1500);loadProjects()}catch(e){toast(e.message,1)}}
async function appLogs(){const s=await api(`/projects/${proj}/app/status`);const b=$('#appState');b.textContent=s.running?`running · port ${s.port} · ${Math.floor(s.uptime/60)}m`:'stopped';b.className='badge '+(s.running?'ok':'');$('#appLog').textContent=s.log||'No logs yet. Start the app or publish a Python/Node project.'}
async function addDomain(){try{const r=await api(`/projects/${proj}/domains`,{method:'POST',body:JSON.stringify({domain:$('#domIn').value})});$('#domIn').value='';renderDeploy();showDns(r.domain,r.token)}catch(e){toast(e.message,1)}}
function showDns(d,tok){alert(`Add these DNS records at your registrar for ${d}:\n\nCNAME  www  →  sites.forgevia.com\nA      @    →  76.76.21.21\nTXT    _forgevia  →  ${tok}\n\nThen click Verify.`)}
async function verifyDom(d){const r=await api(`/domains/${d}/verify`,{method:'POST'});toast(r.verified?'Domain verified':'Not verified yet — DNS may take time',!r.verified);renderDeploy()}
async function delDom(d){await api(`/domains/${d}`,{method:'DELETE'});renderDeploy()}

/* ─────────── TERMINAL ─────────── */
function toggleTerm(){$('#termPane').classList.toggle('hidden');editor?.layout();$('#termIn').focus()}
const hist=[];let hi=0;
async function termKey(e){const i=$('#termIn');if(e.key==='ArrowUp'){hi=Math.max(0,hi-1);i.value=hist[hi]||'';return}if(e.key==='ArrowDown'){hi=Math.min(hist.length,hi+1);i.value=hist[hi]||'';return}if(e.key!=='Enter'||!i.value.trim())return;
 const cmd=i.value;hist.push(cmd);hi=hist.length;i.value='';const out=$('#termOut');out.textContent+=`\n$ ${cmd}\n`;
 if(cmd==='clear'){out.textContent='';return}
 try{const r=await api('/run',{method:'POST',body:JSON.stringify({cmd,project:proj})});out.textContent+=(r.stdout||'')+(r.stderr?r.stderr:'')+(r.code?`[exit ${r.code}]`:'');if(/^(touch|mkdir|rm|mv|cp|npm|pip|echo.*>)/.test(cmd))loadFiles()}catch(e){out.textContent+=e.message}
 out.scrollTop=out.scrollHeight}

/* ─────────── AI ─────────── */
function toggleAi(){$('#aiPane').classList.toggle('hidden');editor?.layout();$('#aiQ').focus()}
async function askAi(){const q=$('#aiQ').value.trim();if(!q)return;$('#aiQ').value='';const box=$('#aiMsgs');box.insertAdjacentHTML('beforeend',`<div class="msg me">${esc(q)}</div>`);
 const sel=editor?.getModel()?.getValueInRange(editor.getSelection())||'';
 const r=await api('/ai',{method:'POST',body:JSON.stringify({prompt:q,context:sel,file:cur||''})});
 const md=t=>esc(t).replace(/\*\*(.+?)\*\*/g,'<b>$1</b>').replace(/`(.+?)`/g,'<code>$1</code>').replace(/\n/g,'<br>');
 let h=`<div class="msg bot">${md(r.text)}`;if(r.code){const code=r.code.replace(/PROJECT/g,proj);const id='c'+Date.now();window[id]=code;h+=`<pre>${esc(code)}</pre><div class="row"><button class="s" onclick="insertCode(window['${id}'])">Insert at cursor</button><button class="s" onclick="copy(window['${id}'])">Copy</button></div>`}
 box.insertAdjacentHTML('beforeend',h+'</div>');box.scrollTop=box.scrollHeight}
function insertCode(c){if(!editor)return;editor.executeEdits('ai',[{range:editor.getSelection(),text:c}]);editor.focus();toast('Inserted')}

/* ─────────── SEO ─────────── */
$$('.subtabs button').forEach(b=>b.onclick=()=>{$$('.subtabs button').forEach(x=>x.classList.toggle('on',x===b));$$('.sub').forEach(s=>s.classList.toggle('on',s.dataset.sub===b.dataset.s))});
const abs=u=>u.startsWith('/')?location.origin+u:u;
const ring=(score,size=120)=>{const c=score>=80?'#22c55e':score>=50?'#f59e0b':'#ef4444';const r=52,C=2*Math.PI*r;return `<div class="ring" style="width:${size}px;height:${size}px"><svg width="${size}" height="${size}" viewBox="0 0 120 120"><circle cx="60" cy="60" r="${r}" fill="none" stroke="#ffffff10" stroke-width="10"/><circle cx="60" cy="60" r="${r}" fill="none" stroke="${c}" stroke-width="10" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C*(1-score/100)}" style="transition:stroke-dashoffset 1s"/></svg><b style="color:${c}">${score}</b></div>`};
async function seoAudit(u){const url=abs(u||$('#seoUrl').value.trim());if(!url)return;$('#seoOut').innerHTML='<div class="card">Auditing…</div>';
 try{const r=await api('/seo/audit',{method:'POST',body:JSON.stringify({url})});const cats=[...new Set(r.checks.map(c=>c.cat))];
  $('#seoOut').innerHTML=`<div class="card score">${ring(r.score)}<div><h2 style="margin:0">${r.passed}/${r.total} checks passed</h2><p class="mut">${r.url} · HTTP ${r.status} · ${r.words} words · robots.txt ${r['robots.txt']?'✓':'✗'} · sitemap ${r['sitemap.xml']?'✓':'✗'}</p><div class="row"><button class="s" onclick="seoAudit('${r.url}')">↻ Re-audit</button><button class="s" onclick="$('#crawlUrl').value='${r.url}';$$('.subtabs button')[1].click();seoCrawl()">Crawl whole site →</button></div></div></div>
  <div class="grid2"><div class="card"><h3>Google preview</h3><div class="serp"><div class="u">${esc(r.serp.url)}</div><div class="t">${esc(r.serp.title)}</div><div class="dsc">${esc(r.serp.desc)}</div></div></div>
  <div class="card"><h3>Top keywords on page</h3><div class="kwchips">${r.keywords.map(k=>`<span title="${k.density}% density">${k.word} <small class="mut">×${k.count}</small></span>`).join('')}</div></div></div>
  ${cats.map(c=>`<div class="card"><h3>${c}</h3>${r.checks.filter(x=>x.cat===c).map(x=>`<div class="check"><div class="d ${x.ok?'ok':'bad'}">${x.ok?'✓':'!'}</div><div><b>${x.name}</b> <span class="mut">— ${esc(x.detail)}</span>${x.fix?`<div class="fix">${esc(x.fix)}</div>`:''}</div></div>`).join('')}</div>`).join('')}`}catch(e){$('#seoOut').innerHTML=`<div class="card" style="color:var(--bad)">${e.message}</div>`}}
async function seoCrawl(){const url=abs($('#crawlUrl').value.trim());if(!url)return;$('#crawlOut').innerHTML='<div class="card">Crawling up to '+$('#crawlN').value+' pages… this can take a minute</div>';
 try{const r=await api('/seo/crawl?limit='+$('#crawlN').value,{method:'POST',body:JSON.stringify({url})});
  $('#crawlOut').innerHTML=`<div class="card score">${ring(r.avg)}<div><h2 style="margin:0">${r.pages.length} pages crawled</h2><p class="mut">${r.broken.length} broken links · ${Object.keys(r.duplicate_titles).length} duplicate titles</p></div></div>
  <div class="card"><table><tr><th>Page</th><th>Title</th><th>Words</th><th>ms</th><th>Issues</th><th>Score</th></tr>${r.pages.map(p=>`<tr><td><a href="${p.url}" target="_blank">${esc(p.url.replace(/^https?:\/\/[^/]+/,'')||'/')}</a></td><td>${esc(p.title||'—').slice(0,50)}</td><td>${p.words}</td><td>${p.ms}</td><td title="${esc(p.issues.join(', '))}">${p.issues.length}</td><td><b style="color:${p.score>=80?'var(--ok)':p.score>=50?'var(--warn)':'var(--bad)'}">${p.score}</b></td></tr>`).join('')}</table></div>
  ${r.broken.length?`<div class="card"><h3>Broken links</h3>${r.broken.map(b=>`<div class="check"><div class="d bad">!</div><div>${esc(b.url)} <span class="mut">— ${esc(b.error)}</span></div></div>`).join('')}</div>`:''}
  ${Object.keys(r.duplicate_titles).length?`<div class="card"><h3>Duplicate titles</h3>${Object.entries(r.duplicate_titles).map(([t,u])=>`<p><b>${esc(t)}</b><br><span class="mut small">${u.map(esc).join('<br>')}</span></p>`).join('')}</div>`:''}`}catch(e){$('#crawlOut').innerHTML=`<div class="card" style="color:var(--bad)">${e.message}</div>`}}
async function seoKw(){const k=$('#kwIn').value.trim();if(!k)return;$('#kwOut').innerHTML='<div class="card">Researching…</div>';const r=await api('/seo/keywords',{method:'POST',body:JSON.stringify({keyword:k})});
 const chips=l=>`<div class="kwchips">${l.map(x=>`<span onclick="$('#kwIn').value='${esc(x)}';seoKw()">${esc(x)}</span>`).join('')||'<span class="mut">none</span>'}</div>`;
 $('#kwOut').innerHTML=`<div class="card"><h3>${r.count} ideas for “${esc(k)}”</h3><button class="s" onclick="copy(${JSON.stringify(r.ideas.join('\n'))})">Copy all</button></div><div class="card"><h3>Questions people ask</h3>${chips(r.questions)}</div><div class="card"><h3>Long-tail (4+ words)</h3>${chips(r.longtail)}</div><div class="card"><h3>All suggestions</h3>${chips(r.ideas)}</div>`}
async function seoGen(){const r=await api('/seo/generate',{method:'POST',body:JSON.stringify({topic:$('#gTopic').value,keywords:$('#gKw').value,brand:$('#gBrand').value,type:$('#gType').value})});
 $('#genOut').innerHTML=`<h3>Google preview</h3><div class="serp"><div class="u">https://yoursite.com/${r.slug}</div><div class="t">${esc(r.title)}</div><div class="dsc">${esc(r.description)}</div></div><h3 style="margin-top:16px">&lt;head&gt; snippet</h3><pre class="log">${esc(r.head)}</pre><div class="row" style="margin-top:8px"><button class="s" onclick="copy(${JSON.stringify(r.head)})">Copy head</button><button class="s" onclick="insertCode(${JSON.stringify(r.head)});go('editor')">Insert in editor</button></div><h3 style="margin-top:16px">Suggested outline</h3><ol>${r.outline.map(o=>`<li>${esc(o)}</li>`).join('')}</ol>`}
async function seoFix(){const p=$('#fixSel').value;$('#fixOut').innerHTML='<p>Fixing…</p>';await api(`/projects/${p}/versions?label=before%20seo%20autofix`,{method:'POST'});const r=await api(`/seo/fix/${p}`,{method:'POST'});
 $('#fixOut').innerHTML=r.fixed.length?`<h3 style="margin-top:16px">Fixed ${r.fixed.length} file(s)</h3>${r.fixed.map(f=>`<div class="check"><div class="d ok">✓</div><div><b>${f.file}</b> <span class="mut">— ${f.fixed.join(', ')}</span></div></div>`).join('')}<div class="row" style="margin-top:12px"><button class="p" onclick="openProject('${p}');go('editor')">Review in editor</button><button class="s" onclick="openProject('${p}').then(publish)">Publish now</button></div>`:'<p class="mut">Nothing to fix — this project already has all essentials.</p>';if(p===proj)openProject(p)}

/* ─────────── SCRAPER ─────────── */
async function scrape(){const url=$('#scUrl').value.trim();if(!url)return;$('#scOut').innerHTML='<pre>Scraping… ⏳</pre>';
 const fields={};$('#scFields').value.split('\n').forEach(l=>{const[k,...v]=l.split(':');if(k&&v.length)fields[k.trim()]=v.join(':').trim()});
 try{last=await api('/scrape',{method:'POST',body:JSON.stringify({url,mode:$('#scMode').value,selector:$('#scSel').value,attr:$('#scAttr').value,fields:Object.keys(fields).length?fields:null,pages:+$('#scPages').value||1,next_selector:$('#scNext').value})});
  $('#scMeta').textContent=`${last.visited.length} page(s) · ${last.count!=null?last.count+' items':(last.data.length/1024).toFixed(1)+' KB'}`;
  const d=last.data;if(Array.isArray(d)&&d.length&&typeof d[0]==='object'&&!Array.isArray(d[0])){const keys=[...new Set(d.flatMap(Object.keys))];$('#scOut').innerHTML=`<div style="overflow:auto;max-height:520px"><table><tr>${keys.map(k=>`<th>${esc(k)}</th>`).join('')}</tr>${d.slice(0,300).map(r=>`<tr>${keys.map(k=>`<td>${/^https?:/.test(r[k])?`<a href="${esc(r[k])}" target="_blank">${esc(String(r[k]).slice(0,80))}</a>`:esc(String(r[k]??'').slice(0,120))}</td>`).join('')}</tr>`).join('')}</table></div>`}
  else $('#scOut').innerHTML=`<pre class="log" style="max-height:520px">${esc(typeof d==='string'?d:JSON.stringify(d,null,2))}</pre>`}catch(e){$('#scOut').innerHTML=`<pre style="color:var(--bad)">${e.message}</pre>`}}
async function scInspect(){const url=$('#scUrl').value.trim();if(!url)return;const r=await api('/scrape/screenshot',{method:'POST',body:JSON.stringify({url})});
 $('#scInspectOut').innerHTML=`<div class="card"><h3>${esc(r.title)}</h3><p class="mut small">${r.links} links · ${r.images} images · ${r.tables} tables · ${r.forms} forms — click a class to use it as selector</p><div class="kwchips">${r.classes.map(([c,n])=>`<span onclick="$('#scSel').value='.${c}'">.${esc(c)} <small class="mut">×${n}</small></span>`).join('')}</div>${r.ids.length?`<p class="mut small" style="margin-top:10px">IDs:</p><div class="kwchips">${r.ids.map(i=>`<span onclick="$('#scSel').value='#${i}'">#${esc(i)}</span>`).join('')}</div>`:''}</div>`}
function dl(t){if(!last)return;let s,mime='application/json';const d=last.data;
 if(t==='json')s=JSON.stringify(d,null,2);else{mime='text/csv';const rows=Array.isArray(d)?(typeof d[0]==='object'&&!Array.isArray(d[0])?[Object.keys(d[0]),...d.map(o=>Object.values(o))]:Array.isArray(d[0])?d.flat():d.map(x=>[x])):[[d]];s=rows.map(r=>(Array.isArray(r)?r:[r]).map(v=>`"${String(v??'').replace(/"/g,'""')}"`).join(',')).join('\n')}
 const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([s],{type:mime}));a.download='forgevia-scrape.'+t;a.click()}

/* ─────────── ANALYTICS ─────────── */
async function loadAnalytics(){const p=$('#anSel').value||proj;if(!p)return;const a=await api(`/projects/${p}/analytics?days=`+$('#anDays').value);
 $('#anTotal').textContent=fmt(a.total);$('#anUniq').textContent=fmt(a.unique);$('#anAvg').textContent=a.unique?(a.total/a.unique).toFixed(1):0;$('#anTop').textContent=a.pages[0]?.[0]||'—';
 const days=+$('#anDays').value,map=Object.fromEntries(a.daily),pts=[];for(let i=days-1;i>=0;i--){const d=new Date(Date.now()-i*864e5).toISOString().slice(0,10);pts.push([d,map[d]||0])}
 const mx=Math.max(1,...pts.map(p=>p[1]));const xs=i=>i/(pts.length-1)*780+10,ys=v=>190-v/mx*170;const path=pts.map((p,i)=>`${i?'L':'M'}${xs(i)},${ys(p[1])}`).join(' ');
 $('#anChart').innerHTML=`<defs><linearGradient id="ag" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#7c5cff" stop-opacity=".5"/><stop offset="1" stop-color="#7c5cff" stop-opacity="0"/></linearGradient></defs><path d="${path} L790,190 L10,190Z" fill="url(#ag)"/><path d="${path}" fill="none" stroke="#a78bfa" stroke-width="2.5" stroke-linejoin="round"/>${pts.map((p,i)=>`<circle cx="${xs(i)}" cy="${ys(p[1])}" r="3" fill="#22d3ee"><title>${p[0]}: ${p[1]} views</title></circle>`).join('')}`;
 const tbl=(l,total)=>l.map(([k,v])=>`<tr><td>${esc(k)}</td><td><div class="bar" style="width:80px;display:inline-block;margin-right:8px;vertical-align:middle"><i style="width:${v/total*100}%"></i></div>${v}</td></tr>`).join('')||'<tr><td class="mut">No data yet — publish and share your site!</td></tr>';
 $('#anPages').innerHTML=tbl(a.pages,a.total);$('#anRefs').innerHTML=tbl(a.referrers,a.total);$('#anDev').innerHTML=tbl(a.devices,a.total);$('#anBr').innerHTML=tbl(a.browsers,a.total)}

/* ─────────── FORMS ─────────── */
let formsData=[];
async function loadForms(){const p=$('#fmSel').value||proj;if(!p)return;formsData=await api(`/projects/${p}/forms`);if(!formsData.length)return $('#fmOut').innerHTML=`<div class="card"><p class="mut">No submissions yet. Add this to your HTML:</p><pre class="log">&lt;form action="/api/forms/${p}/contact" method="post"&gt;\n  &lt;input name="email" type="email" required&gt;\n  &lt;textarea name="message"&gt;&lt;/textarea&gt;\n  &lt;button&gt;Send&lt;/button&gt;\n&lt;/form&gt;</pre></div>`;
 const groups={};formsData.forEach(f=>(groups[f.form]=groups[f.form]||[]).push(f));
 $('#fmOut').innerHTML=Object.entries(groups).map(([name,list])=>{const keys=[...new Set(list.flatMap(f=>Object.keys(f.data)))].filter(k=>!k.startsWith('_'));return `<div class="card"><h3>${esc(name)} <span class="badge">${list.length}</span></h3><div style="overflow:auto"><table><tr><th>When</th>${keys.map(k=>`<th>${esc(k)}</th>`).join('')}<th></th></tr>${list.map(f=>`<tr><td class="mut small">${ago(f.ts)}</td>${keys.map(k=>`<td>${esc(String(f.data[k]??'')).slice(0,100)}</td>`).join('')}<td><button class="s danger" onclick="delForm(${f.id})">✕</button></td></tr>`).join('')}</table></div></div>`}).join('')}
async function delForm(id){await api(`/projects/${$('#fmSel').value}/forms/${id}`,{method:'DELETE'});loadForms()}
function dlForms(){if(!formsData.length)return;const keys=[...new Set(formsData.flatMap(f=>Object.keys(f.data)))];const csv=[['form','time',...keys],...formsData.map(f=>[f.form,new Date(f.ts*1000).toISOString(),...keys.map(k=>f.data[k]??'')])].map(r=>r.map(v=>`"${String(v).replace(/"/g,'""')}"`).join(',')).join('\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));a.download='forms.csv';a.click()}

/* ─────────── MONITOR ─────────── */
async function loadMon(){const ms=await api('/monitors');$('#monOut').innerHTML=ms.map(m=>{const up=m.last_status>=200&&m.last_status<400;return `<div class="card"><div class="rowb" style="margin:0"><div><b>${esc(m.url)}</b><p class="mut small">${m.last_check?'checked '+ago(m.last_check):'pending first check'} · HTTP ${m.last_status||'—'} · ${m.last_ms||0} ms · uptime ${m.uptime??'—'}%</p></div><div class="row" style="margin:0"><span class="badge ${m.last_check?(up?'ok':'bad'):''}">${m.last_check?(up?'● UP':'● DOWN'):'…'}</span><button class="s danger" onclick="delMon(${m.id})">✕</button></div></div><div class="spark" style="margin-top:12px">${m.history.map(h=>`<i class="${h.status>=200&&h.status<400?'':'dn'}" style="height:${Math.min(100,Math.max(15,h.ms/20))}%" title="${new Date(h.ts*1000).toLocaleString()} · ${h.status} · ${h.ms}ms"></i>`).join('')}</div></div>`}).join('')||'<div class="card mut">No monitors yet. Add your published site URL above.</div>'}
async function addMon(){try{await api('/monitors',{method:'POST',body:JSON.stringify({url:abs($('#monUrl').value)})});$('#monUrl').value='';setTimeout(loadMon,2000);loadMon()}catch(e){toast(e.message,1)}}
async function delMon(id){await api('/monitors/'+id,{method:'DELETE'});loadMon()}

/* ─────────── TOOLS ─────────── */
async function tDomain(){$('#tDomOut').innerHTML='<p class="mut">Checking…</p>';const r=await api('/domains/check?name='+encodeURIComponent($('#tDom').value));$('#tDomOut').innerHTML=`<table>${r.map(d=>`<tr><td class="mono">${d.domain}</td><td>${d.available===null?'<span class="badge">?</span>':d.available?'<span class="badge ok">available</span>':'<span class="badge bad">taken</span>'}</td><td>${d.available?`<a class="s" href="${d.buy}" target="_blank">Buy ↗</a>`:''}</td></tr>`).join('')}</table>`}
async function tSpeedRun(){$('#tSpeedOut').innerHTML='<p class="mut">Testing…</p>';try{const r=await api('/tools/speed?url='+encodeURIComponent(abs($('#tSpeed').value)));$('#tSpeedOut').innerHTML=`<div class="score">${ring(r.score,90)}<div><b>TTFB ${r.ttfb_ms} ms</b> · ${r.requests} requests · ${r.total_kb} KB total<br>${r.tips.map(t=>`<div class="mut small">${t}</div>`).join('')||'<span class="mut small">Looking good!</span>'}</div></div><table style="margin-top:10px">${r.assets.slice(0,8).map(a=>`<tr><td class="mono small">${esc(a.url.split('/').pop().slice(0,40))}</td><td>${a.type}</td><td>${(a.size/1024).toFixed(0)} KB</td></tr>`).join('')}</table>`}catch(e){$('#tSpeedOut').innerHTML=`<p style="color:var(--bad)">${e.message}</p>`}}
async function tHeaders(){$('#tHdrOut').innerHTML='<p class="mut">Scanning…</p>';try{const r=await api('/tools/headers?url='+encodeURIComponent(abs($('#tHdr').value)));$('#tHdrOut').innerHTML=`<div class="score">${ring(r.security_score,90)}<div><b>Security headers</b><br>${Object.entries(r.security).map(([k,v])=>`<div class="small" style="color:${v?'var(--ok)':'var(--bad)'}">${v?'✓':'✕'} <span style="color:var(--fg)">${k}</span></div>`).join('')}</div></div><p class="mut small">Server: ${esc(r.server)} · HTTP ${r.status} · ${r.ms} ms</p><pre class="log" style="max-height:160px">${esc(Object.entries(r.headers).map(([k,v])=>k+': '+v).join('\n'))}</pre>`}catch(e){$('#tHdrOut').innerHTML=`<p style="color:var(--bad)">${e.message}</p>`}}
async function tDnsRun(){const r=await api('/tools/dns?domain='+encodeURIComponent($('#tDns').value));$('#tDnsOut').innerHTML=`<table>${Object.entries(r).map(([t,v])=>`<tr><td><b>${t}</b></td><td class="mono small" style="text-align:left">${v.map(esc).join('<br>')||'<span class="mut">—</span>'}</td></tr>`).join('')}</table>`}
async function tWhois(){const r=await api('/tools/whois?domain='+encodeURIComponent($('#tWho').value));$('#tWhoOut').innerHTML=r.error?`<p style="color:var(--bad)">${r.error}</p>`:!r.registered?'<p class="badge ok">Not registered — available!</p>':`<table><tr><td>Registrar</td><td>${esc(r.registrar||'—')}</td></tr><tr><td>Created</td><td>${(r.created||'—').slice(0,10)}</td></tr><tr><td>Expires</td><td>${(r.expires||'—').slice(0,10)}</td></tr><tr><td>Nameservers</td><td class="small">${r.nameservers.map(esc).join('<br>')}</td></tr></table>`}
async function snShare(){const r=await api('/snippets',{method:'POST',body:JSON.stringify({title:$('#snTitle').value||'Untitled',code:$('#snCode').value})});$('#snOut').innerHTML=`<a href="${r.url}" target="_blank">${location.origin}${r.url}</a>`;copy(location.origin+r.url)}
async function pgRun(){$('#pgOut').textContent='Running…';const r=await api('/run',{method:'POST',body:JSON.stringify({code:$('#pgCode').value,lang:$('#pgLang').value})});$('#pgOut').textContent=(r.stdout||'')+(r.stderr||'')+`\n[exit ${r.code} · ${r.ms} ms]`}
$('#pgLang').onchange=e=>$('#pgCode').value={python:'print("Hello from Forgevia")\nprint(sum(range(101)))',node:'console.log("Hello from Forgevia", process.version)\nconsole.log([1,2,3].map(x=>x*x))',bash:'echo "Hello from Forgevia"\nuname -a\ndate'}[e.target.value];

/* global shortcuts */
document.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key==='p'&&$('.view.on').dataset.view==='editor'){e.preventDefault();quickOpen()}});
window.addEventListener('beforeunload',e=>{if(dirty.size){e.preventDefault();e.returnValue=''}});
boot();

/* ─────────── OAUTH & GITHUB ─────────── */
let PROV={};
fetch('/api/auth/providers').then(r=>r.json()).then(p=>{PROV=p;const n=[];if(!p.github)n.push('GitHub');if(!p.google)n.push('Google');if(n.length&&$('#oauthNote'))$('#oauthNote').textContent=n.join(' & ')+' OAuth not configured on this server yet — see README. You can still connect GitHub with a token after signing in.'}).catch(()=>{});
function oauth(p){if(!PROV[p]){toast(p+' sign-in is not configured yet. Ask the admin to add '+p.toUpperCase()+'_CLIENT_ID.',1);return}
 const w=window.open('/api/auth/'+p+'/start','fv_oauth','width=520,height=680');if(!w)location.href='/api/auth/'+p+'/start'}
window.addEventListener('message',e=>{if(e.data&&e.data.forgevia==='oauth'){if(e.data.ok){if(e.data.token)store.set('fv_token',e.data.token);toast('Signed in');boot();loadConnections()}else toast('Sign-in failed',1)}});
async function loadConnections(){if(!$('#connList'))return;try{const c=await api('/connections');const row=(p,label)=>{const d=c[p];return `<div class="conn">${d?.avatar?`<img src="${d.avatar}" alt="">`:`<span class="avatar" style="width:32px;height:32px">${label[0]}</span>`}<div><b>${label}</b><br><span class="mut small">${d?'Connected as '+esc(d.login):'Not connected'}</span></div><span class="grow"></span>${d?`<button class="s danger" onclick="disconnect('${p}')">Disconnect</button>`:`<button class="s" onclick="oauth('${p}')">Connect</button>`}</div>`};
 $('#connList').innerHTML=row('github','GitHub')+row('google','Google');if(c.github)loadRepos()}catch(e){}}
async function disconnect(p){await api('/connections/'+p,{method:'DELETE'});loadConnections();$('#ghRepos').innerHTML=''}
async function ghConnect(){try{const r=await api('/github/connect',{method:'POST',body:JSON.stringify({token:$('#ghTok').value})});$('#ghTok').value='';toast('Connected as '+r.login);loadConnections()}catch(e){toast(e.message,1)}}
async function loadRepos(){try{const l=await api('/github/repos');$('#ghRepos').innerHTML=l.slice(0,40).map(r=>`<span onclick="$('#ghImportRepo').value='${r.full_name}'" title="${r.private?'private':'public'} · updated ${r.updated.slice(0,10)}">${r.private?'🔒 ':''}${esc(r.full_name)}</span>`).join('')}catch(e){}}
async function ghImport(){const repo=$('#ghImportRepo').value.trim();if(!repo)return;toast('Importing…');try{const r=await api('/github/import',{method:'POST',body:JSON.stringify({repo,name:$('#ghImportName').value||null})});toast(`Imported ${r.files} files`);await loadProjects();openProject(r.name);go('editor')}catch(e){toast(e.message,1)}}
async function ghPush(){if(!proj)return;await saveFile(true);$('#ghPushOut').innerHTML='<p class="mut">Pushing…</p>';try{const r=await api(`/projects/${proj}/github/push`,{method:'POST',body:JSON.stringify({repo:$('#ghRepo').value,message:$('#ghMsg').value||'Deploy from Forgevia',private:$('#ghPriv').checked,create_pages:$('#ghPages').checked})});
 $('#ghPushOut').innerHTML=`<div class="urlbox"><span class="mono">${r.repo}@${r.branch} · ${r.files} files · ${r.commit}</span><a class="s" href="${r.url}" target="_blank">Open repo ↗</a>${r.pages_url?`<a class="s" href="${r.pages_url}" target="_blank">Pages ↗</a>`:''}</div>`;toast('Pushed to GitHub');renderActivity()}catch(e){$('#ghPushOut').innerHTML=`<p style="color:var(--bad)">${e.message}</p>`}}
async function ghLinkInfo(){try{const l=await api(`/projects/${proj}/github`);if(l.repo){$('#ghRepo').value=l.repo;$('#ghLinkInfo').textContent=`Linked to ${l.repo} (${l.branch})`+(l.pushed?` · last push ${ago(l.pushed)}`:'')}else{$('#ghLinkInfo').textContent="Push this project's files to a repository as a single commit."}}catch{}}


/* ─────────── ONBOARDING HELPERS ─────────── */
function hideStart(){$('#startPanel').classList.add('hidden');store.set('fv_hideStart','1')}
function mySiteUrl(){const p=projects.find(x=>x.published)||projects[0];return p?location.origin+'/sites/'+p.name+'/':'https://example.com'}
function updateSteps(){const pub=projects.some(p=>p.published);const changed=projects.some(p=>(p.versions||0)>1)||store.get('fv_published')==='1';
 $('#s2')?.classList.toggle('done',!!proj);$('#s3')?.classList.toggle('done',changed);$('#s4')?.classList.toggle('done',store.get('fv_shared')==='1'&&pub)}
async function scDemo(){$('#scUrl').value='https://example.com';$('#scMode').value='headings';$('#scSel').value='';await scrape()}
async function formsDemo(){const p=$('#fmSel').value||proj;if(!p){toast('Create a project first',1);return}
 await fetch('/api/forms/'+p+'/contact',{method:'POST',body:new URLSearchParams({name:'Test visitor',email:'visitor@example.com',message:'Hello from the Forms demo!'})});toast('Test message sent');loadForms()}
async function anDemo(){const p=$('#anSel').value||proj;if(!p){toast('Create a project first',1);return}
 for(let i=0;i<5;i++)await fetch('/api/beacon/'+p,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({p:i%2?'/':'/pricing',r:['https://google.com/','https://twitter.com/',''][i%3]})});toast('5 visits recorded');loadAnalytics()}
function showPublished(url){const full=location.origin+url;const box=document.createElement('div');box.className='pubOk';box.innerHTML=`<h3>✓ Your site is live</h3><p class="mut small">Share this link with anyone. Edit in Code and press Publish again to update it.</p><div class="lnk"><code>${full}</code><button class="s" onclick="copy('${full}');store.set('fv_shared','1');updateSteps()">Copy link</button><a class="p s" style="text-decoration:none" target="_blank" href="${full}">Open ↗</a></div>`;
 const host=$('#dpStatus')?.parentElement;host?.querySelector('.pubOk')?.remove();host?.insertBefore(box,$('#dpUrl'));$('#dpUrl')?.classList.add('hidden');store.set('fv_published','1');updateSteps()}
