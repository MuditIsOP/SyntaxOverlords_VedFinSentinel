const output = document.getElementById("output");
const apiBaseInput = document.getElementById("apiBase");

document.querySelectorAll("[data-menu]").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll("[data-section]").forEach((section) => section.classList.add("hidden"));
    document.querySelector(`[data-section="${button.dataset.menu}"]`)?.classList.remove("hidden");
  });
});

document.querySelectorAll("[data-endpoint]").forEach((button) => {
  button.addEventListener("click", async () => {
    const endpoint = button.dataset.endpoint;
    const baseUrl = apiBaseInput.value.trim().replace(/\/$/, "");
    output.textContent = `Loading ${endpoint}...`;
    try {
      const response = await fetch(`${baseUrl}${endpoint}`);
      const payload = await response.json();
      output.textContent = JSON.stringify(payload, null, 2);
    } catch (error) {
      output.textContent = `Request failed: ${error.message}`;
    }
  });
});

document.getElementById("clearOutput").addEventListener("click", () => {
  output.textContent = "Output cleared.";
});
