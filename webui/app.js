const entitySchemas = {
  zones: { label: "区域", singular: "zone", fields: ["id", "name", "description"] },
  items: {
    label: "物品",
    singular: "item",
    fields: ["id", "name", "description", "visible", "active", "enabled", "allow_take", "allow_drop", "allow_use", "allow_give"],
  },
  characters: { label: "角色", singular: "character", fields: ["id", "name", "description"] },
  tasks: { label: "任务", singular: "task", fields: ["id", "name", "description"] },
  variables: { label: "变量", singular: "variable", fields: ["id", "name", "var_type", "value"] },
  inputs: { label: "输入", singular: "input", fields: ["id", "name", "variable_id"] },
  media_objects: { label: "媒体", singular: "media_object", fields: ["id", "name", "filename"] },
};

const emptyProject = {
  id: "cart-new",
  name: "新建卡带",
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
  toolbar.innerHTML = `<h2>${schema.label}</h2><button class="filled" type="button">新增${schema.label}</button>`;
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
    shapeSelect.innerHTML = `<option value="circle">圆形</option><option value="polygon">多边形</option>`;
    shapeSelect.value = entity.extras.shape_type;
    shapeSelect.onchange = () => {
      entity.extras.shape_type = shapeSelect.value;
      if (shapeSelect.value === "polygon") entity.extras.points = entity.extras.points || [];
      renderAll();
    };
    shapeField.innerHTML = "<span>区域类型</span>";
    shapeField.appendChild(shapeSelect);
    container.appendChild(shapeField);
    container.appendChild(numberField("纬度", entity.extras.lat ?? 39.9042, (value) => {
      entity.extras.lat = value;
      renderMap();
    }));
    container.appendChild(numberField("经度", entity.extras.lon ?? 116.4074, (value) => {
      entity.extras.lon = value;
      renderMap();
    }));
    container.appendChild(numberField("半径 米", entity.extras.radius_m ?? entity.extras.radius ?? 40, (value) => {
      entity.extras.radius_m = value;
      renderMap();
    }));
    if (entity.extras.shape_type === "polygon") {
      const points = Array.isArray(entity.extras.points) ? entity.extras.points : [];
      const helper = document.createElement("div");
      helper.className = "helper";
      helper.textContent = `顶点数：${points.length}（地图点击可追加顶点）`;
      container.appendChild(helper);
      const clearBtn = document.createElement("button");
      clearBtn.type = "button";
      clearBtn.className = "secondary";
      clearBtn.textContent = "清空顶点";
      clearBtn.onclick = () => {
        entity.extras.points = [];
        renderMap();
        renderFields(container, entity, schema);
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
  const defaultNames = {
    zones: "新区域",
    items: "新物品",
    characters: "新角色",
    tasks: "新任务",
    variables: "新变量",
    inputs: "新输入",
    media_objects: "新媒体",
  };
  const entity = { id, name: defaultNames[state.selectedCollection] || schema.label };
  if (schema.fields.includes("description")) entity.description = "";
  if (state.selectedCollection === "variables") {
    entity.var_type = "string";
    entity.value = "";
  }
  if (state.selectedCollection === "inputs") entity.variable_id = state.project.variables[0]?.id || "";
  if (state.selectedCollection === "media_objects") entity.filename = "";
  if (state.selectedCollection === "zones") entity.extras = { lat: 39.9042, lon: 116.4074, radius_m: 40 };
  if (state.selectedCollection === "zones") entity.extras.shape_type = "circle";
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
    showToast(`已新增${entitySchemas[state.selectedCollection].label}`);
  } catch (error) {
    showToast(`新增失败：${error.message}`);
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
    showToast("删除成功");
  } catch (error) {
    showToast(`删除失败：${error.message}`);
  }
}

function renderEntityForm() {
  $("selectedZoneInfo").textContent = currentEntity()
    ? `当前 ${state.selectedCollection}: ${currentEntity().name || currentEntity().id}`
    : "请选择或新建一个区域。";
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
    const template = event.extras.template || null;
    const card = document.createElement("div");
    card.className = "event-card";
    card.innerHTML = `
      <div class="event-grid">
        <label class="field"><span>名称</span><input data-field="name" value="${escapeAttr(event.name || "")}"></label>
        <label class="field"><span>对象名</span><input data-field="object_name" value="${escapeAttr(event.object_name || "")}"></label>
        <label class="field"><span>类型</span><select data-field="event_type">
          <option value="wig">wig</option><option value="callback">callback</option>
        </select></label>
        <label class="field"><span>回调键</span><input type="number" data-field="callback_key" value="${event.callback_key || 0}"></label>
        <label class="field"><span>编辑模式</span>
          <select data-field="editor_mode">
            <option value="template">模板</option>
            <option value="lua">Lua</option>
          </select>
        </label>
      </div>
      <div class="field full" data-template-panel></div>
      <label class="field"><span>Lua 脚本</span><textarea data-field="lua_script">${escapeHtml(event.lua_script || "")}</textarea></label>
      <button class="text-button danger" data-remove>删除事件</button>
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
          return;
        }
        if (field === "editor_mode") {
          event.extras.editor_mode = input.value;
          if (input.value === "template") event.lua_script = "";
          renderEvents();
          return;
        }
        event[field] = input.value;
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
    name: `事件${state.project.events.length + 1}`,
    object_name: state.project.zones[0]?.name || "",
    event_type: "wig",
    callback_key: 0,
    lua_script: "-- 在这里写 Lua",
    groups: [],
    extras: { editor_mode: "lua", trigger: { kind: "zone_on_enter", zone_name: state.project.zones[0]?.name || "" } },
  });
  renderEvents();
}

function renderEventTemplatePanel(container, event, eventIndex) {
  if (event.extras?.editor_mode !== "template") {
    container.innerHTML = `<span class="helper">当前为 Lua 高级编辑模式。</span>`;
    return;
  }
  const template = event.extras?.template || {};
  const preset = state.presets.find((entry) => entry.id === template.id) || state.presets[0];
  if (!preset) {
    container.innerHTML = `<span class="helper">模板库尚未加载。</span>`;
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
      <label class="field"><span>模板</span>
        <select data-template-id>
          ${state.presets.map((entry) => `<option value="${entry.id}" ${entry.id === preset.id ? "selected" : ""}>${entry.label}</option>`).join("")}
        </select>
      </label>
      <div class="helper full">${escapeHtml(preset.description || "")}</div>
      <div class="helper full">触发器：${escapeHtml(preset.trigger || "自定义")}</div>
      ${fields}
      <button type="button" class="secondary" data-rebuild>按模板重建脚本</button>
    </div>
  `;
  container.querySelector("[data-template-id]").onchange = (e) => {
    const selected = state.presets.find((entry) => entry.id === e.target.value);
    event.extras.template = { id: selected.id, version: selected.version, params: {} };
    renderEvents();
  };
  container.querySelectorAll("[data-param]").forEach((input) => {
    input.oninput = () => {
      event.extras.template = event.extras.template || { id: preset.id, version: preset.version, params: {} };
      event.extras.template.params[input.dataset.param] = input.type === "number" ? Number(input.value || 0) : input.value;
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
      renderEvents();
      showToast("已按模板重建");
    } catch (error) {
      showToast(`模板重建失败：${error.message}`);
    }
  };
}

function renderPresetBuilder() {
  const box = $("presetBuilder");
  if (!box) return;
  if (!state.presets.length) {
    box.innerHTML = `<div class="helper">模板库加载中...</div>`;
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
        <label class="field"><span>事件模板</span>
          <select id="presetSelect">${state.presets.map((entry) => `<option value="${entry.id}" ${entry.id === current.id ? "selected" : ""}>${entry.label}</option>`).join("")}</select>
        </label>
        <div class="helper full">${escapeHtml(current.description || "")}</div>
        ${fields}
        <button class="secondary" type="button" id="createFromPreset">创建模板事件</button>
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
    showToast("模板事件已添加");
  } catch (error) {
    showToast(`创建失败：${error.message}`);
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
        attribution: "&copy; OpenStreetMap 贡献者",
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
      $("map").textContent = "Leaflet 未加载；请在分区字段中直接编辑 WGS84 坐标。";
    }
  } catch (error) {
    $("map").textContent = "地图初始化失败；请在分区字段中直接编辑 WGS84 坐标。";
    console.warn("地图初始化失败:", error);
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
            const vertex = L.circleMarker(pt, { radius: 5, color: "#ff9800" }).addTo(state.map);
            vertex.on("click", () => {
              state.selectedCollection = "zones";
              state.selectedId = zone.id;
              renderAll();
            });
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
      marker.bindPopup(`<strong>${escapeHtml(zone.name || zone.id)}</strong><br>WGS84：${lat.toFixed(6)}, ${lon.toFixed(6)}`);
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
      const radius = Number(zone.extras?.radius_m ?? 40);
      const circle = L.circle([lat, lon], { radius, color: zone.id === state.selectedId ? "#1565c0" : "#2e7d32" }).addTo(state.map);
      state.mapLayers.set(zone.id, circle);
      bounds.push([lat, lon]);
    }
    if (bounds.length) state.map.fitBounds(bounds, { padding: [40, 40], maxZoom: 14 });
  } catch (error) {
    console.warn("地图渲染失败:", error);
  }
}

async function validateProject() {
  saveMeta();
  state.project.author_scripts = $("authorScripts").value;
  try {
    const data = await api("/api/project", { method: "POST", body: JSON.stringify(projectPayload()) });
    $("statusLog").textContent = JSON.stringify(data.validation, null, 2);
    showToast(data.validation.valid ? "项目校验通过" : "项目存在错误");
  } catch (error) {
    $("statusLog").textContent = error.message;
    showToast("校验失败");
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
  showToast("Lua 已导出");
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
  $("statusLog").innerHTML = `构建完成\n${links}`;
  showToast("构建完成");
}

function exportJson() {
  saveMeta();
  state.project.author_scripts = $("authorScripts").value;
  downloadText(`${slug(state.project.name)}.wigi.json`, JSON.stringify(state.project, null, 2), "application/json");
  showToast("JSON 已下载");
}

function importJson(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = () => {
    try {
      setProject(JSON.parse(reader.result));
      showToast("项目导入成功");
    } catch (error) {
      showToast(`导入失败：${error.message}`);
    }
  };
  reader.readAsText(file);
}

function newProject() {
  setProject(structuredClone(emptyProject));
  showToast("已创建新项目");
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
  $("addEventFromTemplate").onclick = createEventFromPreset;
  $("projectId").oninput = saveMeta;
  $("projectName").oninput = saveMeta;
  $("projectFile").oninput = saveMeta;
  $("authorScripts").oninput = () => { state.project.author_scripts = $("authorScripts").value; };
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
// Load project from server on startup
fetch("/api/project")
  .then(res => res.json())
  .then(data => setProject(data.cartridge))
  .catch((error) => {
    console.warn("项目加载失败:", error);
    setProject(structuredClone(emptyProject));
  });
