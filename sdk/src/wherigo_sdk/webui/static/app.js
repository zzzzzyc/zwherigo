const entitySchemas = {
  zones: { label: "Zones", singular: "zone", fields: ["id", "name", "description"] },
  items: { label: "Items", singular: "item", fields: ["id", "name", "description"] },
  characters: { label: "Characters", singular: "character", fields: ["id", "name", "description"] },
  tasks: { label: "Tasks", singular: "task", fields: ["id", "name", "description"] },
  variables: { label: "Variables", singular: "variable", fields: ["id", "name", "var_type", "value"] },
  inputs: { label: "Inputs", singular: "input", fields: ["id", "name", "variable_id"] },
  media_objects: { label: "Media", singular: "media_object", fields: ["id", "name", "filename"] },
};

const emptyProject = {
  id: "cart-new",
  name: "New Cartridge",
  file_name: "",
  author_scripts: "",
  zones: [],
  items: [],
  characters: [],
  tasks: [],
  variables: [],
  inputs: [],
  media_objects: [],
  events: [],
  extras: {},
};

const state = {
  project: structuredClone(emptyProject),
  selectedCollection: "zones",
  selectedId: null,
  map: null,
  markers: new Map(),
};

const $ = (id) => document.getElementById(id);

function clone(value) {
  return JSON.parse(JSON.stringify(value));
}

function slug(text) {
  return String(text || "entity").trim().toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "") || "entity";
}

function showToast(message) {
  $("toast").textContent = message;
  $("toast").classList.add("show");
  setTimeout(() => $("toast").classList.remove("show"), 2400);
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    ...options,
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
  });
  const text = await response.text();
  const data = text ? JSON.parse(text) : {};
  if (!response.ok || data.ok === false) {
    throw new Error((data.errors || [data.error || response.statusText]).join("; "));
  }
  return data;
}

function projectPayload() {
  return { project: state.project };
}

function setProject(project) {
  state.project = { ...clone(emptyProject), ...project };
  for (const key of Object.keys(entitySchemas)) {
    state.project[key] = state.project[key] || [];
  }
  state.project.events = state.project.events || [];
  state.selectedCollection = "zones";
  state.selectedId = state.project.zones[0]?.id || null;
  renderAll();
}

function renderAll() {
  renderMeta();
  renderNav();
  renderEntityList();
  renderEntityForm();
  renderEvents();
  renderAuthorScripts();
  renderMap();
}

function renderMeta() {
  $("projectId").value = state.project.id || "";
  $("projectName").value = state.project.name || "";
  $("projectFile").value = state.project.file_name || "";
}

function saveMeta() {
  state.project.id = $("projectId").value.trim();
  state.project.name = $("projectName").value.trim();
  state.project.file_name = $("projectFile").value.trim();
}

function renderNav() {
  const nav = $("entityNav");
  nav.innerHTML = "";
  for (const [key, schema] of Object.entries(entitySchemas)) {
    const button = document.createElement("button");
    button.className = key === state.selectedCollection ? "active" : "";
    button.textContent = `${schema.label} (${state.project[key].length})`;
    button.onclick = () => {
      state.selectedCollection = key;
      state.selectedId = state.project[key][0]?.id || null;
      renderAll();
    };
    nav.appendChild(button);
  }
}

function renderEntityList() {
  const list = $("entityList");
  const schema = entitySchemas[state.selectedCollection];
  list.innerHTML = "";
  const toolbar = document.createElement("article");
  toolbar.className = "card entity-toolbar";
  toolbar.innerHTML = `<h2>${schema.label}</h2><button class="filled" type="button">Add ${schema.singular}</button>`;
  toolbar.querySelector("button").onclick = addEntity;
  list.appendChild(toolbar);
  for (const entity of state.project[state.selectedCollection]) {
    const card = document.getElementById("entityCardTemplate").content.firstElementChild.cloneNode(true);
    card.classList.toggle("selected", entity.id === state.selectedId);
    card.querySelector(".entity-type").textContent = schema.singular;
    card.querySelector(".entity-title").textContent = entity.name || entity.id;
    card.onclick = () => {
      state.selectedId = entity.id;
      renderAll();
    };
    card.querySelector(".remove-button").onclick = (event) => {
      event.stopPropagation();
      state.selectedId = entity.id;
      removeEntity();
    };
    renderFields(card.querySelector(".fields"), entity, schema);
    list.appendChild(card);
  }
}

function renderFields(container, entity, schema) {
  for (const field of schema.fields) {
    const wrapper = document.createElement("label");
    const input = document.createElement(field === "description" ? "textarea" : "input");
    input.value = entity[field] ?? "";
    input.oninput = () => {
      if (field === "id") state.selectedId = input.value.trim();
      entity[field] = field === "value" && entity.var_type === "number" ? Number(input.value || 0) : input.value;
      renderNav();
      renderMap();
    };
    wrapper.innerHTML = `<span>${field}</span>`;
    wrapper.appendChild(input);
    container.appendChild(wrapper);
  }
  if (state.selectedCollection === "zones") {
    entity.extras = entity.extras || {};
    container.appendChild(numberField("Latitude (WGS84)", entity.extras.lat ?? 39.9042, (value) => {
      entity.extras.lat = value;
      renderMap();
    }));
    container.appendChild(numberField("Longitude (WGS84)", entity.extras.lon ?? 116.4074, (value) => {
      entity.extras.lon = value;
      renderMap();
    }));
    container.appendChild(numberField("Radius meters", entity.extras.radius_m ?? entity.extras.radius ?? 40, (value) => {
      entity.extras.radius_m = value;
      renderMap();
    }));
  }
}

function currentEntity() {
  return state.project[state.selectedCollection].find((entity) => entity.id === state.selectedId) || null;
}

function defaultEntity() {
  const schema = entitySchemas[state.selectedCollection];
  const id = `${schema.singular}-${state.project[state.selectedCollection].length + 1}`;
  const entity = { id, name: schema.label.slice(0, -1) || schema.label };
  if (schema.fields.includes("description")) entity.description = "";
  if (state.selectedCollection === "variables") {
    entity.var_type = "string";
    entity.value = "";
  }
  if (state.selectedCollection === "inputs") entity.variable_id = state.project.variables[0]?.id || "";
  if (state.selectedCollection === "media_objects") entity.filename = "";
  if (state.selectedCollection === "zones") entity.extras = { lat: 39.9042, lon: 116.4074, radius_m: 40 };
  return entity;
}

function addEntity() {
  const entity = defaultEntity();
  state.project[state.selectedCollection].push(entity);
  state.selectedId = entity.id;
  renderAll();
}

function removeEntity() {
  if (!state.selectedId) return;
  state.project[state.selectedCollection] = state.project[state.selectedCollection].filter((entity) => entity.id !== state.selectedId);
  state.selectedId = state.project[state.selectedCollection][0]?.id || null;
  renderAll();
}

function renderEntityForm() {
  $("selectedZoneInfo").textContent = currentEntity()
    ? `Selected ${state.selectedCollection}: ${currentEntity().name || currentEntity().id}`
    : "Select or add a zone.";
}

function numberField(label, value, onInput) {
  const wrapper = document.createElement("label");
  wrapper.className = "field";
  const input = document.createElement("input");
  input.type = "number";
  input.step = "any";
  input.inputMode = "decimal";
  input.value = value;
  input.onchange = () => onInput(Number(input.value || 0));
  wrapper.innerHTML = `<span>${label}</span>`;
  wrapper.appendChild(input);
  return wrapper;
}

function renderEvents() {
  const list = $("eventList");
  list.innerHTML = "";
  state.project.events.forEach((event, index) => {
    const card = document.createElement("div");
    card.className = "event-card";
    card.innerHTML = `
      <div class="event-grid">
        <label class="field"><span>Name</span><input data-field="name" value="${escapeAttr(event.name || "")}"></label>
        <label class="field"><span>Object name</span><input data-field="object_name" value="${escapeAttr(event.object_name || "")}"></label>
        <label class="field"><span>Type</span><select data-field="event_type">
          <option value="wig">wig</option><option value="callback">callback</option>
        </select></label>
        <label class="field"><span>Callback key</span><input type="number" data-field="callback_key" value="${event.callback_key || 0}"></label>
      </div>
      <label class="field"><span>Lua script</span><textarea data-field="lua_script">${escapeHtml(event.lua_script || "")}</textarea></label>
      <button class="text-button danger" data-remove>Remove event</button>
    `;
    card.querySelector("[data-field='event_type']").value = event.event_type || "wig";
    card.querySelectorAll("[data-field]").forEach((input) => {
      input.oninput = () => {
        const field = input.dataset.field;
        event[field] = field === "callback_key" ? Number(input.value || 0) : input.value;
      };
    });
    card.querySelector("[data-remove]").onclick = () => {
      state.project.events.splice(index, 1);
      renderEvents();
    };
    list.appendChild(card);
  });
}

function addEvent() {
  state.project.events.push({
    name: `On${state.project.events.length + 1}`,
    object_name: state.project.zones[0]?.name || "",
    event_type: "wig",
    callback_key: 0,
    lua_script: "-- Lua here",
    groups: [],
  });
  renderEvents();
}

function renderAuthorScripts() {
  $("authorScripts").value = state.project.author_scripts || "";
}

function initMap() {
  try {
    if (typeof L !== "undefined") {
      state.map = L.map("map", { zoomControl: true }).setView([39.9042, 116.4074], 11);
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
        maxZoom: 19,
        attribution: "&copy; OpenStreetMap contributors",
      }).addTo(state.map);
      state.map.on("click", (event) => {
        const zone = currentEntity();
        if (!zone || state.selectedCollection !== "zones") return;
        zone.extras = zone.extras || {};
        zone.extras.lat = Number(event.latlng.lat.toFixed(6));
        zone.extras.lon = Number(event.latlng.lng.toFixed(6));
        renderAll();
      });
    } else {
      $("map").textContent = "Leaflet is unavailable; edit WGS84 coordinates in the zone fields.";
    }
  } catch (error) {
    $("map").textContent = "Map initialization failed; edit WGS84 coordinates in the zone fields.";
    console.warn("Map initialization failed:", error);
  }
}

function renderMap() {
  if (!state.map) return;
  if (typeof L === "undefined") return;
  try {
    for (const marker of state.markers.values()) marker.remove();
    state.markers.clear();
    const bounds = [];
    for (const zone of state.project.zones) {
      const lat = Number(zone.extras?.lat);
      const lon = Number(zone.extras?.lon);
      if (!Number.isFinite(lat) || !Number.isFinite(lon)) continue;
      const marker = L.marker([lat, lon], { draggable: true }).addTo(state.map);
      marker.bindPopup(`<strong>${escapeHtml(zone.name || zone.id)}</strong><br>WGS84 ${lat.toFixed(6)}, ${lon.toFixed(6)}`);
      marker.on("dragend", () => {
        const point = marker.getLatLng();
        zone.extras = zone.extras || {};
        zone.extras.lat = Number(point.lat.toFixed(6));
        zone.extras.lon = Number(point.lng.toFixed(6));
        if (zone.id === state.selectedId) renderEntityForm();
      });
      marker.on("click", () => {
        state.selectedCollection = "zones";
        state.selectedId = zone.id;
        renderAll();
      });
      state.markers.set(zone.id, marker);
      bounds.push([lat, lon]);
    }
    if (bounds.length) state.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  } catch (error) {
    console.warn("Map render failed:", error);
  }
}

async function validateProject() {
  saveMeta();
  state.project.author_scripts = $("authorScripts").value;
  try {
    const data = await api("/api/project", { method: "POST", body: JSON.stringify(projectPayload()) });
    $("statusLog").textContent = JSON.stringify(data.validation, null, 2);
    showToast(data.validation.valid ? "Project valid" : "Project has errors");
  } catch (error) {
    $("statusLog").textContent = error.message;
    showToast("Validation failed");
  }
}

async function exportLua() {
  saveMeta();
  state.project.author_scripts = $("authorScripts").value;
  await api("/api/project", { method: "POST", body: JSON.stringify(projectPayload()) });
  const response = await fetch("/api/export-lua");
  const lua = await response.text();
  $("luaPreview").value = lua;
  downloadText(`${slug(state.project.name)}.lua`, lua, "text/plain");
  showToast("Lua exported");
}

async function buildArtifacts() {
  saveMeta();
  state.project.author_scripts = $("authorScripts").value;
  await api("/api/project", { method: "POST", body: JSON.stringify(projectPayload()) });
  const data = await api("/api/build", { method: "POST", body: JSON.stringify(projectPayload()) });
  const links = ["lua_file", "gwz_file", "manifest_file"]
    .filter((key) => data[key])
    .map((key) => `<a href="${data.download_base}${data[key]}">${data[key]}</a>`)
    .join("\n");
  $("statusLog").innerHTML = `Build complete\n${links}`;
  showToast("Build complete");
}

function exportJson() {
  saveMeta();
  state.project.author_scripts = $("authorScripts").value;
  downloadText(`${slug(state.project.name)}.wigi.json`, JSON.stringify(state.project, null, 2), "application/json");
  showToast("JSON downloaded");
}

function importJson(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      setProject(JSON.parse(reader.result));
      showToast("Project imported");
    } catch (error) {
      showToast(`Import failed: ${error.message}`);
    }
  };
  reader.readAsText(file);
}

function newProject() {
  setProject(structuredClone(emptyProject));
  showToast("New project ready");
}

function downloadText(filename, text, type) {
  const blob = new Blob([text], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (ch) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#039;" }[ch]));
}

function escapeAttr(text) {
  return escapeHtml(text).replace(/`/g, "&#096;");
}

function wireEvents() {
  $("newProject").onclick = newProject;
  $("importButton").onclick = () => $("fileInput").click();
  $("fileInput").onchange = (event) => importJson(event.target.files[0]);
  $("downloadJson").onclick = exportJson;
  $("validateButton").onclick = validateProject;
  $("exportLua").onclick = exportLua;
  $("buildButton").onclick = buildArtifacts;
  $("addEntity").onclick = addEntity;
  $("deleteEntity").onclick = removeEntity;
  $("addEvent").onclick = addEvent;
  $("projectId").oninput = saveMeta;
  $("projectName").oninput = saveMeta;
  $("projectFile").oninput = saveMeta;
  $("authorScripts").oninput = () => { state.project.author_scripts = $("authorScripts").value; };
}

wireEvents();
initMap();
// Load project from server on startup
fetch("/api/project")
  .then(res => res.json())
  .then(data => setProject(data.cartridge))
  .catch((error) => {
    console.warn("Project load failed:", error);
    setProject(structuredClone(emptyProject));
  });
