    /* Inbox + Viewer Logic */

        /* this script:
        Fetches last 50 emails
        Displays subjects in the lsit panel
        Displays selected email in viwer panel
        enables anaylse button when email selected
        */
document.addEventListener("componentsLoaded", () => {
  console.log("Inbox controller loaded");

  const viewer = document.querySelector(".viewer");
  const listPanel = document.querySelector(".list");
  const analyseBtn = document.querySelector(".analyse-btn");
  const metaMsg = document.getElementById("noSelectionMsg");

  if (!viewer || !listPanel || !analyseBtn || !metaMsg) return;

  // ---- Modal elements (NOW they exist, because componentsLoaded fired) ----
  const saveBtn = document.getElementById("saveLoginBtn");
  const cancelBtn = document.getElementById("cancelLoginBtn");
  const gmailInput = document.getElementById("gmailInput");
  const appPassInput = document.getElementById("appPassInput");

  // Wire modal buttons
  if (saveBtn) {
    saveBtn.addEventListener("click", () => {
      const email = (gmailInput?.value || "").trim();
      const pass = (appPassInput?.value || "").trim();

      if (!email || !pass) {
        Auth.showModal("Please enter both Gmail and App Password.");
        return;
      }

      Auth.login(email, pass);
      Auth.hideModal();
      loadInbox();
    });
  }

  if (cancelBtn) {
    cancelBtn.addEventListener("click", () => {
      Auth.hideModal();
    });
  }

  function renderWelcome(username) {
    viewer.innerHTML = `
      <div class="viewer-placeholder">
        <h3>Welcome, ${username}</h3>
        <p style="opacity:0.7;">Select an email from the list to view it here.</p>
        <hr>
      </div>
    `;
  }

  function renderEmailList(emails) {
    listPanel.innerHTML = "";

    if (!emails || emails.length === 0) {
      listPanel.innerHTML = "Inbox is empty.";
      return;
    }

    emails.forEach((emailObj) => {
      const item = document.createElement("div");
      item.className = "email-item";
      item.style.padding = "12px";
      item.style.cursor = "pointer";
      item.style.borderBottom = "1px solid rgba(255,255,255,0.1)";

      item.innerHTML = `
        <strong>${emailObj.subject || "(No subject)"}</strong>
        <div style="font-size:12px; opacity:0.7;">
          ${emailObj.from || ""}
        </div>
      `;

      item.addEventListener("click", () => {
        viewer.innerHTML = `
          <h3>${emailObj.subject || "(No subject)"}</h3>
          <p><strong>From:</strong> ${emailObj.from || ""}</p>
          <hr>
          <div style="white-space:pre-wrap;">${emailObj.body || ""}</div>
        `;
        analyseBtn.disabled = false;
        metaMsg.style.display = "none";
      });

      listPanel.appendChild(item);
    });
  }

  async function loadInbox() {
    const creds = Auth.getCreds();

    if (!creds) {
      listPanel.innerHTML = "Please login to load inbox.";
      renderWelcome("User");
      Auth.showModal("Please login to continue.");
      return;
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
        listPanel.innerHTML = "Login failed. Please try again.";
        renderWelcome("User");
        Auth.showModal(data.error || "Invalid credentials.");
        return;
      }

      renderWelcome(Auth.getUsername());
      renderEmailList(data.emails);

    } catch (err) {
      console.error(err);
      listPanel.innerHTML = "Network error.";
    }
  }

  analyseBtn.addEventListener("click", () => {
    alert("Analysis logic will connect here next.");
  });

  loadInbox();
});