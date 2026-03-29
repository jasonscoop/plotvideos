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

  var menuBtn = document.querySelector(".yt-menu-btn");
  var overlay = document.querySelector(".yt-sidebar-overlay");
  if (menuBtn) {
    menuBtn.addEventListener("click", function () {
      document.body.classList.toggle("sidebar-open");
    });
  }
  if (overlay) {
    overlay.addEventListener("click", function () {
      document.body.classList.remove("sidebar-open");
    });
  }
})();
