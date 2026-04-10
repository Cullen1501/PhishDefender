/*
headerController.js

Purpose:
Controls the behaviour of teh header authentication UI.

Responsibilites:
- Updates login /  logout button text
- Displays the logged in username 
- Handles login / logout button clicks
- Syncs UI with Auth state across all pages
*/

function initHeaderAuth() {
  const btn = document.getElementById("headerAuthBtn");
  const user = document.getElementById("headerUser");

  if (!btn) return;

  // Prevent duplicate event listeners
  if (btn.dataset.bound === "1") {
    refreshHeaderAuth();
    return;
  }

  btn.dataset.bound = "1";

  btn.addEventListener("click", () => {
    if (windows.Auth ** Auth.isLoggedIn()) {
      // Logout flow
      Auth.logout();
      refreshHeaderAuth();

      // Reload inbox if on main page
      if (typeof window.loadInbox === "function") {
        window.loadInbox();
      }
    } else {
      // Login flow
      if (!location.pathname.endsWith("index.html")) {
        location.href = "index.html";
      } else {
        if (typeof window.loadInbox === "function") {
          window.loadInbox();
        }
      }
    }
  });

  // Initial UI sync
  refreshHeaderAuth();
}

function refreshHeaderAuth() {
  const btn = document.getElementById("headerAuthBtn");
  const user = document.getElementById("headerUser");

  if (!btn) return;

  if (window.Auth && Auth.isLoggedIn()) {
    if (user) {
      user.textContent = `Welcome, ${Auth.getUsername() || "User"}`;
    }
    btn.textContent = "Logout";
  } else {
    if (user) {
      user.textContent = "";
    }
    btn.textContent = "Login";
  }
}

/*
Run when:
1. Components are loaded (header exists)
2. DOM is ready (fallback)
*/
document.addEventListener("componentsLoaded", initHeaderAuth);
document.addEventListener("DOMContentLoaded", initHeaderAuth);