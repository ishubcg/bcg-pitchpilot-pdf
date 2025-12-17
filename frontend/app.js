// ------------------------------
// API BASE URL
// ------------------------------
// const API_BASE = 'http://localhost:8000';
const API_BASE = 'https://bcg-pitchpilot-backend.onrender.com';

// ------------------------------
// API WRAPPER
// ------------------------------
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
    const url = URL.createObjectURL(blob);

    const a = document.createElement("a");
    a.href = url;
    a.download = "final_recommended_pitch.pdf";
    document.body.appendChild(a);
    a.click();
    a.remove();

    URL.revokeObjectURL(url);
    toast("final_recommended_pitch.pdf downloaded");
  }
};

// ------------------------------
// Allowed Products
// ------------------------------
const allowedProducts = [
  "MPLS","ILL","SD_WAN","IOT","DARK_FIBER","VSAT","CNPN_PRIVATE_5G",
  "DATA_CENTRE_SERVICES","WIFI","SIP","CCTV","BULK_FTTH",
  "BULK_SMS_CPAAS","ISDN_PRI_SERVICES"
];

const state = {
  soldProducts: new Set(),
  productMap: {},
  allProducts: []
};

// ------------------------------
// Toast Function
// ------------------------------
function toast(message) {
  const t = document.getElementById("toast");
  t.querySelector("span").textContent = message;
  t.classList.remove("hidden");
  setTimeout(() => t.classList.add("hidden"), 2200);
}

// ------------------------------
// VALIDATION
// ------------------------------
function validateForm() {
  const requiredFields = [
    "client_name",
    "company_name",
    "nam_name",
    "nam_circle_search",   // UPDATED FIELD
    "industry",
    "budget_band"
  ];

  let valid = true;
  let firstInvalid = null;

  requiredFields.forEach(id => {
    const el = document.getElementById(id);

    if (!el.value.trim()) {
      if (el.dataset.touched === "true") {
        el.classList.add("input-error");
      }
      valid = false;
      if (!firstInvalid) firstInvalid = el;
    } else {
      el.classList.remove("input-error");
    }
  });

  document.getElementById("btn-generate").disabled = !valid;

  if (!valid && firstInvalid && firstInvalid.dataset.touched === "true") {
    firstInvalid.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  return valid;
}

// ------------------------------
// Sold Product Tags
// ------------------------------
function renderSoldTags() {
  const container = document.getElementById("sold_products_tags");
  container.innerHTML = "";

  state.soldProducts.forEach(id => {
    const name = state.productMap[id] || id;

    const chip = document.createElement("div");
    chip.className =
      "inline-flex items-center gap-1 px-3 py-1 rounded-full bg-slate-200 text-slate-800 text-xs font-medium";

    chip.innerHTML = `
      <span>${name}</span>
      <button type="button" data-id="${id}" class="text-slate-500">&times;</button>
    `;

    container.appendChild(chip);
  });

  container.querySelectorAll("button[data-id]").forEach(btn => {
    btn.onclick = () => {
      state.soldProducts.delete(btn.dataset.id);
      renderSoldTags();
    };
  });
}

// ------------------------------
// Render Recommendations
// ------------------------------
function renderRecommendations(data) {
  const panel = document.getElementById("reco-panel");
  const list = document.getElementById("reco-list");
  list.innerHTML = "";

  data.recommended.forEach((rec, idx) => {
    const div = document.createElement("div");
    div.innerHTML = `
      <div class="font-semibold">${idx + 1}. ${rec.name}</div>
      <ul class="list-disc pl-5 mt-1">
        ${rec.talking_points.map(tp => `<li>${tp}</li>`).join("")}
      </ul>
    `;
    list.appendChild(div);
  });

  // Add product pitch downloads
  const downloadSec = document.createElement("div");
  downloadSec.className = "mt-8 border-t pt-4";
  downloadSec.innerHTML = `
    <h4 class="text-sm font-semibold mb-2">Download Any Product Pitch Deck</h4>
    <div id="all-product-buttons" class="flex flex-wrap gap-3"></div>
  `;
  list.appendChild(downloadSec);

  const btnContainer = downloadSec.querySelector("#all-product-buttons");

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

// ------------------------------
// NAM/KAM CIRCLE SEARCHABLE DROPDOWN
// ------------------------------
const CIRCLES = [
  "Andhra Pradesh","Assam","Bihar","Chennai","Delhi",
  "Gujarat","Haryana","Himachal Pradesh","Jammu & Kashmir",
  "Karnataka","Kerala","Kolkata","Madhya Pradesh","Maharashtra",
  "Mumbai","North East 1", "North East 2", "Odisha","Punjab","Rajasthan",
  "Tamil Nadu","Uttar Pradesh (East)","Uttar Pradesh (West)",
  "West Bengal", "Chhattisgarh", "Andaman & Nicobar", "Jharkhand", "Sikkim", "Telangana", "Uttarakhand", "CNTX N", "CNTX S"
];

const circleInput = document.getElementById("nam_circle_search");
const dropdown = document.getElementById("circle_dropdown");

function renderCircleOptions(filter = "") {
  dropdown.innerHTML = "";

  const filtered = CIRCLES.filter(c =>
    c.toLowerCase().includes(filter.toLowerCase())
  );

  filtered.forEach(circle => {
    const option = document.createElement("div");
    option.className = "px-4 py-2 hover:bg-slate-100 cursor-pointer text-sm";
    option.textContent = circle;
    option.onclick = () => {
      circleInput.value = circle;
      dropdown.classList.add("hidden");
      circleInput.dataset.touched = "true";
      validateForm();
    };
    dropdown.appendChild(option);
  });

  dropdown.classList.remove("hidden");
}

circleInput.addEventListener("click", () => renderCircleOptions(""));
circleInput.addEventListener("input", () => renderCircleOptions(circleInput.value));

document.addEventListener("click", (e) => {
  if (!circleInput.contains(e.target) && !dropdown.contains(e.target)) {
    dropdown.classList.add("hidden");
  }
});

// ------------------------------
// INIT
// ------------------------------
async function init() {
  const data = await api.catalog();

  state.allProducts = data.products || [];

  // Industry dropdown
  const indSel = document.getElementById("industry");
  indSel.innerHTML = `<option value="">Select an Industry</option>`;
  data.industries.forEach(i => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = i;
    indSel.appendChild(opt);
  });

  // Sold product dropdown
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

  // Validation triggers
  [
    "client_name",
    "company_name",
    "nam_name",
    "nam_circle_search",
    "industry",
    "budget_band"
  ].forEach(id => {
    const el = document.getElementById(id);
    el.addEventListener("input", () => {
      el.dataset.touched = "true";
      validateForm();
    });
    el.addEventListener("change", () => {
      el.dataset.touched = "true";
      validateForm();
    });
  });

  validateForm();
}

// ------------------------------
// Generate Pitch
// ------------------------------
document.getElementById("btn-generate").onclick = async () => {
  if (!validateForm()) return;

  const payload = {
    client_name: document.getElementById("client_name").value.trim(),
    company_name: document.getElementById("company_name").value.trim(),
    client_email: document.getElementById("client_email").value.trim(),
    nam_name: document.getElementById("nam_name").value.trim(),
    nam_circle: document.getElementById("nam_circle_search").value.trim(),
    industry: document.getElementById("industry").value,
    budget_band: document.getElementById("budget_band").value,
    size: document.getElementById("size").value || null,
    products_already_sold: Array.from(state.soldProducts),
    bandwidth_mbps: 100
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
