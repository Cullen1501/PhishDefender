/*
Login modal
sessionStorage credentials
Login state
Logout
Shared access across pages 
*/

const Auth = (function() {

    const KEY_EMAIL = "pd_gmail";
    const KEY_PASS = "pd_app_pass";

    function getCreds () {
        const email = sessionStorage.getItem(KEY_EMAIL);
        const appPassword = sessionStorage.getItem(KEY_PASS);

        if (!email || !appPassword) return null;
        return { email, appPassword };
    }

    function login(email, password) {
        sessionStorage.setItem(KEY_EMAIL, email.trim());
        sessionStorage.setItem(KEY_PASS, password.replaceAll(" ", "").trim());
    }

    function logout() {
        sessionStorage.removeItem(KEY_EMAIL);
        sessionStorage.removeItem(KEY_PASS);
    }

    function isLoggedIn() {
        return !!getCreds();
    }

    function getUsername() {
        const creds = getCreds();
        if(!creds) return null;
        return creds.email.split("@")[0];
    }

    function showModal(message = "") {
        const modal = document.getElementById("loginModal");
        const error = document.getElementById("loginError");

        if (!modal) return;

        if (error) {
            error.textContent = message;
            error.style.display = message ? "block" : "none";
        }

        modal.style.display = "flex";
    }

    function hideModal() {
        const modal = document.getElementById("loginModal");
        if (!modal) return;

        modal.style.display = "none";
    }

    return{
        getCreds,
        login,
        logout,
        isLoggedIn,
        getUsername,
        showModal,
        hideModal
    };
})();