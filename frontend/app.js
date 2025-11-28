const API_BASE = 'https://bcg-pitchpilot-backend.onrender.com';


const api = {
  async catalog() {
    const res = await fetch(`${API_BASE}/api/catalog`);
    if (!res.ok) throw new Error('Failed to load catalog');
    return res.json();
  },
  async recommend(payload) {
    const res = await fetch(`${API_BASE}/api/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(msg || 'Recommendation failed');
    }
    return res.json();
  },
  async generate(payload) {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const msg = await res.text();
      throw new Error(msg || 'Generation failed');
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'final_recommended_pitch.pdf';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
    toast('final_recommended_pitch.pdf downloaded');
  }
};

const state = { soldProducts: new Set() };

function toast(message) {
  const t = document.getElementById('toast');
  t.querySelector('span').textContent = message;
  t.classList.remove('hidden');
  setTimeout(() => t.classList.add('hidden'), 2200);
}

function setLoading(v) {
  document.getElementById('btn-generate').disabled = v;
  document.getElementById('spinner').classList.toggle('hidden', !v);
  document.getElementById('btn-text').textContent = v ? 'Generating…' : 'Recommended Product';
}

function renderSoldTags() {
  const container = document.getElementById('sold_products_tags');
  container.innerHTML = '';
  state.soldProducts.forEach(id => {
    const chip = document.createElement('div');
    chip.className = 'inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-200 text-slate-800 text-xs font-medium';
    chip.innerHTML = `
      <span>${id}</span>
      <button type="button" class="text-slate-500 hover:text-slate-800 text-xs" data-id="${id}">&times;</button>
    `;
    container.appendChild(chip);
  });
  container.querySelectorAll('button[data-id]').forEach(btn => {
    btn.addEventListener('click', () => {
      const id = btn.getAttribute('data-id');
      state.soldProducts.delete(id);
      renderSoldTags();
    });
  });
}

function renderRecommendations(data) {
  const panel = document.getElementById('reco-panel');
  const list = document.getElementById('reco-list');
  list.innerHTML = '';

  (data.recommended || []).forEach((rec, index) => {
    const block = document.createElement('div');
    block.innerHTML = `
      <div class="font-semibold text-slate-800">${index + 1}. ${rec.id} – ${rec.name}</div>
      <ul class="list-disc pl-5 text-slate-700 mt-1">
        ${(rec.talking_points || []).map(tp => `<li>${tp}</li>`).join('')}
      </ul>
    `;
    list.appendChild(block);
  });

  const hasRecs = (data.recommended || []).length > 0;
  panel.classList.toggle('hidden', !hasRecs);
  if (hasRecs) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

async function init() {
  try {
    const data = await api.catalog();

    const industrySel = document.getElementById('industry');
    (data.industries || []).forEach(i => {
      const opt = document.createElement('option');
      opt.value = i;
      opt.textContent = i;
      industrySel.appendChild(opt);
    });

    const soldSel = document.getElementById('sold_products_select');
    soldSel.innerHTML = '';
    const placeholderOpt = document.createElement('option');
    placeholderOpt.value = '';
    placeholderOpt.textContent = 'Select a product to mark as sold';
    soldSel.appendChild(placeholderOpt);

    (data.product_ids || []).forEach(pid => {
      const opt = document.createElement('option');
      opt.value = pid;
      opt.textContent = pid;
      soldSel.appendChild(opt);
    });

    soldSel.addEventListener('change', () => {
      const val = soldSel.value;
      if (val) {
        state.soldProducts.add(val);
        renderSoldTags();
        soldSel.value = '';
      }
    });
  } catch (e) {
    const err = document.getElementById('error');
    err.textContent = e.message;
    err.classList.remove('hidden');
  }
}

document.getElementById('btn-generate').addEventListener('click', async () => {
  const industry = document.getElementById('industry').value;
  const budget = Number(document.getElementById('budget').value || '0');
  const sizeVal = document.getElementById('size').value;
  const size = sizeVal ? Number(sizeVal) : null;
  const client_name = document.getElementById('client_name').value || null;
  const nam_name = document.getElementById('nam_name').value || null;

  const bandwidth_mbps = 100; // fixed for scoring
  const products_already_sold = Array.from(state.soldProducts);

  const payload = {
    industry,
    annual_budget_inr: budget,
    bandwidth_mbps,
    size,
    products_already_sold,
    client_name,
    nam_name
  };

  const err = document.getElementById('error');
  err.classList.add('hidden');
  err.textContent = '';

  setLoading(true);
  try {
    const reco = await api.recommend(payload);
    renderRecommendations(reco);
    await api.generate(payload);
  } catch (e) {
    err.textContent = e.message;
    err.classList.remove('hidden');
  } finally {
    setLoading(false);
  }
});

init();
