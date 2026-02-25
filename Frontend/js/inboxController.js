document.addEventListener("componentsLoaded", () => {
  console.log("Inbox controller loaded");

  const viewer = document.querySelector(".viewer");
  const listPanel = document.querySelector(".list");
  const analyseBtn = document.querySelector(".analyse-btn");
  const metaMsg = document.getElementById("noSelectionMsg");

  if (!viewer || !listPanel || !analyseBtn || !metaMsg) return;


  const newMailBar = document.createElement("div");
  newMailBar.style.display = "none";
  newMailBar.style.padding = "10px 12px";
  newMailBar.style.marginBottom = "10px";
  newMailBar.style.border = "1px solid rgba(255,255,255,0.18)";
  newMailBar.style.borderRadius = "10px";
  newMailBar.style.background = "rgba(56,189,248,0.10)";
  newMailBar.style.cursor = "pointer";
  newMailBar.style.userSelect = "none";

  const newMailBtn = document.createElement("div");
  newMailBtn.textContent = "New emails — Click to refresh";
  newMailBtn.style.fontWeight = "700";
  newMailBar.appendChild(newMailBtn);

  listPanel.parentNode.insertBefore(newMailBar, listPanel);

  
  let selectedEmailKey = null; 
  let lastKnownKeys = new Set();  
  let pendingNewCount = 0;
  let checking = false;

  function renderWelcome(username) {
    viewer.innerHTML = `
      <div class="viewer-placeholder">
        <h3>Welcome${username ? `, ${username}` : ""}</h3>
        <p style="opacity:0.7;">Select an email from the list to view it here.</p>
        <hr>
      </div>
    `;
  }

  function setListStatus(text) {
    listPanel.innerHTML = `<div style="opacity:0.75; padding:12px;">${text}</div>`;
  }

  function hideNewMailBar() {
    pendingNewCount = 0;
    newMailBar.style.display = "none";
  }

  function showNewMailBar(count) {
    pendingNewCount = count;
    newMailBtn.textContent = `New email${count === 1 ? "" : "s"} (${count}) — Click to refresh`;
    newMailBar.style.display = "block";
  }

  function getEmailKey(e) {
    const id = e.id || e.uid || e.messageId || e.message_id || e._id;
    if (id) return String(id);

    const s = (e.subject || "").trim();
    const f = (e.from || "").trim();
    const d = (e.date || "").trim();
    return `${s}|||${f}|||${d}`;
  }

  function renderLoginPanel(message = "") {
    hideNewMailBar();
    listPanel.innerHTML = `
      <div class="login-panel">
        <h3>Login to Gmail</h3>
        <div class="hint">Use your Gmail & App Password (not your normal password).</div>

        <input id="inlineGmailInput" type="email" placeholder="Your Gmail address" />
        <input id="inlineAppPassInput" type="password" placeholder="Gmail App Password" />

        <div id="inlineLoginError" class="error">${message || ""}</div>

        <div class="actions">
          <button id="inlineLoginBtn" class="primary">Login</button>
          <button id="inlineClearBtn" class="secondary">Clear</button>
        </div>
      </div>
    `;

    const err = document.getElementById("inlineLoginError");
    if (err) err.style.display = message ? "block" : "none";

    const loginBtn = document.getElementById("inlineLoginBtn");
    const clearBtn = document.getElementById("inlineClearBtn");
    const emailInput = document.getElementById("inlineGmailInput");
    const passInput = document.getElementById("inlineAppPassInput");

    if (loginBtn) {
      loginBtn.addEventListener("click", () => {
        const email = (emailInput?.value || "").trim();
        const pass = (passInput?.value || "").trim();

        if (!email || !pass) {
          renderLoginPanel("Please enter both Gmail and App Password.");
          return;
        }

        Auth.login(email, pass);
        loadInbox({ silent: false });
        startNewMailWatcher();
      });
    }

    if (clearBtn) {
      clearBtn.addEventListener("click", () => {
        if (emailInput) emailInput.value = "";
        if (passInput) passInput.value = "";
        renderLoginPanel("");
      });
    }
  }

  function makeEmailRow(emailObj) {
    const item = document.createElement("div");
    item.className = "email-item";
    item.style.padding = "12px";
    item.style.cursor = "pointer";
    item.style.borderBottom = "1px solid rgba(255,255,255,0.1)";

    const key = getEmailKey(emailObj);

    item.innerHTML = `
      <strong>${emailObj.subject || "(No subject)"}</strong>
      <div style="font-size:12px; opacity:0.7;">${emailObj.from || ""}</div>
    `;

    item.addEventListener("click", () => {
      selectedEmailKey = key;

      viewer.innerHTML = `
        <h3>${emailObj.subject || "(No subject)"}</h3>
        <p><strong>From:</strong> ${emailObj.from || ""}</p>
        ${emailObj.date ? `<p><strong>Date:</strong> ${emailObj.date}</p>` : ""}
        <hr>
        <div style="white-space:pre-wrap;">${emailObj.body || ""}</div>
      `;
      analyseBtn.disabled = false;
      metaMsg.style.display = "none";
    });

    return item;
  }

  function renderEmailList(emails) {
    listPanel.innerHTML = "";

    if (!emails || emails.length === 0) {
      setListStatus("Inbox is empty.");
      return;
    }

    lastKnownKeys = new Set(emails.map(getEmailKey));

    emails.forEach((emailObj) => {
      listPanel.appendChild(makeEmailRow(emailObj));
    });
  }

  async function loadInbox({ silent } = { silent: false }) {
    const creds = Auth.getCreds();

    if (!creds) {
      renderWelcome("");
      analyseBtn.disabled = true;
      metaMsg.style.display = "block";
      renderLoginPanel("");
      return;
    }

    if (!silent) {
      renderWelcome(Auth.getUsername() || "User");
      analyseBtn.disabled = true;
      metaMsg.style.display = "block";
      setListStatus("Getting Emails...");
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/api/recent-emails", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: creds.email,
          appPassword: creds.appPassword,
          limit: 50,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        Auth.logout();
        renderWelcome("");
        renderLoginPanel(data.error || "Login failed. Please try again.");
        return;
      }

    
      const emails = Array.isArray(data.emails) ? data.emails.slice().reverse() : [];

      renderEmailList(emails);
      hideNewMailBar(); 

    } catch (err) {
      console.error(err);
      if (!silent) {
        setListStatus("Network error. Make sure your backend is running on port 5000.");
      }
    }
  }

  async function checkForNewEmails() {
    if (checking) return;
    checking = true;

    const creds = Auth.getCreds();
    if (!creds) {
      checking = false;
      return;
    }

    try {
      const response = await fetch("http://127.0.0.1:5000/api/recent-emails", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: creds.email,
          appPassword: creds.appPassword,
          limit: 20, 
        }),
      });

      const data = await response.json();
      if (!response.ok) {
        checking = false;
        return;
      }

     
      const incoming = Array.isArray(data.emails) ? data.emails.slice().reverse() : [];

      const incomingKeys = incoming.map(getEmailKey);

      let newCount = 0;
      for (const k of incomingKeys) {
        if (!lastKnownKeys.has(k)) newCount++;
      }

      if (newCount > 0) {
        showNewMailBar(newCount);
      }

    } catch (e) {
    
    } finally {
      checking = false;
    }
  }

  let watcherTimer = null;
  function startNewMailWatcher() {
    if (watcherTimer) return;
    watcherTimer = setInterval(checkForNewEmails, 15000);
  }

  newMailBar.addEventListener("click", () => {
    loadInbox({ silent: true });
  });

  window.loadInbox = () => loadInbox({ silent: false });

  analyseBtn.addEventListener("click", () => {
    alert("Analysis logic will connect here next.");
  });

  loadInbox({ silent: false });

  if (Auth.getCreds()) startNewMailWatcher();
});