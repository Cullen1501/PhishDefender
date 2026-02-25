function initHeaderAuth() {
    const btn = document.getElementById("headerAuthBtn");
    const user = document.getElementById("headerUser");

    if (!btn) return;

    if (btn.dataset.bound === "1") return;
    btn.dataset.bound ="1";

    function refreshHeader() {
        if (window.Auth && Auth.isLoggedIn()) {
            if (user) user.textContent = `Welcome, ${Auth.getUsername()}`;
            btn.textContent = "Logout";
        } else {
            if (user) user.textContent = "";
            btn.textContent = "login";
        }
    }

    btn.addEventListener("click", () =>{
        console.log("Header auth button clocked");

        if (Auth.isLoggedIn()) {
            Auth.logout();
            refreshHeader();
        } else {
            Auth.showModal("");
        }
    });

    refreshHeader();
}

document.addEventListener("componentsLoaded", initHeaderAuth);
document.addEventListener("DOMContentLoaded", initHeaderAuth);