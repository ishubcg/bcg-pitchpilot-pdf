// const API_BASE = 'http://localhost:8000';
const API_BASE = 'https://bcg-pitchpilot-backend.onrender.com';

// const api = {
//   async catalog() {
//     const res = await fetch(`${API_BASE}/api/catalog`);
//     if (!res.ok) throw new Error('Failed to load catalog');
//     return res.json();
//   },
//   async recommend(payload) {
//     const res = await fetch(`${API_BASE}/api/recommend`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(payload)
//     });
//     if (!res.ok) {
//       const msg = await res.text();
//       throw new Error(msg || 'Recommendation failed');
//     }
//     return res.json();
//   },
//   async generate(payload) {
//     const res = await fetch(`${API_BASE}/api/generate`, {
//       method: 'POST',
//       headers: { 'Content-Type': 'application/json' },
//       body: JSON.stringify(payload)
//     });
//     if (!res.ok) {
//       const msg = await res.text();
//       throw new Error(msg || 'Generation failed');
//     }
//     const blob = await res.blob();
//     const url = URL.createObjectURL(blob);
//     const a = document.createElement('a');
//     a.href = url;
//     a.download = 'final_recommended_pitch.pdf';
//     document.body.appendChild(a);
//     a.click();
//     a.remove();
//     URL.revokeObjectURL(url);
//     toast('final_recommended_pitch.pdf downloaded');
//   }
// };

// const state = {
//   soldProducts: new Set(),
//   productMap: {},
//   allProducts: []
// };

// function toast(message) {
//   const t = document.getElementById('toast');
//   t.querySelector('span').textContent = message;
//   t.classList.remove('hidden');
//   setTimeout(() => t.classList.add('hidden'), 2200);
// }

// function setLoading(v) {
//   document.getElementById('btn-generate').disabled = v;
//   document.getElementById('spinner').classList.toggle('hidden', !v);
//   document.getElementById('btn-text').textContent = v ? 'Generating…' : 'Recommended Product';
// }

// function renderSoldTags() {
//   const container = document.getElementById('sold_products_tags');
//   container.innerHTML = '';
  
//   state.soldProducts.forEach(id => {
//     const name = state.productMap[id] || id;
//     const chip = document.createElement('div');
//     chip.className =
//       'inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-200 text-slate-800 text-xs font-medium';
//     chip.innerHTML = `
//       <span>${name}</span>
//       <button type="button" class="text-slate-500 hover:text-slate-800 text-xs" data-id="${id}">&times;</button>
//     `;
//     container.appendChild(chip);
//   });

//   container.querySelectorAll('button[data-id]').forEach(btn => {
//     btn.addEventListener('click', () => {
//       const id = btn.getAttribute('data-id');
//       state.soldProducts.delete(id);
//       renderSoldTags();
//     });
//   });
// }

// function renderRecommendations(data) {
//   const panel = document.getElementById('reco-panel');
//   const list = document.getElementById('reco-list');
//   list.innerHTML = '';

//   // ----- Show recommended product names & talking points -----
//   (data.recommended || []).forEach((rec, index) => {
//     const block = document.createElement('div');
//     block.innerHTML = `
//       <div class="font-semibold text-slate-800">${index + 1}. ${rec.name}</div>
//       <ul class="list-disc pl-5 text-slate-700 mt-1">
//         ${(rec.talking_points || []).map(tp => `<li>${tp}</li>`).join('')}
//       </ul>
//     `;
//     list.appendChild(block);
//   });

//   // ----- Download ANY product section -----
//   const allSection = document.createElement('div');
//   allSection.className = 'mt-8 border-t pt-4';
//   allSection.innerHTML = `
//     <h4 class="text-sm font-semibold text-slate-800 mb-2">
//       Download Any Product Pitch Deck
//     </h4>
//     <div id="all-product-downloads" class="flex flex-wrap gap-3"></div>
//   `;
//   list.appendChild(allSection);

//   const allBtnContainer = allSection.querySelector('#all-product-downloads');

//   (state.allProducts || []).forEach(prod => {
//     const btn = document.createElement('button');
//     btn.className =
//       'px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-xl text-xs font-medium shadow-soft';
//     btn.textContent = prod.name;

//     btn.addEventListener('click', () => {
//       const url = `${API_BASE}/api/product-pitch/${prod.id}`;
//       const a = document.createElement('a');
//       a.href = url;
//       a.download = `${prod.name}.pdf`;
//       document.body.appendChild(a);
//       a.click();
//       a.remove();
//     });

//     allBtnContainer.appendChild(btn);
//   });

//   // Show panel
//   const hasRecs = (data.recommended || []).length > 0;
//   panel.classList.toggle('hidden', !hasRecs);
//   if (hasRecs) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
// }

// async function init() {
//   try {
//     const data = await api.catalog();

//     // Save full product catalog
//     state.allProducts = data.products || [];

//     // Populate industry dropdown
//     const industrySel = document.getElementById('industry');
//     (data.industries || []).forEach(i => {
//       const opt = document.createElement('option');
//       opt.value = i;
//       opt.textContent = i;
//       industrySel.appendChild(opt);
//     });

//     // Populate budget dropdown (NO DUPLICATES)
//     const budgetSel = document.getElementById('budget_band');
//     // Do NOT append more options — index.html already contains Low/Medium/High

//     // Build product map + sold dropdown
//     state.productMap = {};
//     const soldSel = document.getElementById('sold_products_select');
//     soldSel.innerHTML = '';

//     const placeholderOpt = document.createElement('option');
//     placeholderOpt.value = '';
//     placeholderOpt.textContent = 'Select a product to mark as sold';
//     soldSel.appendChild(placeholderOpt);

//     (data.product_ids || []).forEach(item => {
//       state.productMap[item.id] = item.name;

//       const opt = document.createElement('option');
//       opt.value = item.id;
//       opt.textContent = item.name;
//       soldSel.appendChild(opt);
//     });

//     soldSel.addEventListener('change', () => {
//       const val = soldSel.value;
//       if (val) {
//         state.soldProducts.add(val);
//         renderSoldTags();
//         soldSel.value = '';
//       }
//     });

//   } catch (e) {
//     const err = document.getElementById('error');
//     err.textContent = e.message;
//     err.classList.remove('hidden');
//   }
// }

// document.getElementById('btn-generate').addEventListener('click', async () => {
//   const industry = document.getElementById('industry').value;
//   const budget_band = document.getElementById('budget_band').value;
//   const sizeVal = document.getElementById('size').value;
//   const size = sizeVal ? Number(sizeVal) : null;
//   const client_name = document.getElementById('client_name').value || null;
//   const nam_name = document.getElementById('nam_name').value || null;

//   const bandwidth_mbps = 100;
//   const products_already_sold = Array.from(state.soldProducts);

//   const payload = {
//     industry,
//     budget_band,
//     bandwidth_mbps,
//     size,
//     products_already_sold,
//     client_name,
//     nam_name
//   };

//   const err = document.getElementById('error');
//   err.classList.add('hidden');
//   err.textContent = '';

//   if (!industry || !budget_band) {
//     err.textContent = 'Please select both Industry and Budget Band.';
//     err.classList.remove('hidden');
//     return;
//   }

//   setLoading(true);
//   try {
//     const reco = await api.recommend(payload);
//     renderRecommendations(reco);
//     await api.generate(payload);
//   } catch (e) {
//     err.textContent = e.message;
//     err.classList.remove('hidden');
//   } finally {
//     setLoading(false);
//   }
// });

// init();


// Only Selected Products:


const api = {
  async catalog() {
    return (await fetch(`${API_BASE}/api/catalog`)).json();
  },
  async recommend(payload) {
    const res = await fetch(`${API_BASE}/api/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    return res.json();
  },
  async generate(payload) {
    const res = await fetch(`${API_BASE}/api/generate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error(await res.text());
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "final_recommended_pitch.pdf";
    a.click();
  }
};

const allowedProducts = [
  "MPLS","ILL","SDWAN","IoT",
  "Dark_Fiber","VSAT","CNPN","Data_Center_Services"
];

const state = {
  soldProducts: new Set(),
  productMap: {},
  allProducts: []
};


// ---------- FIELD VALIDATION ----------

function validateForm() {
  const client = document.getElementById("client_name");
  const nam = document.getElementById("nam_name");
  const ind = document.getElementById("industry");
  const budget = document.getElementById("budget_band");

  const required = [client, nam, ind, budget];

  let firstInvalid = null;
  let valid = true;

  required.forEach(el => {
    if (!el.value.trim()) {
      el.classList.add("border-red-500");
      el.classList.add("bg-red-50");

      if (!firstInvalid) firstInvalid = el;
      valid = false;
    } else {
      el.classList.remove("border-red-500");
      el.classList.remove("bg-red-50");
    }
  });

  document.getElementById("btn-generate").disabled = !valid;

  if (!valid && firstInvalid) {
    firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return valid;
}


// ---------- RENDER TAGS ----------

function renderSoldTags() {
  const container = document.getElementById('sold_products_tags');
  container.innerHTML = '';
  state.soldProducts.forEach(id => {
    const name = state.productMap[id] || id;
    const chip = document.createElement('div');
    chip.className =
      'inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-200 text-slate-800 text-xs font-medium';
    chip.innerHTML = `
      <span>${name}</span>
      <button type="button" class="text-slate-500" data-id="${id}">&times;</button>
    `;
    container.appendChild(chip);
  });

  container.querySelectorAll('button[data-id]').forEach(btn => {
    btn.onclick = () => {
      state.soldProducts.delete(btn.dataset.id);
      renderSoldTags();
    };
  });
}


// ---------- RENDER RECOMMENDATIONS + DOWNLOADS ----------

function renderRecommendations(data) {
  const panel = document.getElementById("reco-panel");
  const list = document.getElementById("reco-list");
  list.innerHTML = "";

  // Recommended list
  data.recommended.forEach((rec, i) => {
    const block = document.createElement("div");
    block.innerHTML = `
      <div class="font-semibold">${i + 1}. ${rec.name}</div>
      <ul class="list-disc pl-5 mt-1">
        ${rec.talking_points.map(t => `<li>${t}</li>`).join("")}
      </ul>
    `;
    list.appendChild(block);
  });

  // Download any product deck
  const allSec = document.createElement("div");
  allSec.className = "mt-8 border-t pt-4";
  allSec.innerHTML = `
    <h4 class="text-sm font-semibold mb-2">Download Any Product Pitch Deck</h4>
    <div id="all-product-buttons" class="flex flex-wrap gap-3"></div>
  `;
  list.appendChild(allSec);

  const btnContainer = allSec.querySelector("#all-product-buttons");

  allowedProducts.forEach(pid => {
    const pObj = state.allProducts.find(p => p.id === pid);
    const name = pObj ? pObj.name : pid.replace(/_/g, " ");
    const btn = document.createElement("button");
    btn.className =
      "px-4 py-2 bg-slate-700 hover:bg-slate-800 text-white rounded-xl text-xs font-medium";
    btn.textContent = name;
    btn.onclick = () => {
      const a = document.createElement("a");
      a.href = `${API_BASE}/api/product-pitch/${pid}`;
      a.download = `${name}.pdf`;
      document.body.appendChild(a);
      a.click();
      a.remove();
    };
    btnContainer.appendChild(btn);
  });

  panel.classList.remove("hidden");
  panel.scrollIntoView({ behavior: "smooth" });
}


// ---------- INIT ----------

async function init() {
  const data = await api.catalog();

  state.allProducts = data.products || [];

  // Industries
  const indSel = document.getElementById("industry");
  data.industries.forEach(ind => {
    const opt = document.createElement("option");
    opt.value = ind;
    opt.textContent = ind;
    indSel.appendChild(opt);
  });

  // Products already sold dropdown
  const soldSel = document.getElementById("sold_products_select");
  soldSel.innerHTML = `<option value="">Select a product to mark as sold</option>`;

  allowedProducts.forEach(pid => {
    const pObj = data.products.find(p => p.id === pid);
    const name = pObj ? pObj.name : pid.replace(/_/g, " ");
    state.productMap[pid] = name;

    const opt = document.createElement("option");
    opt.value = pid;
    opt.textContent = name;
    soldSel.appendChild(opt);
  });

  soldSel.onchange = () => {
    if (soldSel.value) {
      state.soldProducts.add(soldSel.value);
      renderSoldTags();
      soldSel.value = "";
    }
  };

  // Required field validation on input
  ["client_name", "nam_name", "industry", "budget_band"].forEach(id => {
    document.getElementById(id).addEventListener("input", validateForm);
    document.getElementById(id).addEventListener("change", validateForm);
  });

  validateForm();
}

document.getElementById("btn-generate").onclick = async () => {
  if (!validateForm()) return;

  const payload = {
    client_name: document.getElementById("client_name").value.trim(),
    nam_name: document.getElementById("nam_name").value.trim(),
    industry: document.getElementById("industry").value,
    budget_band: document.getElementById("budget_band").value,
    size: document.getElementById("size").value || null,
    bandwidth_mbps: 100,
    products_already_sold: Array.from(state.soldProducts),
  };

  const err = document.getElementById("error");
  err.classList.add("hidden");

  try {
    const reco = await api.recommend(payload);
    renderRecommendations(reco);
    await api.generate(payload);
  } catch (e) {
    err.textContent = e.message;
    err.classList.remove("hidden");
  }
};

init();
