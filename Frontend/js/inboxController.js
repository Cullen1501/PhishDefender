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
  const EMAIL_CACHE_KEY = "pd_analysed_emails";
  const EMAIL_CACHE_TIME_KEY = "pd_analysed_emails_cached_at";
  const checkNewEmailsBtn = document.getElementById("checkNewEmailsBtn");
  const newEmailNotice = document.getElementById("newEmailNotice");

  if (!viewer || !listPanel || !phishingList || !legitimateList) return;

  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

    function getCachedEmails() {
    try {
      const raw = sessionStroage.getItem(EMAIL_CACHE_KEY);
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed)? parsed : [];
    } catch (error) {
      console.error("Failed to read cached emails:", error);
      return [];
    }
  }

  function saveCachedEmails(emails) {
    sessionStorage.setItem(EMAIL_CACHE_KEY, JSON.stringify(emails));
    sessionStorage.setItem(EMAIL_CACHE_TIME_KEY, String(Date.now()));
  }

  function getLastestCachedUid(emails) {
    if (!Array.isArray(emails) || !emails.length) return null;

    const withUid = emails
    .map((email) => Number(email.uid))
    .filter((uid) =>  Number.isFinite(uid));

  if (!withUid.lengt) return null;
  return Math.max(...withUid);
  }

  function renderLoadedInbox(emails) {
    renderInboxList(emails);
    renderSortedLists(emails);

    if (emails.length > 0) {
      openEmail(emails[0]);
    } else {
      renderWelcome(auth.getUseranme() || "User");
    }
  }

  function renderWelcome(username = "") {
    viewer.innerHTML = `
      <div class="viewer-placeholder">
        <h3>Welcome${username ? `, ${escapeHtml(username)}` : ""}</h3>
        <p>Select an email from the inbox panel to view it here.</p>
        <hr>
      </div>
    `;
    if (viewerStatus) viewerStatus.textContent = "No Email Selected";
  }

  function setInboxStatus(message) {
    listPanel.innerHTML = `<div class="list-status">${escapeHtml(message)}</div>`;
  }

  function renderLoginPanel(message = "") {
    renderWelcome("");
    setResultPlaceholders();

    listPanel.innerHTML = `
      <div class="login-panel">
        <h3>Login to Gmail</h3>
        <div class="hint">Use your Gmail address and a Google App Password.</div>

        <input id="inlineGmailInput" type="email" placeholder="Your Gmail address" />
        <input id="inlineAppPassInput" type="password" placeholder="Gmail App Password" />

        <div id="inlineLoginError" class="error" style="display:${message ? "block" : "none"};">${escapeHtml(message)}</div>

        <div class="actions">
          <button id="inlineLoginBtn" class="primary" type="button">Login</button>
          <button id="inlineClearBtn" class="secondary" type="button">Clear</button>
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
      renderLoginPanel("");
    });
  }

  function openEmail(emailObj) {
    viewer.innerHTML = `
      <div class="email-view-content">
        <h3>${escapeHtml(emailObj.subject || "(No subject)")}</h3>
        <p><strong>From:</strong> ${escapeHtml(emailObj.from || "")}</p>
        <p><strong>Date:</strong> ${escapeHtml(emailObj.date || "")}</p>
        <p><strong>Prediction:</strong> ${escapeHtml(emailObj.prediction || "unknown")}</p>
        ${typeof emailObj.phishing_confidence === "number" ? `<p><strong>Phishing confidence:</strong> ${(emailObj.phishing_confidence * 100).toFixed(1)}%</p>` : ""}
        ${typeof emailObj.legitimate_confidence === "number" ? `<p><strong>Legitimate confidence:</strong> ${(emailObj.legitimate_confidence * 100).toFixed(1)}%</p>` : ""}
        <hr>
        <div class="email-body">${escapeHtml(emailObj.body || "No email body available.")}</div>
      </div>
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
      <div class="email-item-meta">${escapeHtml(emailObj.from || "")}</div>
      <div class="email-item-date">${escapeHtml(emailObj.date || "")}</div>
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
      <div class="email-item-meta">${escapeHtml(emailObj.from || "")}</div>
      ${typeof emailObj.phishing_confidence === "number" ? `<div class="result-confidence">Phishing: ${(emailObj.phishing_confidence * 100).toFixed(1)}%</div>` : ""}
      ${typeof emailObj.legitimate_confidence === "number" ? `<div class="result-confidence">Legitimate: ${(emailObj.legitimate_confidence * 100).toFixed(1)}%</div>` : ""}
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

    const loginSummary = document.createElement("div");
    loginSummary.className = "login-summary";
    loginSummary.innerHTML = `
      <div>
        <strong>${escapeHtml(Auth.getCreds()?.email || "")}</strong>
        <div class="login-summary-sub">Showing all inbox emails</div>
      </div>
    `;
    listPanel.appendChild(loginSummary);

    if (!emails.length) {
      const emptyState = document.createElement("div");
      emptyState.className = "list-status";
      emptyState.textContent = "Inbox is empty.";
      listPanel.appendChild(emptyState);
      return;
    }

    emails.forEach((item) => listPanel.appendChild(makeInboxRow(item)));
  }

async function loadInbox(options = {}) {
  const { forceRefresh = false } = options;

  const creds = Auth.getCreds();
  if (!creds) {
    renderLoginPanel("");
    return;
  }

  const cachedEmails = getCachedEmails();

  if (!forceRefresh && cachedEmails.length > 0) {
    renderLoadedInbox(cachedEmails);
    return;
  }

  renderWelcome(Auth.getUsername() || "User");
  setInboxStatus("Loading inbox emails and sorting them...");
  setResultPlaceholders();

  try {
    const response = await fetch("http://127.0.0.1:5000/api/emails", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: creds.email,
        appPassword: creds.appPassword,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      Auth.logout();
      renderLoginPanel(data.error || "Login failed. Please try again.");
      return;
    }

    const emails = Array.isArray(data.emails) ? data.emails : [];
    saveCachedEmails(emails);
    renderLoadedInbox(emails);
  } catch (error) {
    console.error(error);
    setInboxStatus("Network error. Make sure the backend is running on port 5000.");
    setResultPlaceholders();
  }
}

async function loadInbox(options = {}) {
  const { forceRefresh = false } = options;

  const creds = Auth.getCreds();
  if (!creds) {
    renderLoginPanel("");
    return;
  }

  const cachedEmails = getCachedEmails();

  if (!forceRefresh && cachedEmails.length > 0) {
    renderLoadedInbox(cachedEmails);
    return;
  }

  renderWelcome(Auth.getUsername() || "User");
  setInboxStatus("Loading inbox emails and sorting them...");
  setResultPlaceholders();

  try {
    const response = await fetch("http://127.0.0.1:5000/api/emails", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        email: creds.email,
        appPassword: creds.appPassword,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      Auth.logout();
      renderLoginPanel(data.error || "Login failed. Please try again.");
      return;
    }

    const emails = Array.isArray(data.emails) ? data.emails : [];
    saveCachedEmails(emails);
    renderLoadedInbox(emails);
  } catch (error) {
    console.error(error);
    setInboxStatus("Network error. Make sure the backend is running on port 5000.");
    setResultPlaceholders();
  }
}

  refreshBtn?.addEventListener("click", () => loadInbox({ forceRefresh: true}));
  checkNewEmailsBtn?.addEventListener("click", checkForNewEmails);

analyseBtn?.addEventListener("click", () => {
  const savedEmails = sessionStorage.getItem("pd_analysed_emails");

  if (!savedEmails) {
    alert("Please analyse the inbox first so there are results to explain.");
    return;
  }

  window.location.href = "explanation.html";
});

  window.loadInbox = loadInbox;
  loadInbox();
});