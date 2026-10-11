let page = 1; const pageSize = 25;
const $ = id => document.getElementById(id);
const badge = s => s >= 88 ? 'score-A' : s >= 73 ? 'score-B' : s >= 55 ? 'score-C' : 'score-D';

async function loadFacets() {
  const f = await (await fetch('/api/facets')).json();
  f.industries.forEach(i => $('industry').insertAdjacentHTML('beforeend', `<option>${i}</option>`));
  f.countries.forEach(c => $('country').insertAdjacentHTML('beforeend', `<option>${c}</option>`));
  const s = await (await fetch('/api/stats')).json();
  $('stats').innerHTML = `<h2 class="font-bold mb-1">Pipeline</h2>
    <div class="grid grid-cols-2 gap-2">
    <div class="rounded-lg bg-slate-50 p-2"><div class="text-[11px] text-slate-500">Total</div><div class="font-extrabold text-lg">${s.total}</div></div>
    <div class="rounded-lg bg-slate-50 p-2"><div class="text-[11px] text-slate-500">Avg score</div><div class="font-extrabold text-lg">${s.avg_score}</div></div>
    <div class="rounded-lg bg-slate-50 p-2"><div class="text-[11px] text-slate-500">Valid emails</div><div class="font-extrabold text-lg text-emerald-600">${s.valid_emails}</div></div>
    <div class="rounded-lg bg-slate-50 p-2"><div class="text-[11px] text-slate-500">A-tier</div><div class="font-extrabold text-lg">${s.by_tier['A — Prioritize'] || 0}</div></div>
    </div>`;
}

async function search() {
  const p = new URLSearchParams({ q: $('q').value, industry: $('industry').value, country: $('country').value, tier: $('tier').value, min_emp: $('minEmp').value || 0, min_score: $('minScore').value || 0, page, page_size: pageSize, verify: $('verify').checked, dedupe_on: $('dedupe').checked, sort: 'score_desc' });
  const r = await (await fetch('/api/leads?' + p)).json();
  $('meta').textContent = `${r.total} leads (page ${r.page}) · dedupe removed ${r.removed_duplicates || 0}`;
  $('page').textContent = `Page ${r.page} of ${Math.max(1, Math.ceil(r.total / pageSize))}`;
  $('rows').innerHTML = r.items.map(L => `<tr class="border-t hover:bg-slate-50">
    <td class="p-2"><b>${L.company}</b><div class="text-[11px] text-slate-500">${L.industry} · ${L.city}, ${L.country}</div><div class="text-[11px] text-indigo-600">${L.domain}</div></td>
    <td class="p-2">${L.contact}<div class="text-[11px] text-slate-500">${L.title}</div></td>
    <td class="p-2 font-mono text-[12px]">${L.email || '<span class=text-slate-300>—</span>'}<div class="text-[11px] font-sans ${L.verify.email_status === 'valid' ? 'text-emerald-600' : L.verify.email_status === 'invalid' ? 'text-red-500' : 'text-amber-600'}">${L.verify.email_status}</div></td>
    <td class="p-2"><span class="px-2 py-1 rounded-full font-bold ${badge(L.score)}">${L.score}</span></td>
    <td class="p-2 text-[12px]">${L.tier}</td>
    <td class="p-2">${L.employees}</td></tr>`).join('') || '<tr><td class=p-4 colspan=6>No leads match. Lower min score.</td></tr>';
}

$('searchBtn').onclick = () => { page = 1; search(); };
$('prev').onclick = () => { if (page > 1) { page--; search(); } };
$('next').onclick = () => { page++; search(); };
$('exportBtn').onclick = () => {
  const p = new URLSearchParams({ q: $('q').value, industry: $('industry').value, country: $('country').value, min_score: $('minScore').value || 0, verify: true });
  window.location = '/api/export?' + p;
};
['q', 'industry', 'country', 'tier', 'minEmp', 'minScore', 'verify', 'dedupe'].forEach(id => $(id).addEventListener('change', () => { page = 1; search(); }));
loadFacets().then(search);
