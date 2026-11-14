/* GapHunter front-end. build.py copies this to /assets/app.<hash>.js */
(function(){
"use strict";
var d=document,$=function(s,r){return(r||d).querySelector(s)},$$=function(s,r){return Array.prototype.slice.call((r||d).querySelectorAll(s))};
var store={get:function(k,v){try{var x=localStorage.getItem(k);return x?JSON.parse(x):v}catch(e){return v}},set:function(k,v){try{localStorage.setItem(k,JSON.stringify(v))}catch(e){}}};
function esc(s){return String(s==null?"":s).replace(/[&<>"']/g,function(c){return{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]})}
function toast(m){var t=$("#toast");if(!t)return;t.textContent=m;t.classList.add("show");clearTimeout(t._h);t._h=setTimeout(function(){t.classList.remove("show")},2200)}
function copyText(txt,msg){
  function fb(){var dl=$("#copyDialog");if(!dl||!dl.showModal){return}$("textarea",dl).value=txt;dl.showModal();var ta=$("textarea",dl);ta.focus();ta.select()}
  try{navigator.clipboard.writeText(txt).then(function(){toast(msg||"Copied!")},fb)}catch(e){fb()}
}
d.documentElement.classList.remove("no-js");

/* theme */
var SUN='<circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/>',MOON='<path d="M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z"/>';
function paintTheme(){var t=d.documentElement.dataset.theme;var i=$("#themeIcon");if(i)i.innerHTML=t==="dark"?SUN:MOON}
paintTheme();
var tb=$("#themeBtn");if(tb)tb.addEventListener("click",function(){var t=d.documentElement.dataset.theme==="dark"?"light":"dark";d.documentElement.dataset.theme=t;store.set("gh_theme",t);paintTheme()});
var mb=$("#menuBtn");if(mb)mb.addEventListener("click",function(){var n=$("#navLinks");n.classList.toggle("open");mb.setAttribute("aria-expanded",n.classList.contains("open"))});
$$("#navLinks a").forEach(function(a){a.addEventListener("click",function(){$("#navLinks").classList.remove("open")})});

/* scroll ui */
var prog=$("#progress"),top=$("#toTop"),ticking=false;
addEventListener("scroll",function(){if(ticking)return;ticking=true;requestAnimationFrame(function(){var h=d.documentElement,p=h.scrollTop/Math.max(1,h.scrollHeight-h.clientHeight);if(prog)prog.style.transform="scaleX("+p+")";if(top)top.classList.toggle("show",h.scrollTop>700);ticking=false})},{passive:true});
if(top)top.addEventListener("click",function(){scrollTo({top:0,behavior:"smooth"})});
if("IntersectionObserver" in window){var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add("in");$$("[data-count]",e.target).forEach(countUp);io.unobserve(e.target)}})},{threshold:.1});$$(".reveal").forEach(function(el){io.observe(el)})}else{$$(".reveal").forEach(function(el){el.classList.add("in")})}
function countUp(el){var end=+el.dataset.count,t0=performance.now();(function s(n){var k=Math.min(1,(n-t0)/1200);el.textContent=Math.round(end*(1-Math.pow(1-k,3)))+(k===1&&el.dataset.plus?"+":"");if(k<1)requestAnimationFrame(s)})(t0)}

/* saved ideas (shared across pages) */
var saved=store.get("gh_saved2",[]);
function isSaved(id){return saved.some(function(s){return s.id===id})}
function persist(){store.set("gh_saved2",saved);renderSaved()}
function toggleSave(info){
  if(isSaved(info.id)){saved=saved.filter(function(s){return s.id!==info.id});toast("Removed from saved")}else{saved.push(info);toast("Saved 🔖")}
  persist();$$('[data-bm="'+info.id+'"]').forEach(function(b){var on=isSaved(info.id);b.classList.toggle("on",on);b.setAttribute("aria-pressed",on);if(b.dataset.label)b.textContent=on?"✓ Saved":"🔖 Save idea"});
}
function infoFrom(el){return{id:el.dataset.id,title:el.dataset.title,url:el.dataset.url||"",type:el.dataset.type,cat:el.dataset.cat,gap:el.dataset.gap}}
function renderSaved(){
  var c=$("#savedCount");if(c){c.hidden=!saved.length;c.textContent=saved.length}
  var body=$("#drawerBody");if(!body)return;
  body.innerHTML=saved.length?saved.map(function(i){return'<div class="saved-item"><a href="'+esc(i.url||"#explore")+'"><b>'+esc(i.title)+'</b><small>'+esc(i.type)+" · "+esc(i.cat)+" · Gap "+esc(i.gap)+'</small></a><button class="icon-btn" data-rm="'+esc(i.id)+'" aria-label="Remove"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M18 6 6 18M6 6l12 12"/></svg></button></div>'}).join(""):'<div class="empty" style="padding:40px 10px"><p>No saved ideas yet. Tap the bookmark on any idea.</p></div>';
}
renderSaved();
$$("[data-bm]").forEach(function(b){var on=isSaved(b.dataset.bm);b.classList.toggle("on",on);b.setAttribute("aria-pressed",on);if(b.dataset.label&&on)b.textContent="✓ Saved"});
d.addEventListener("click",function(e){
  var b=e.target.closest("[data-bm]");if(b){e.preventDefault();toggleSave(infoFrom(b.closest("[data-id]")||b));return}
  var r=e.target.closest("[data-rm]");if(r){var id=r.dataset.rm;saved=saved.filter(function(s){return s.id!==id});persist();$$('[data-bm="'+id+'"]').forEach(function(x){x.classList.remove("on")});return}
  var cp=e.target.closest("[data-copy]");if(cp){var src=$(cp.dataset.copy);if(src)copyText(src.textContent.trim(),"Idea brief copied ✓")}
});
var drawer=$("#drawer"),scrim=$("#scrim");
function openDrawer(){drawer.classList.add("open");scrim.classList.add("open")}
function closeDrawer(){drawer.classList.remove("open");scrim.classList.remove("open")}
if(drawer){$("#savedBtn").addEventListener("click",openDrawer);$("#drawerClose").addEventListener("click",closeDrawer);scrim.addEventListener("click",closeDrawer);addEventListener("keydown",function(e){if(e.key==="Escape")closeDrawer()})
  $("#clearSaved").addEventListener("click",function(){saved=[];persist();$$("[data-bm]").forEach(function(x){x.classList.remove("on")})});
  $("#exportBtn").addEventListener("click",function(){if(!saved.length){toast("Nothing saved yet");return}var base=location.origin;copyText("# My GapHunter Ideas\n\n"+saved.map(function(i){return"- **"+i.title+"** ("+i.type+", "+i.cat+", Gap "+i.gap+")"+(i.url?" — "+base+i.url:"")}).join("\n"),"Markdown copied ✓")});
}

/* ===== index page only ===== */
var grid=$("#grid");
if(grid){
  /* typed hero */
  var tEl=$("#typed");if(tEl){var words=JSON.parse(tEl.dataset.words),w=0,c=words[0].length,del=true;setTimeout(function tick(){var word=words[w];tEl.textContent=word.slice(0,c);if(!del&&c<word.length){c++;setTimeout(tick,45)}else if(!del){del=true;setTimeout(tick,1800)}else if(c>0){c--;setTimeout(tick,22)}else{del=false;w=(w+1)%words.length;setTimeout(tick,300)}},2200)}

  /* community ideas */
  var CAT_ICON=JSON.parse($("#catIcons").textContent);
  var userIdeas=store.get("gh_user",[]);
  function bars(n){var s='<span class="bars">';for(var k=1;k<=5;k++)s+='<i class="'+(k<=n?"f":"")+'"></i>';return s+"</span>"}
  function userCard(i){return'<article class="card glass" data-id="'+i.id+'" data-title="'+esc(i.title)+'" data-type="'+esc(i.type)+'" data-cat="'+esc(i.cat)+'" data-gap="60" data-diff="3" data-weeks="6" data-budget="Low" data-earn="12" data-added="'+i.added+'" data-search="'+esc((i.title+" "+i.problem+" "+i.cat+" "+i.type).toLowerCase())+'"><div class="card-top"><div class="tags"><span class="tag t-'+i.type.replace(/\s/g,"")+'">'+esc(i.type)+'</span><span class="tag">'+(CAT_ICON[i.cat]||"✨")+" "+esc(i.cat)+'</span><span class="tag" style="color:var(--neon)">Community</span></div><button class="bm" data-bm="'+i.id+'" aria-label="Save idea" aria-pressed="false"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"/></svg></button></div><h3>'+esc(i.title)+'</h3><p class="pitch">'+esc(i.problem)+'</p>'+(i.why?'<div class="why"><b>Why now?</b> '+esc(i.why)+"</div>":"")+'<div class="card-foot"><span>Added by you · saved in this browser</span></div></article>'}
  userIdeas.forEach(function(i){grid.insertAdjacentHTML("beforeend",userCard(i))});

  var cards=$$(".card",grid),PAGE=24,shown=PAGE;
  var S={type:"all",cat:"all",diff:"all",budget:"all",time:"all",sort:"gap",q:""};
  var sorters={gap:function(a,b){return b.dataset.gap-a.dataset.gap},new:function(a,b){return(b.dataset.added||"").localeCompare(a.dataset.added||"")||b.dataset.gap-a.dataset.gap},easy:function(a,b){return a.dataset.diff-b.dataset.diff||a.dataset.weeks-b.dataset.weeks||b.dataset.gap-a.dataset.gap},earn:function(a,b){return b.dataset.earn-a.dataset.earn||b.dataset.gap-a.dataset.gap}};
  function match(c){var x=c.dataset;
    if(S.type!=="all"&&x.type!==S.type)return false;
    if(S.cat==="pk"){if(x.pk!=="1")return false}else if(S.cat==="new"){if(x.new!=="1")return false}else if(S.cat!=="all"&&x.cat!==S.cat)return false;
    var df=+x.diff;if(S.diff==="easy"&&df>2)return false;if(S.diff==="medium"&&df!==3)return false;if(S.diff==="hard"&&df<4)return false;
    if(S.budget!=="all"&&x.budget!==S.budget)return false;
    if(S.time!=="all"){var t=+S.time,wk=+x.weeks;if(t===99?wk<=12:wk>t)return false}
    if(S.q){var words=S.q.toLowerCase().split(/\s+/).filter(Boolean);for(var k=0;k<words.length;k++)if(x.search.indexOf(words[k])<0)return false}
    return true}
  function apply(resetPage){
    if(resetPage)shown=PAGE;
    var list=cards.filter(match).sort(sorters[S.sort]);
    cards.forEach(function(c){c.hidden=true});
    list.forEach(function(c,k){grid.appendChild(c);c.hidden=k>=shown});
    $("#resultMeta").textContent=list.length+" idea"+(list.length===1?"":"s")+" found"+(S.q?" for “"+S.q+"”":"");
    $("#emptyState").hidden=!!list.length;
    $("#moreBtn").hidden=list.length<=shown;
  }
  $("#moreBtn").addEventListener("click",function(){shown+=PAGE;apply(false)});
  $("#catChips").addEventListener("click",function(e){var b=e.target.closest(".chip");if(!b)return;S.cat=b.dataset.v;$$("#catChips .chip").forEach(function(x){x.classList.toggle("on",x===b);x.setAttribute("aria-pressed",x===b)});apply(true)});
  $("#typeSeg").addEventListener("click",function(e){var b=e.target.closest("button");if(!b)return;S.type=b.dataset.v;$$("#typeSeg button").forEach(function(x){x.classList.toggle("on",x===b);x.setAttribute("aria-pressed",x===b)});apply(true)});
  [["#fDiff","diff"],["#fBudget","budget"],["#fTime","time"],["#fSort","sort"]].forEach(function(p){$(p[0]).addEventListener("change",function(e){S[p[1]]=e.target.value;apply(true)})});
  var qT;$("#q").addEventListener("input",function(e){clearTimeout(qT);qT=setTimeout(function(){S.q=e.target.value.trim();apply(true)},150)});
  function reset(){S={type:"all",cat:"all",diff:"all",budget:"all",time:"all",sort:"gap",q:""};$("#q").value="";["#fDiff","#fBudget","#fTime"].forEach(function(s){$(s).value="all"});$("#fSort").value="gap";$$("#typeSeg button").forEach(function(x){x.classList.toggle("on",x.dataset.v==="all")});$$("#catChips .chip").forEach(function(x){x.classList.toggle("on",x.dataset.v==="all")});apply(true)}
  $("#resetBtn").addEventListener("click",reset);$("#emptyReset").addEventListener("click",reset);
  function searchFor(q){S.q=q;$("#q").value=q;apply(true);d.getElementById("explore").scrollIntoView({behavior:"smooth"})}
  $("#heroSearch").addEventListener("submit",function(e){e.preventDefault();searchFor($("#heroQ").value.trim())});
  d.addEventListener("click",function(e){var t=e.target.closest("[data-q]");if(t){e.preventDefault();searchFor(t.dataset.q)}});
  var qp=new URLSearchParams(location.search).get("q");if(qp){$("#heroQ").value=qp;S.q=qp;$("#q").value=qp}
  apply(true);

  /* generator */
  var G=JSON.parse($("#genData").textContent),spinning=false;
  function pick(a){return a[Math.floor(Math.random()*a.length)]}
  $("#genForm").addEventListener("submit",function(e){e.preventDefault();if(spinning)return;spinning=true;
    var skill=$("#gSkill").value,budget=$("#gBudget").value,cat=$("#gCat").value;
    var pools=[G.aud[cat]||G.aud.AI,G.fmt[skill],G.twist[budget]],finals=pools.map(pick);
    $("#genOut").innerHTML="<p>🎰 Spinning…</p>";
    ["#r1","#r2","#r3"].forEach(function(s,k){var r=$(s),b=$("b",r);r.classList.remove("done");r.classList.add("spin");var iv=setInterval(function(){b.textContent=pick(pools[k])},80);
      setTimeout(function(){clearInterval(iv);r.classList.remove("spin");r.classList.add("done");b.textContent=finals[k];if(k===2)done(finals,skill,budget,cat)},900+k*400)})});
  function done(f,skill,budget,cat){spinning=false;
    var pool=cards.filter(function(c){return c.dataset.cat===cat&&c.dataset.url});
    var fit=pool.filter(function(c){var x=c.dataset;return(skill==="nocode"?+x.diff<=2:skill==="marketing"?(x.type==="Service"||+x.diff<=2):true)&&(budget==="High"||x.budget!=="High")});
    var m=(fit.length?fit:pool).sort(sorters.gap)[0];
    $("#genOut").innerHTML="<h3>"+(/^[aeiou]/i.test(f[1])?"An ":"A ")+esc(f[1])+" for "+esc(f[0])+" "+esc(f[2])+".</h3><p>Next step: talk to 5 "+esc(f[0])+" this week and ask how they solve this today. If they already pay for a workaround, you have a gap.</p>"+(m?'<div style="margin-top:14px;padding-top:14px;border-top:1px solid var(--border)"><p style="margin-bottom:8px">Closest real gap in our list:</p><a class="btn btn-ghost btn-sm" href="'+esc(m.dataset.url)+'">'+esc(m.dataset.title)+" · Gap "+m.dataset.gap+" →</a></div>":"")}

  /* calculator */
  var cur={m:0,y:0,p:0},raf;function fmtN(n){return Math.round(n).toLocaleString()}
  function calc(){var c=$("#cCur").value,price=+$("#cPrice").value,users=+$("#cUsers").value,conv=+$("#cConv").value,months=+$("#cMonths").value;
    $("#cPriceV").textContent=c+price;$("#cUsersV").textContent=fmtN(users);$("#cConvV").textContent=conv+"%";$("#cMonthsV").textContent=months;
    var paying=users*conv/100*months,monthly=paying*price,target={p:paying,m:monthly,y:monthly*12},from={p:cur.p,m:cur.m,y:cur.y},t0=performance.now();cancelAnimationFrame(raf);
    (function step(n){var k=Math.min(1,(n-t0)/450),e=1-Math.pow(1-k,3);for(var key in target)cur[key]=from[key]+(target[key]-from[key])*e;$("#cMonthly").textContent=c+fmtN(cur.m);$("#cYearly").textContent=c+fmtN(cur.y);$("#cPaying").textContent=fmtN(cur.p);if(k<1)raf=requestAnimationFrame(step)})(t0)}
  ["#cCur","#cPrice","#cUsers","#cConv","#cMonths"].forEach(function(s){$(s).addEventListener("input",calc)});calc();

  /* submit idea */
  $("#submitForm").addEventListener("submit",function(e){e.preventDefault();var t=$("#sTitle").value.trim(),pr=$("#sProb").value.trim();if(!t||!pr)return;
    var i={id:"u"+Date.now(),title:t,problem:pr,type:$("#sType").value,cat:$("#sCat").value,why:$("#sWhy").value.trim(),added:new Date().toISOString().slice(0,10)};
    userIdeas.push(i);store.set("gh_user",userIdeas);grid.insertAdjacentHTML("afterbegin",userCard(i));cards=$$(".card",grid);e.target.reset();S.sort="new";$("#fSort").value="new";apply(true);toast("Idea added 🎉");d.getElementById("explore").scrollIntoView({behavior:"smooth"})});

}
})();
