/*
explanation.js

Purpose:
Handles rendering of the explanation page, showing why each email was classified as phishing or legitimate.

Key features:
- Loads analysed emails from sessionStorage
- Dynamically bui;ds explanation cards
- Displays LIME and SHAP outputs
- Supports filtering by prediction type
*/

document.addEventListener("componentsLoaded", () => {
  // Main UI elements
  const explanationList = document.getElementById("explanationList");
  const backToInboxBtn = document.getElementById("backToInboxBtn");
  const filterButtons = document.querySelectorAll(".filter-btn");

  // Escapes HTML to prevent injection attacks and broken rendering
  function escapeHtml(value) {
    return String(value || "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#39;");
  }

  // Retrieves analysed emails stored in sessionStorage 
  function getStoredEmails() {
    try {
      const raw = sessionStorage.getItem("pd_analysed_emails");
      if (!raw) return [];
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (error) {
      console.error("Failed to read analysed emails:", error);
      return [];
    }
  }

    // Formats confidence values into percentages
  function percent(value) {
    return typeof value === "number" ? `${(value * 100).toFixed(1)}%` : "N/A";
  }

  // Converts confidence value into width for progress bars
  function widthPercent(value) {
    return typeof value === "number"
      ? `${Math.max(0, Math.min(100, value * 100))}%`
      : "0%";
  }

  // Formats feature weights (used in LIME/SHAP)
  function formatWeight(weight) {
    if (typeof weight !== "number") return "";
    const sign = weight > 0 ? "+" : "";
    return `${sign}${weight.toFixed(4)}`;
  }

  // Renders simple text explanation lists
  function renderTextList(items, type) {
    if (!Array.isArray(items) || items.length === 0) {
      return `<div class="reason-chip ${type}">No details available.</div>`;
    }

    return items
      .map((item) => `<div class="reason-chip ${type}">${escapeHtml(item)}</div>`)
      .join("");
  }

  // Renders feature importance lists (LIME/SHAP)
  function renderFeatureList(features) {
    if (!Array.isArray(features) || features.length === 0) {
        return `<div class="reason-chip neutral">No feature contributions available.</div>`;
    }

    return features
    .map((item) => {
        const feature = item?.feature ?? "Unknown feature";
        const rawWeight = typeof item?.weight === "number"? item.weight : null;
        const weight = formatWeight(rawWeight);

        let chipType = "neutral";
        if (rawWeight !== null) {
            chipType = rawWeight > 0 ? "warning" : rawWeight < 0 ? "safe" : "neutral";
        }

        return `
        <div class="reason-chip ${chipType}">
            <strong>${escapeHtml(feature)}</strong>
            ${weight ? `<span class="feature-weight">${escapeHtml(weight)}</span>` : ""}
            </div>
        `;
    })
    .join("");
  }

  // Creates a full explanation card for a single email
  function createCard(email) {
    const prediction = email.prediction || "unknown";
    const predictionClass =
      prediction === "phishing" ? "is-phishing" : "is-legitimate";

    const article = document.createElement("article");
    article.className = `explanation-card ${predictionClass}`;
    article.dataset.prediction = prediction;

    article.innerHTML = `
      <div class="explanation-card-top">
        <div class="explanation-card-title">
          ${escapeHtml(email.subject || "(No subject)")}
        </div>
        <div class="prediction-badge ${predictionClass}">
          ${escapeHtml(prediction)}
        </div>
      </div>

      <div class="explanation-grid">
        <div class="explanation-panel">
          <h3>Email</h3>
          <div class="email-meta">
            <div><strong>From:</strong> ${escapeHtml(email.from || "Unknown sender")}</div>
            <div><strong>Date:</strong> ${escapeHtml(email.date || "No date available")}</div>
            <div><strong>Trusted sender:</strong> ${email.trusted_sender ? "Yes" : "No"}</div>
          </div>

          <div class="email-body-box">
            ${escapeHtml(email.body || "No email body available.")}
          </div>
        </div>

        <div class="explanation-panel">
          <h3>Why</h3>

          <div class="reason-block">
            <h4>Overall explanation</h4>
            <div class="reason-list">
              ${renderTextList(email.explanation_summary || [], "neutral")}
            </div>
          </div>

          <div class="reason-block">
            <h4>LIME summary</h4>
            <p class="reason-summary">
              ${escapeHtml(email.lime_summary || "No LIME summary available.")}
            </p>
          </div>

          <div class="reason-block">
            <h4>LIME top features</h4>
            <div class="reason-list">
              ${renderFeatureList(email.lime_features || [])}
            </div>
          </div>

          <div class="reason-block">
            <h4>SHAP summary</h4>
            <p class="reason-summary">
              ${escapeHtml(email.shap_summary || "No SHAP summary available.")}
            </p>
          </div>

          <div class="reason-block">
            <h4>SHAP top features</h4>
            <div class="reason-list">
              ${renderFeatureList(email.shap_features || [])}
            </div>
          </div>

          <div class="confidence-row">
            <div class="confidence-item">
              <span>Phishing confidence: ${percent(email.phishing_confidence)}</span>
              <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${widthPercent(email.phishing_confidence)};"></div>
              </div>
            </div>

            <div class="confidence-item">
              <span>Legitimate confidence: ${percent(email.legitimate_confidence)}</span>
              <div class="confidence-bar">
                <div class="confidence-fill" style="width: ${widthPercent(email.legitimate_confidence)};"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    `;

    return article;
  }

  // Renders emails based on selected filter
  function renderEmails(filter = "all") {
    const emails = getStoredEmails();

    if (!emails.length) {
      explanationList.innerHTML = `
        <div class="empty-state">
          No analysed emails available yet. Please go back and load the inbox first.
        </div>
      `;
      return;
    }

    const filteredEmails =
      filter === "all"
        ? emails
        : emails.filter((email) => email.prediction === filter);

    if (!filteredEmails.length) {
      explanationList.innerHTML = `
        <div class="empty-state">
          No emails match this filter.
        </div>
      `;
      return;
    }

    explanationList.innerHTML = "";
    filteredEmails.forEach((email) => {
      explanationList.appendChild(createCard(email));
    });
  }

  // Navigation button back to inbox
  backToInboxBtn?.addEventListener("click", () => {
    window.location.href = "index.html";
  });

  // Filter button logic
  filterButtons.forEach((button) => {
    button.addEventListener("click", () => {
      filterButtons.forEach((btn) => btn.classList.remove("is-active"));
      button.classList.add("is-active");
      renderEmails(button.dataset.filter);
    });
  });

  // Inital render
  renderEmails("all");
});