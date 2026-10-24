// The editing room (editor/suite/index.html) was written for the claude.ai Artifact runtime. On the Mac it is
// served by editor/app/server.py, and this file gives it the same three things, kept in the episode folder:
// db (edits and requests), assets (voice notes) and user (the owner).
(function () {
  const ep = document.currentScript.dataset.ep;
  const api = (p) => `/api/db/${ep}${p}`;
  const ok = (r) => (r.ok ? r.json() : Promise.reject(new Error("http " + r.status)));
  const send = (method, path, data) =>
    fetch(api(`/doc?path=${encodeURIComponent(path)}`), {
      method, headers: {"Content-Type": "application/json"}, body: data === undefined ? undefined : JSON.stringify(data),
    }).then(ok);
  const list = (col) => fetch(api(`/list?path=${encodeURIComponent(col)}`)).then(ok);

  function doc(path) {
    return {
      id: path.split("/").pop(),
      path,
      get: () => fetch(api(`/doc?path=${encodeURIComponent(path)}`)).then(ok)
        .then((d) => ({id: path.split("/").pop(), exists: d !== null, data: () => d})),
      set: (data) => send("PUT", path, data),
      update: (data) => send("PATCH", path, data),
      delete: () => send("DELETE", path),
    };
  }
  function snap(rows) {
    return {docs: rows.map((r) => ({id: r.id, exists: true, data: () => r.data})), size: rows.length, empty: !rows.length};
  }
  function collection(name) {
    return {
      doc: (id) => doc(`${name}/${id}`),
      add: (data) => fetch(api(`/add?col=${encodeURIComponent(name)}`), {
        method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify(data),
      }).then(ok).then((r) => doc(r.path)),
      get: () => list(name).then(snap),
      onSnapshot(fn, onErr) {
        let last = null, stop = false;
        const tick = async () => {
          if (stop) return;
          try {
            const rows = await list(name), key = JSON.stringify(rows);
            if (key !== last) { last = key; fn(snap(rows)); }
          } catch (e) { if (onErr) onErr(e); }
          setTimeout(tick, 1500);
        };
        tick();
        return () => { stop = true; };
      },
    };
  }
  const names = {owner: "صاحب القناة", claude: "كلود"};
  const caps = {
    db: {doc, collection},
    assets: {
      upload: (blob) => fetch(api(`/asset?type=${encodeURIComponent(blob.type || "")}`), {method: "PUT", body: blob}).then(ok),
    },
    user: {
      id: async () => "owner",
      me: async () => ({id: "owner", name: names.owner}),
      profiles: async (ids) => Object.fromEntries(ids.map((i) => [i, {id: i, name: names[i] || ""}])),
      isOwner: () => true, canEdit: () => true, can: () => true,
    },
  };
  window.claude = {use: async (n) => caps[n] || null};
})();
