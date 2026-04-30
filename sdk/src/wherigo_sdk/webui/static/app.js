const entitySchemas = {
  zones: { label: "Zones", singular: "zone", fields: ["id", "name", "description"] },
  items: {
    label: "Items",
    singular: "item",
    fields: ["id", "name", "description", "visible", "active", "enabled", "allow_take", "allow_drop", "allow_use", "allow_give"],
  },
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
  presets: [],
  presetDraft: { template_id: "", params: {} },
  mapLayers: new Map(),
  pointLayers: new Map(),
  dirty: false,
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

function markDirty() {
  state.dirty = true;
  if ($("dirtyState")) $("dirtyState").textContent = "Unsaved changes";
}

function clearDirty() {
  state.dirty = false;
  if ($("dirtyState")) $("dirtyState").textContent = "No unsaved changes";
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
  state.project.events.forEach((event) => {
    event.extras = event.extras || {};
    event.extras.editor_mode = event.extras.template ? "template" : "lua";
  });
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
  renderPresetBuilder();
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
  toolbar.innerHTML = `<h2>${schema.label}</h2><button class="filled" type="button">Add ${schema.label}</button>`;
  toolbar.querySelector("button").onclick = addEntity;
  list.appendChild(toolbar);
  for (const entity of state.project[state.selectedCollection]) {
    const card = document.getElementById("entityCardTemplate").content.firstElementChild.cloneNode(true);
    card.classList.toggle("selected", entity.id === state.selectedId);
    card.querySelector(".entity-type").textContent = schema.singular;
    card.querySelector(".entity-title").textContent = entity.name || entity.id;
    const heading = card.querySelector(".entity-heading");
    heading.onclick = () => {
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
  container.innerHTML = "";
  for (const field of schema.fields) {
    const wrapper = document.createElement("label");
    const isBool = typeof entity[field] === "boolean";
    const input = document.createElement(field === "description" ? "textarea" : "input");
    if (isBool) {
      input.type = "checkbox";
      input.checked = Boolean(entity[field]);
      input.onchange = () => {
        entity[field] = input.checked;
        markDirty();
        renderNav();
      };
    } else {
      input.value = entity[field] ?? "";
      input.onchange = () => {
        if (field === "id") state.selectedId = input.value.trim();
        entity[field] = field === "value" && entity.var_type === "number" ? Number(input.value || 0) : input.value;
        markDirty();
        renderNav();
        renderMap();
      };
    }
    input.onclick = (event) => event.stopPropagation();
    input.onfocus = (event) => event.stopPropagation();
    wrapper.onclick = (event) => event.stopPropagation();
    wrapper.innerHTML = `<span>${field}</span>`;
    wrapper.appendChild(input);
    container.appendChild(wrapper);
  }
  if (state.selectedCollection === "zones") {
    entity.extras = entity.extras || {};
    entity.extras.shape_type = entity.extras.shape_type || "circle";
    const shapeField = document.createElement("label");
    const shapeSelect = document.createElement("select");
    shapeSelect.innerHTML = `<option value="circle">Circle</option><option value="polygon">Polygon</option>`;
    shapeSelect.value = entity.extras.shape_type;
    shapeSelect.onchange = () => {
      entity.extras.shape_type = shapeSelect.value;
      if (shapeSelect.value === "polygon") entity.extras.points = entity.extras.points || [];
      markDirty();
      renderAll();
    };
    shapeField.innerHTML = "<span>Shape type</span>";
    shapeField.appendChild(shapeSelect);
    container.appendChild(shapeField);
    container.appendChild(numberField("Latitude (WGS84)", entity.extras.lat ?? 39.9042, (value) => {
      entity.extras.lat = value;
      markDirty();
      renderMap();
    }));
    container.appendChild(numberField("Longitude (WGS84)", entity.extras.lon ?? 116.4074, (value) => {
      entity.extras.lon = value;
      markDirty();
      renderMap();
    }));
    container.appendChild(numberField("Radius meters", entity.extras.radius_m ?? entity.extras.radius ?? 40, (value) => {
      entity.extras.radius_m = value;
      markDirty();
      renderMap();
    }));
    if (entity.extras.shape_type === "polygon") {
      const points = Array.isArray(entity.extras.points) ? entity.extras.points : [];
      const helper = document.createElement("div");
      helper.className = "helper";
      helper.textContent = `Vertices: ${points.length} (click map to append)`;
      container.appendChild(helper);
      const deleteBtn = document.createElement("button");
      deleteBtn.type = "button";
      deleteBtn.className = "secondary";
      deleteBtn.textContent = "Delete last vertex";
      deleteBtn.onclick = () => {
        entity.extras.points = points.slice(0, -1);
        markDirty();
        renderAll();
      };
      container.appendChild(deleteBtn);
      const clearBtn = document.createElement("button");
      clearBtn.type = "button";
      clearBtn.className = "secondary";
      clearBtn.textContent = "Clear vertices";
      clearBtn.onclick = () => {
        entity.extras.points = [];
        markDirty();
        renderAll();
      };
      container.appendChild(clearBtn);
    }
  }
}

function currentEntity() {
  return state.project[state.selectedCollection].find((entity) => entity.id === state.selectedId) || null;
}

function defaultEntity() {
  const schema = entitySchemas[state.selectedCollection];
  const id = `${schema.singular}-${state.project[state.selectedCollection].length + 1}`;
  const defaultName = {
    zones: "Zone",
    items: "Item",
    characters: "Character",
    tasks: "Task",
    variables: "Variable",
    inputs: "Input",
    media_objects: "Media",
  }[state.selectedCollection] || schema.singular;
  const entity = { id, name: defaultName };
  if (schema.fields.includes("description")) entity.description = "";
  if (state.selectedCollection === "variables") {
    entity.var_type = "string";
    entity.value = "";
  }
  if (state.selectedCollection === "inputs") entity.variable_id = state.project.variables[0]?.id || "";
  if (state.selectedCollection === "media_objects") entity.filename = "";
  if (state.selectedCollection === "zones") entity.extras = { lat: 39.9042, lon: 116.4074, radius_m: 40, shape_type: "circle" };
  if (state.selectedCollection === "items") {
    entity.visible = true;
    entity.active = true;
    entity.enabled = true;
    entity.allow_take = true;
    entity.allow_drop = true;
    entity.allow_use = true;
    entity.allow_give = true;
  }
  return entity;
}

async function addEntity() {
  const entity = defaultEntity();
  try {
    const data = await api("/api/command", {
      method: "POST",
      body: JSON.stringify({ op: "add", entity_type: entitySchemas[state.selectedCollection].singular, payload: entity }),
    });
    setProject(data.state.cartridge);
    state.selectedCollection = state.selectedCollection;
    state.selectedId = entity.id;
    markDirty();
    showToast(`Added ${entitySchemas[state.selectedCollection].label}`);
  } catch (error) {
    showToast(`Add failed: ${error.message}`);
  }
}

async function removeEntity() {
  if (!state.selectedId) return;
  try {
    const data = await api("/api/command", {
      method: "POST",
      body: JSON.stringify({
        op: "remove",
        entity_type: entitySchemas[state.selectedCollection].singular,
        entity_id: state.selectedId,
        mode: "restrict",
      }),
    });
    setProject(data.state.cartridge);
    state.selectedId = state.project[state.selectedCollection][0]?.id || null;
    markDirty();
    showToast("Removed");
  } catch (error) {
    showToast(`Remove failed: ${error.message}`);
  }
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
    event.extras = event.extras || {};
    const mode = event.extras.editor_mode || (event.extras.template ? "template" : "lua");
    event.extras.editor_mode = mode;
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
        <label class="field"><span>Mode</span>
          <select data-field="editor_mode">
            <option value="template">template</option>
            <option value="lua">lua</option>
          </select>
        </label>
      </div>
      <div class="field full" data-template-panel></div>
      <label class="field"><span>Lua script</span><textarea data-field="lua_script">${escapeHtml(event.lua_script || "")}</textarea></label>
      <button class="text-button danger" data-remove>Remove event</button>
    `;
    card.querySelector("[data-field='event_type']").value = event.event_type || "wig";
    card.querySelector("[data-field='editor_mode']").value = mode;
    const scriptInput = card.querySelector("[data-field='lua_script']");
    scriptInput.disabled = mode !== "lua";
    const templatePanel = card.querySelector("[data-template-panel]");
    renderEventTemplatePanel(templatePanel, event, index);
    card.querySelectorAll("[data-field]").forEach((input) => {
      input.oninput = () => {
        const field = input.dataset.field;
        if (field === "callback_key") {
          event[field] = Number(input.value || 0);
          markDirty();
          return;
        }
        if (field === "editor_mode") {
          event.extras.editor_mode = input.value;
          if (input.value === "template") event.lua_script = "";
          markDirty();
          renderEvents();
          return;
        }
        event[field] = input.value;
        markDirty();
      };
    });
    card.querySelector("[data-remove]").onclick = () => {
      state.project.events.splice(index, 1);
      markDirty();
      renderEvents();
    };
    list.appendChild(card);
  });
}

function addEvent() {
  state.project.events.push({
    name: `Event${state.project.events.length + 1}`,
    object_name: state.project.zones[0]?.name || "",
    event_type: "wig",
    callback_key: 0,
    lua_script: "",
    groups: [],
    extras: { editor_mode: "lua", trigger: { kind: "zone_on_enter", zone_name: state.project.zones[0]?.name || "" } },
  });
  markDirty();
  renderEvents();
}

function renderEventTemplatePanel(container, event, eventIndex) {
  if (event.extras?.editor_mode !== "template") {
    container.innerHTML = `<span class="helper">Lua advanced mode.</span>`;
    return;
  }
  const template = event.extras?.template || {};
  const preset = state.presets.find((entry) => entry.id === template.id) || state.presets[0];
  if (!preset) {
    container.innerHTML = `<span class="helper">Preset library is loading.</span>`;
    return;
  }
  const params = { ...(template.params || {}) };
  const fields = preset.params
    .map((spec) => {
      const value = params[spec.key] ?? "";
      const inputType = spec.type === "number" ? "number" : "text";
      return `<label class="field"><span>${spec.label}</span><input data-param="${spec.key}" type="${inputType}" value="${escapeAttr(value)}"></label>`;
    })
    .join("");
  container.innerHTML = `
    <div class="event-grid">
      <label class="field"><span>Template</span>
        <select data-template-id>
          ${state.presets.map((entry) => `<option value="${entry.id}" ${entry.id === preset.id ? "selected" : ""}>${entry.label}</option>`).join("")}
        </select>
      </label>
      <div class="helper full">${escapeHtml(preset.description || "")}</div>
      <div class="helper full">Trigger: ${escapeHtml(preset.trigger || "custom")}</div>
      ${fields}
      <button type="button" class="secondary" data-rebuild>Rebuild script from template</button>
    </div>
  `;
  container.querySelector("[data-template-id]").onchange = (e) => {
    const selected = state.presets.find((entry) => entry.id === e.target.value);
    event.extras.template = { id: selected.id, version: selected.version, params: {} };
    markDirty();
    renderEvents();
  };
  container.querySelectorAll("[data-param]").forEach((input) => {
    input.oninput = () => {
      event.extras.template = event.extras.template || { id: preset.id, version: preset.version, params: {} };
      event.extras.template.params[input.dataset.param] = input.type === "number" ? Number(input.value || 0) : input.value;
      markDirty();
    };
  });
  container.querySelector("[data-rebuild]").onclick = async () => {
    try {
      const templateId = container.querySelector("[data-template-id]").value;
      const preview = await api("/api/presets/preview", {
        method: "POST",
        body: JSON.stringify({
          template_id: templateId,
          params: event.extras.template?.params || {},
        }),
      });
      state.project.events[eventIndex] = {
        ...state.project.events[eventIndex],
        ...preview.event,
        extras: {
          ...(preview.event.extras || {}),
          editor_mode: "template",
        },
      };
      markDirty();
      renderEvents();
      showToast("Template rebuilt");
    } catch (error) {
      showToast(`Template rebuild failed: ${error.message}`);
    }
  };
}

function renderPresetBuilder() {
  const box = $("presetBuilder");
  if (!box) return;
  if (!state.presets.length) {
    box.innerHTML = `<div class="helper">Preset library is loading...</div>`;
    return;
  }
  const current = state.presets.find((entry) => entry.id === state.presetDraft.template_id) || state.presets[0];
  state.presetDraft.template_id = current.id;
  state.presetDraft.params = state.presetDraft.params || {};
  const fields = current.params
    .map((spec) => {
      const inputType = spec.type === "number" ? "number" : "text";
      const value = state.presetDraft.params[spec.key] ?? "";
      return `<label class="field"><span>${spec.label}</span><input data-draft-param="${spec.key}" type="${inputType}" value="${escapeAttr(value)}"></label>`;
    })
    .join("");
  box.innerHTML = `
    <div class="event-card">
      <div class="event-grid">
        <label class="field"><span>Event template</span>
          <select id="presetSelect">${state.presets.map((entry) => `<option value="${entry.id}" ${entry.id === current.id ? "selected" : ""}>${entry.label}</option>`).join("")}</select>
        </label>
        <div class="helper full">${escapeHtml(current.description || "")}</div>
        ${fields}
        <button class="secondary" type="button" id="createFromPreset">Create template event</button>
      </div>
    </div>
  `;
  $("presetSelect").onchange = () => {
    state.presetDraft.template_id = $("presetSelect").value;
    state.presetDraft.params = {};
    renderPresetBuilder();
  };
  box.querySelectorAll("[data-draft-param]").forEach((input) => {
    input.oninput = () => {
      state.presetDraft.params[input.dataset.draftParam] = input.type === "number" ? Number(input.value || 0) : input.value;
      markDirty();
    };
  });
  $("createFromPreset").onclick = createEventFromPreset;
}

async function createEventFromPreset() {
  try {
    const data = await api("/api/presets/apply", {
      method: "POST",
      body: JSON.stringify({
        template_id: state.presetDraft.template_id,
        params: state.presetDraft.params,
      }),
    });
    setProject(data.state.cartridge);
    markDirty();
    showToast("Template event added");
  } catch (error) {
    showToast(`Create failed: ${error.message}`);
  }
}

async function createQuickZoneTrigger(templateId) {
  const zone = state.project.zones.find((entry) => entry.id === state.selectedId) || state.project.zones[0];
  if (!zone) {
    showToast("Please create/select a zone first");
    return;
  }
  const message = templateId === "zone_exit" ? `Exit ${zone.name || zone.id}` : `Enter ${zone.name || zone.id}`;
  try {
    const data = await api("/api/presets/apply", {
      method: "POST",
      body: JSON.stringify({
        template_id: templateId,
        params: { zone_name: zone.name || zone.id, message },
      }),
    });
    setProject(data.state.cartridge);
    markDirty();
    showToast("Quick trigger created");
  } catch (error) {
    showToast(`Create failed: ${error.message}`);
  }
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
        const shapeType = zone.extras.shape_type || "circle";
        if (shapeType === "polygon") {
          zone.extras.points = zone.extras.points || [];
          zone.extras.points.push([Number(event.latlng.lat.toFixed(6)), Number(event.latlng.lng.toFixed(6))]);
          markDirty();
        } else {
          zone.extras.lat = Number(event.latlng.lat.toFixed(6));
          zone.extras.lon = Number(event.latlng.lng.toFixed(6));
          markDirty();
        }
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
    for (const layer of state.mapLayers.values()) layer.remove();
    for (const points of state.pointLayers.values()) points.forEach((p) => p.remove());
    state.markers.clear();
    state.mapLayers.clear();
    state.pointLayers.clear();
    const bounds = [];
    for (const zone of state.project.zones) {
      const shapeType = zone.extras?.shape_type || "circle";
      if (shapeType === "polygon") {
        const points = Array.isArray(zone.extras?.points) ? zone.extras.points : [];
        if (points.length >= 1) {
          const polyline = L.polygon(points, { color: zone.id === state.selectedId ? "#1565c0" : "#2e7d32" }).addTo(state.map);
          polyline.on("click", () => {
            state.selectedCollection = "zones";
            state.selectedId = zone.id;
            renderAll();
          });
          state.mapLayers.set(zone.id, polyline);
          points.forEach((pt, idx) => {
            const vertex = L.marker(pt, { draggable: zone.id === state.selectedId }).addTo(state.map);
            vertex.on("click", () => {
              state.selectedCollection = "zones";
              state.selectedId = zone.id;
              renderAll();
            });
            if (zone.id === state.selectedId) {
              vertex.on("dragend", () => {
                const moved = vertex.getLatLng();
                zone.extras.points[idx] = [Number(moved.lat.toFixed(6)), Number(moved.lng.toFixed(6))];
                markDirty();
                renderMap();
              });
            }
            state.pointLayers.set(zone.id, [...(state.pointLayers.get(zone.id) || []), vertex]);
            bounds.push([pt[0], pt[1]]);
          });
        }
        continue;
      }
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
        markDirty();
        if (zone.id === state.selectedId) renderEntityForm();
      });
      marker.on("click", () => {
        state.selectedCollection = "zones";
        state.selectedId = zone.id;
        renderAll();
      });
      state.markers.set(zone.id, marker);
      const radius = Number(zone.extras?.radius_m ?? 40);
      const circle = L.circle([lat, lon], { radius, color: zone.id === state.selectedId ? "#1565c0" : "#2e7d32" }).addTo(state.map);
      state.mapLayers.set(zone.id, circle);
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
    clearDirty();
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
  clearDirty();
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
  clearDirty();
}

function exportJson() {
  saveMeta();
  state.project.author_scripts = $("authorScripts").value;
  downloadText(`${slug(state.project.name)}.wigi.json`, JSON.stringify(state.project, null, 2), "application/json");
  showToast("JSON downloaded");
  clearDirty();
}

function importJson(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      setProject(JSON.parse(reader.result));
      clearDirty();
      showToast("Project imported");
    } catch (error) {
      showToast(`Import failed: ${error.message}`);
    }
  };
  reader.readAsText(file);
}

function newProject() {
  setProject(structuredClone(emptyProject));
  clearDirty();
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
  if ($("quickZoneEnter")) $("quickZoneEnter").onclick = () => createQuickZoneTrigger("zone_enter");
  if ($("quickZoneExit")) $("quickZoneExit").onclick = () => createQuickZoneTrigger("zone_exit");
  $("addEventFromTemplate").onclick = () => { state.presetDraft.template_id = state.presets[0]?.id || ""; renderPresetBuilder(); };
  $("projectId").oninput = () => { saveMeta(); markDirty(); };
  $("projectName").oninput = () => { saveMeta(); markDirty(); };
  $("projectFile").oninput = () => { saveMeta(); markDirty(); };
  $("authorScripts").oninput = () => { state.project.author_scripts = $("authorScripts").value; markDirty(); };
}

wireEvents();
initMap();
fetch("/api/presets")
  .then((res) => res.json())
  .then((data) => {
    state.presets = data.presets || [];
    state.presetDraft.template_id = state.presets[0]?.id || "";
    renderPresetBuilder();
  })
  .catch(() => {
    state.presets = [];
    renderPresetBuilder();
  });
fetch("/api/project")
  .then((res) => res.json())
  .then((data) => { setProject(data.cartridge); clearDirty(); })
  .catch((error) => {
    console.warn("Project load failed:", error);
    setProject(structuredClone(emptyProject));
    clearDirty();
  });
const entitySchemas = {
  zones: { label: "Zones", singular: "zone", fields: ["id", "name", "description"] },
  items: {
    label: "Items",
    singular: "item",
    fields: ["id", "name", "description", "visible", "active", "enabled", "allow_take", "allow_drop", "allow_use", "allow_give"],
  },
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
  mapLayers: new Map(),
  pointLayers: new Map(),
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
    const isBool = typeof entity[field] === "boolean";
    const input = document.createElement(field === "description" ? "textarea" : "input");
    if (isBool) {
      input.type = "checkbox";
      input.checked = Boolean(entity[field]);
    } else {
      input.value = entity[field] ?? "";
    }
    input.oninput = () => {
      if (field === "id") state.selectedId = input.value.trim();
      if (isBool) {
        entity[field] = input.checked;
      } else {
        entity[field] = field === "value" && entity.var_type === "number" ? Number(input.value || 0) : input.value;
      }
      renderNav();
      renderMap();
    };
    wrapper.innerHTML = `<span>${field}</span>`;
    wrapper.appendChild(input);
    container.appendChild(wrapper);
  }
  if (state.selectedCollection === "zones") {
    entity.extras = entity.extras || {};
    entity.extras.shape_type = entity.extras.shape_type || "circle";
    const shapeField = document.createElement("label");
    const shapeSelect = document.createElement("select");
    shapeSelect.innerHTML = `<option value="circle">Circle</option><option value="polygon">Polygon</option>`;
    shapeSelect.value = entity.extras.shape_type;
    shapeSelect.onchange = () => {
      entity.extras.shape_type = shapeSelect.value;
      if (shapeSelect.value === "polygon") entity.extras.points = entity.extras.points || [];
      renderAll();
    };
    shapeField.innerHTML = "<span>Shape type</span>";
    shapeField.appendChild(shapeSelect);
    container.appendChild(shapeField);
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
    if (entity.extras.shape_type === "polygon") {
      const points = Array.isArray(entity.extras.points) ? entity.extras.points : [];
      const helper = document.createElement("div");
      helper.className = "helper";
      helper.textContent = `Vertices: ${points.length} (click map to append)`;
      container.appendChild(helper);
      const clearBtn = document.createElement("button");
      clearBtn.type = "button";
      clearBtn.className = "secondary";
      clearBtn.textContent = "Clear vertices";
      clearBtn.onclick = () => {
        entity.extras.points = [];
        renderAll();
      };
      container.appendChild(clearBtn);
    }
  }
}

function currentEntity() {
  return state.project[state.selectedCollection].find((entity) => entity.id === state.selectedId) || null;
}

function defaultEntity() {
  const schema = entitySchemas[state.selectedCollection];
  const id = `${schema.singular}-${state.project[state.selectedCollection].length + 1}`;
  const defaultName = {
    zones: "Zone",
    items: "Item",
    characters: "Character",
    tasks: "Task",
    variables: "Variable",
    inputs: "Input",
    media_objects: "Media",
  }[state.selectedCollection] || schema.singular;
  const entity = { id, name: defaultName };
  if (schema.fields.includes("description")) entity.description = "";
  if (state.selectedCollection === "variables") {
    entity.var_type = "string";
    entity.value = "";
  }
  if (state.selectedCollection === "inputs") entity.variable_id = state.project.variables[0]?.id || "";
  if (state.selectedCollection === "media_objects") entity.filename = "";
  if (state.selectedCollection === "zones") entity.extras = { lat: 39.9042, lon: 116.4074, radius_m: 40, shape_type: "circle" };
  if (state.selectedCollection === "items") {
    entity.visible = true;
    entity.active = true;
    entity.enabled = true;
    entity.allow_take = true;
    entity.allow_drop = true;
    entity.allow_use = true;
    entity.allow_give = true;
  }
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
    name: `OnEnter_${state.project.events.length + 1}`,
    object_name: state.project.zones[0]?.name || "",
    event_type: "wig",
    callback_key: 0,
    lua_script: "",
    groups: [],
    extras: { trigger: { kind: "zone_on_enter", zone_name: state.project.zones[0]?.name || "" } },
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
        const shapeType = zone.extras.shape_type || "circle";
        if (shapeType === "polygon") {
          zone.extras.points = zone.extras.points || [];
          zone.extras.points.push([Number(event.latlng.lat.toFixed(6)), Number(event.latlng.lng.toFixed(6))]);
        } else {
          zone.extras.lat = Number(event.latlng.lat.toFixed(6));
          zone.extras.lon = Number(event.latlng.lng.toFixed(6));
        }
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
    for (const layer of state.mapLayers.values()) layer.remove();
    for (const points of state.pointLayers.values()) points.forEach((p) => p.remove());
    state.markers.clear();
    state.mapLayers.clear();
    state.pointLayers.clear();
    const bounds = [];
    for (const zone of state.project.zones) {
      const shapeType = zone.extras?.shape_type || "circle";
      if (shapeType === "polygon") {
        const points = Array.isArray(zone.extras?.points) ? zone.extras.points : [];
        if (points.length >= 1) {
          const poly = L.polygon(points, { color: zone.id === state.selectedId ? "#1565c0" : "#2e7d32" }).addTo(state.map);
          poly.on("click", () => {
            state.selectedCollection = "zones";
            state.selectedId = zone.id;
            renderAll();
          });
          state.mapLayers.set(zone.id, poly);
          points.forEach((pt) => {
            const vertex = L.circleMarker(pt, { radius: 5, color: "#ff9800" }).addTo(state.map);
            state.pointLayers.set(zone.id, [...(state.pointLayers.get(zone.id) || []), vertex]);
            bounds.push([pt[0], pt[1]]);
          });
        }
        continue;
      }
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
      const radius = Number(zone.extras?.radius_m ?? zone.extras?.radius ?? 40);
      const circle = L.circle([lat, lon], { radius, color: zone.id === state.selectedId ? "#1565c0" : "#2e7d32" }).addTo(state.map);
      state.mapLayers.set(zone.id, circle);
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
