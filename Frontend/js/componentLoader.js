document.addEventListener("DOMContentLoaded", async () => {
  const headerContainer = document.getElementById("headerContainer");
  if (headerContainer) {
    const res = await fetch("components/header.html");
    headerContainer.innerHTML = await res.text();
  }

  const footerContainer = document.getElementById("footerContainer");
  if (footerContainer) {
    const res = await fetch("components/footer.html");
    footerContainer.innerHTML = await res.text();
  }

  document.dispatchEvent(new Event("componentsLoaded"));
});