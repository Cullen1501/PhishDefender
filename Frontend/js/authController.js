/*
authController.js

This file manages simple frontend authentication state for PhishDefender 

What this file does:
1. Stores Gmail login details in sessionStorage
2. Checks whether the user is currently logged in
3. Returns the logged in username for display in the UI
4. Removes saved login details on logout
*/


const Auth = (() => {
  // Key used to store values in sessionStorage
  const KEY_EMAIL = "pd_gmail";
  const KEY_PASS = "pd_app_pass";

  function getCreds() {
    /* 
    Returns the currently saved credentials from sessionStorage.
    
    Returns:
    - null if either value is missing
    - otherwise an object containing
      { email, appPassword }
    */
    const email = sessionStorage.getItem(KEY_EMAIL);
    const pass = sessionStorage.getItem(KEY_PASS);
    if (!email || !pass) return null;
    return { email, appPassword: pass };
  }

  function isLoggedIn() {
    // Returns true if both email and app password are stored, otherwise returns false
    return !!getCreds();
  }

  function getUsername() {
    // Extracts a display freiendly username from the saved Gmail address
    const c = getCreds();
    if (!c) return null;
    return (c.email.split("@")[0] || "").trim() || null;
  }

  function login(email, pass) {
    // Saves login credentials into sessionStorage
    sessionStorage.setItem(KEY_EMAIL, (email || "").trim());
    sessionStorage.setItem(KEY_PASS, (pass || "").replaceAll(" ", "").trim());
  }

  function logout() {
    // Clears the saved login credentails from sessionStroage
    sessionStorage.removeItem(KEY_EMAIL);
    sessionStorage.removeItem(KEY_PASS);
  }

  return { getCreds, isLoggedIn, getUsername, login, logout };
})();

// Make Auth globally accessible to other scripts 
window.Auth = Auth;