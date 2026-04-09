document.addEventListener("componentsLoaded", () => {
  const viewer = document.querySelector(".viewer");
  const listPanel = document.querySelector(".list");
  const phishingList = document.getElementById("phishingList");
  const legitimateList = document.getElementById("legitimateList");
  const phishingCount = document.getElementById("phishingCount");
  const legitimateCount = document.getElementById("legitimateCount");
  const viewerStatus = document.getElementById("viewerStatus");
  const refreshBtn = document.getElementById("refreshInboxBtn");
  const analyseBtn = document.getElementById("analyseBtn");

  if (!viewer || !listPanel || !phishingList || !legitimateList) return;

  const EMAIL_CACHE_KEY = "pd_analysed_emails";
  const OPEN_EMAIL_KEY = "pd_open_email_uid";

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  function saveEmailsToCache(emails) {
    sessionStorage.setItem(EMAIL_CACHE_KEY, JSON.stringify(emails || []));
  }

  function getCachedEmails() {
    try {
      const raw = sessionStorage.getItem(EMAIL_CACHE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (error) {
      console.error("Failed to read cached emails:", error);
      return [];
    }
  }

  function saveOpenEmail(emailObj) {
    if (!emailObj || !emailObj.uid) return;
    sessionStorage.setItem(OPEN_EMAIL_KEY, String(emailObj.uid));
  }

  function getOpenEmailUid() {
    return sessionStorage.getItem(OPEN_EMAIL_KEY);
  }

  function clearOpenEmail() {
    sessionStorage.removeItem(OPEN_EMAIL_KEY);
  }

  function renderWelcome(username = "") {
    viewer.innerHTML = `
      <h3>Welcome${username ? `, ${escapeHtml(username)}` : ""}</h3>
      <p>Select an email from the inbox panel to view it here.</p>
      <hr />
    `;
    if (viewerStatus) viewerStatus.textContent = "No Email Selected";
  }

  function setInboxStatus(message) {
    listPanel.innerHTML = `
      <div class="list-status">${escapeHtml(message)}</div>
    `;
  }

function renderLoginPanel(message = "") {
  renderWelcome("");
  setResultPlaceholders();

  listPanel.innerHTML = `
    <div class="login-panel">
      <h3>Login to Gmail</h3>
      <p>Use your Gmail address and a Google App Password.</p>
      ${message ? `<p class="error-text">${escapeHtml(message)}</p>` : ""}

      <input 
        id="inlineGmailInput" 
        class="login-input"
        type="email" 
        placeholder="Your Gmail address" 
      />

      <input 
        id="inlineAppPassInput" 
        class="login-input"
        type="password" 
        placeholder="Gmail App Password" 
      />

      <div class="login-panel-actions">
        <button id="inlineLoginBtn" type="button" class="action-btn primary-btn">Login</button>
        <button id="inlineClearBtn" type="button" class="action-btn secondary-btn">Clear</button>
      </div>
    </div>
  `;

  document.getElementById("inlineLoginBtn")?.addEventListener("click", () => {
    const email = (document.getElementById("inlineGmailInput")?.value || "").trim();
    const pass = (document.getElementById("inlineAppPassInput")?.value || "").trim();

    if (!email || !pass) {
      renderLoginPanel("Please enter both Gmail and App Password.");
      return;
    }

    Auth.login(email, pass);
    loadInbox();
  });

  document.getElementById("inlineClearBtn")?.addEventListener("click", () => {
    const emailInput = document.getElementById("inlineGmailInput");
    const passInput = document.getElementById("inlineAppPassInput");

    if (emailInput) emailInput.value = "";
    if (passInput) passInput.value = "";
  });
}

  function openEmail(emailObj) {
    if (!emailObj) return;

    saveOpenEmail(emailObj);

    viewer.innerHTML = `
      <h3>${escapeHtml(emailObj.subject || "(No subject)")}</h3>
      <p><strong>From:</strong> ${escapeHtml(emailObj.from || "")}</p>
      <p><strong>Date:</strong> ${escapeHtml(emailObj.date || "")}</p>
      <p><strong>Prediction:</strong> ${escapeHtml(emailObj.prediction || "unknown")}</p>

      ${
        typeof emailObj.phishing_confidence === "number"
          ? `<p><strong>Phishing confidence:</strong> ${(emailObj.phishing_confidence * 100).toFixed(1)}%</p>`
          : ""
      }

      ${
        typeof emailObj.legitimate_confidence === "number"
          ? `<p><strong>Legitimate confidence:</strong> ${(emailObj.legitimate_confidence * 100).toFixed(1)}%</p>`
          : ""
      }

      <hr />
      <p>${escapeHtml(emailObj.body || "No email body available.").replace(/\n/g, "<br>")}</p>
    `;

    if (viewerStatus) {
      viewerStatus.textContent =
        emailObj.prediction === "phishing"
          ? "Viewing possible phishing email"
          : "Viewing possible legitimate email";
    }
  }

  function makeInboxRow(emailObj) {
    const item = document.createElement("button");
    item.type = "button";
    item.className = `email-item ${emailObj.prediction === "phishing" ? "is-phishing" : "is-legitimate"}`;

    item.innerHTML = `
      <strong>${escapeHtml(emailObj.subject || "(No subject)")}</strong>
      <span>${escapeHtml(emailObj.from || "")}</span>
      <small>${escapeHtml(emailObj.date || "")}</small>
    `;

    item.addEventListener("click", () => openEmail(emailObj));
    return item;
  }

  function makeResultRow(emailObj) {
    const row = document.createElement("button");
    row.type = "button";
    row.className = `result-item ${emailObj.prediction === "phishing" ? "is-phishing" : "is-legitimate"}`;

    row.innerHTML = `
      <strong>${escapeHtml(emailObj.subject || "(No subject)")}</strong>
      <span>${escapeHtml(emailObj.from || "")}</span>
      ${
        typeof emailObj.phishing_confidence === "number"
          ? `<small>Phishing: ${(emailObj.phishing_confidence * 100).toFixed(1)}%</small>`
          : ""
      }
      ${
        typeof emailObj.legitimate_confidence === "number"
          ? `<small>Legitimate: ${(emailObj.legitimate_confidence * 100).toFixed(1)}%</small>`
          : ""
      }
    `;

    row.addEventListener("click", () => openEmail(emailObj));
    return row;
  }

  function setResultPlaceholders() {
    phishingList.innerHTML = `<div class="result-placeholder">Emails predicted as phishing will appear here.</div>`;
    legitimateList.innerHTML = `<div class="result-placeholder">Emails predicted as legitimate will appear here.</div>`;

    if (phishingCount) phishingCount.textContent = "0";
    if (legitimateCount) legitimateCount.textContent = "0";
  }

  function renderSortedLists(emails) {
    const phishingEmails = emails.filter((item) => item.prediction === "phishing");
    const legitimateEmails = emails.filter((item) => item.prediction === "legitimate");

    phishingList.innerHTML = "";
    legitimateList.innerHTML = "";

    if (phishingEmails.length === 0) {
      phishingList.innerHTML = `<div class="result-placeholder">No emails are currently flagged as phishing.</div>`;
    } else {
      phishingEmails.forEach((item) => phishingList.appendChild(makeResultRow(item)));
    }

    if (legitimateEmails.length === 0) {
      legitimateList.innerHTML = `<div class="result-placeholder">No emails are currently flagged as legitimate.</div>`;
    } else {
      legitimateEmails.forEach((item) => legitimateList.appendChild(makeResultRow(item)));
    }

    if (phishingCount) phishingCount.textContent = String(phishingEmails.length);
    if (legitimateCount) legitimateCount.textContent = String(legitimateEmails.length);
  }

  function renderInboxList(emails) {
    listPanel.innerHTML = "";

    if (!emails.length) {
      const emptyState = document.createElement("div");
      emptyState.className = "list-status";
      emptyState.textContent = "Inbox is empty.";
      listPanel.appendChild(emptyState);
      return;
    }

    emails.forEach((item) => listPanel.appendChild(makeInboxRow(item)));
  }

  function renderCachedInbox() {
    const creds = Auth.getCreds();
    if (!creds) {
      renderLoginPanel("");
      return;
    }

    const cachedEmails = getCachedEmails();

    renderWelcome(Auth.getUsername() || "User");

    if (!cachedEmails.length) {
      setInboxStatus("No saved inbox yet. Press Refresh Inbox to load and classify emails.");
      setResultPlaceholders();
      clearOpenEmail();
      return;
    }

    renderInboxList(cachedEmails);
    renderSortedLists(cachedEmails);

    const savedUid = getOpenEmailUid();
    const savedEmail = cachedEmails.find((email) => String(email.uid) === String(savedUid));

    if (savedEmail) {
      openEmail(savedEmail);
    } else {
      openEmail(cachedEmails[0]);
    }
  }

  async function loadInbox() {
    const creds = Auth.getCreds();

    if (!creds) {
      renderLoginPanel("");
      return;
    }

    renderWelcome(Auth.getUsername() || "User");
    setInboxStatus("Loading all inbox emails and sorting them...");
    setResultPlaceholders();

    try {
      const response = await fetch("http://127.0.0.1:5000/api/emails", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({
          email: creds.email,
          appPassword: creds.appPassword
        })
      });

      const data = await response.json();

      if (!response.ok) {
        Auth.logout();
        sessionStorage.removeItem(EMAIL_CACHE_KEY);
        clearOpenEmail();
        renderLoginPanel(data.error || "Login failed. Please try again.");
        return;
      }

      const emails = Array.isArray(data.emails) ? data.emails : [];

      saveEmailsToCache(emails);
      renderInboxList(emails);
      renderSortedLists(emails);

      if (emails.length > 0) {
        openEmail(emails[0]);
      } else {
        clearOpenEmail();
        renderWelcome(Auth.getUsername() || "User");
      }
    } catch (error) {
      console.error(error);
      setInboxStatus("Network error. Make sure the backend is running on port 5000.");
      setResultPlaceholders();
    }
  }

  refreshBtn?.addEventListener("click", loadInbox);

  analyseBtn?.addEventListener("click", () => {
    const savedEmails = sessionStorage.getItem("pd_analysed_emails");
    
    if (!savedEmails) {
      alert("Please refresh the inbox first so there are analysed emails to view.");
      return;
    }

    window.location.href = "explanation.html";
  })

  window.loadInbox = loadInbox;

  // IMPORTANT:
  // Do NOT auto-load from backend here.
  // Just restore the previously classified inbox from sessionStorage.
  renderCachedInbox();
});