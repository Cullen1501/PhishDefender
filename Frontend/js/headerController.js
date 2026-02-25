function initHeaderAuth() {
  const btn = document.getElementById("headerAuthBtn");
  const user = document.getElementById("headerUser");
  if (!btn) return;

  if (btn.dataset.bound === "1") return;
  btn.dataset.bound = "1";

  function refresh() {
    if (Auth.isLoggedIn()) {
      if (user) user.textContent = `Welcome, ${Auth.getUsername() || "User"}`;
      btn.textContent = "Logout";
    } else {
      if (user) user.textContent = "";
      btn.textContent = "Login";
    }
  }

  btn.addEventListener("click", () => {
    if (Auth.isLoggedIn()) {
      Auth.logout();
      refresh();

      // If you are on upload page, reload state
      if (typeof window.loadInbox === "function") window.loadInbox();
    } else {
      // No popup anymore — send them to Analyse page to login in-panel
      if (!location.pathname.endsWith("upload.html")) {
        location.href = "upload.html";
      } else {
        // already on upload, show panel by reloading inbox state
        if (typeof window.loadInbox === "function") window.loadInbox();
      }
    }
  });

  refresh();
}

document.addEventListener("componentsLoaded", initHeaderAuth);
document.addEventListener("DOMContentLoaded", initHeaderAuth);