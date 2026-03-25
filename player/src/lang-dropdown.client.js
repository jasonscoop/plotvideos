(function () {
  document.querySelectorAll(".yt-lang-wrap").forEach(function (w) {
    var b = w.querySelector(".yt-lang-btn");
    if (!b) return;
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      w.classList.toggle("open");
    });
  });
  document.addEventListener("click", function () {
    document.querySelectorAll(".yt-lang-wrap.open").forEach(function (w) {
      w.classList.remove("open");
    });
  });
})();
