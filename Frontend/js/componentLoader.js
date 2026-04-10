/*
componentLoader.js

Purpose: 
This file dynamically loads shared UI components (header and footer) into every page so they can be reused instead of duplicated

How it works:
1. Waits for the page to fully load(DOMContentLoaded)
2. Fetches header.html and inserts it into #headerContainer
3. Fetches footer.html and inserts it into #footerContainer
4. Fires a custom event ("componentsLoaded") once done
*/

document.addEventListener("DOMContentLoaded", async () => {
  // Load header component into the page
  const headerContainer = document.getElementById("headerContainer");
  if (headerContainer) {
    try{
      const res = await fetch("components/header.html");
      headerContainer.innerHTML = await res.text();
    } catch (err) {
      console.error("Failed to load header:", err);
    }
  }

  // Load footer components into the page 
  const footerContainer = document.getElementById("footerContainer");
  if (footerContainer) {
    try {
      const res = await fetch("components/footer.html");
      footerContainer.innerHTML = await res.text();
    } catch (err) {
      console.error("Failed to load footer:", err);
    }
  }

    // Notify the rest of the app that components are now available
  document.dispatchEvent(new Event("componentsLoaded"));
});