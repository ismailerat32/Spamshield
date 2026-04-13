const slices = document.querySelectorAll(".slice");
const coreText = document.getElementById("coreText");

const routes = {
  "Analyze": "/analyze",
  "Blocked": "/blocked",
  "Notifications": "/notifications",
  "Reports": "/reports",
  "Settings": "/settings",
  "Community": "/community",
  "License": "/license",
  "Protection": "/protection"
};

slices.forEach((slice) => {
  slice.addEventListener("click", function () {
    slices.forEach((s) => s.classList.remove("active"));
    this.classList.add("active");

    const label = this.getAttribute("data-label");

    if (!label || !routes[label]) {
      alert("Route bulunamadı: " + label);
      return;
    }

    coreText.textContent = label + " açılıyor...";

    setTimeout(() => {
      window.location.href = routes[label];
    }, 300);
  });
});
