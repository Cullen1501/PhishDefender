const Auth = (() => {
  const KEY_EMAIL = "pd_gmail";
  const KEY_PASS = "pd_app_pass";

  function getCreds() {
    const email = sessionStorage.getItem(KEY_EMAIL);
    const pass = sessionStorage.getItem(KEY_PASS);
    if (!email || !pass) return null;
    return { email, appPassword: pass };
  }

  function isLoggedIn() {
    return !!getCreds();
  }

  function getUsername() {
    const c = getCreds();
    if (!c) return null;
    return (c.email.split("@")[0] || "").trim() || null;
  }

  function login(email, pass) {
    sessionStorage.setItem(KEY_EMAIL, (email || "").trim());
    sessionStorage.setItem(KEY_PASS, (pass || "").replaceAll(" ", "").trim());
  }

  function logout() {
    sessionStorage.removeItem(KEY_EMAIL);
    sessionStorage.removeItem(KEY_PASS);
  }

  return { getCreds, isLoggedIn, getUsername, login, logout };
})();