(function () {
  function syncLangMenuPosition(w) {
    var mq = window.matchMedia("(max-width: 640px)");
    if (!w.classList.contains("open") || !mq.matches) {
      w.style.removeProperty("--yt-lang-menu-top");
      w.style.removeProperty("--yt-lang-menu-right");
      w.style.removeProperty("--yt-lang-menu-left");
      w.style.removeProperty("--yt-lang-menu-max-h");
      return;
    }
    var btn = w.querySelector(".yt-lang-btn");
    if (!btn) return;
    var r = btn.getBoundingClientRect();
    var gap = 4;
    w.style.setProperty("--yt-lang-menu-top", r.bottom + gap + "px");
    w.style.setProperty("--yt-lang-menu-max-h", Math.max(120, window.innerHeight - r.bottom - gap - 12) + "px");
    if (document.documentElement.getAttribute("dir") === "rtl") {
      w.style.setProperty("--yt-lang-menu-left", r.left + "px");
      w.style.removeProperty("--yt-lang-menu-right");
    } else {
      w.style.setProperty("--yt-lang-menu-right", window.innerWidth - r.right + "px");
      w.style.removeProperty("--yt-lang-menu-left");
    }
  }

  document.querySelectorAll(".yt-lang-wrap").forEach(function (w) {
    var b = w.querySelector(".yt-lang-btn");
    if (!b) return;
    b.addEventListener("click", function (e) {
      e.stopPropagation();
      w.classList.toggle("open");
      syncLangMenuPosition(w);
    });
  });
  document.addEventListener("click", function () {
    document.querySelectorAll(".yt-lang-wrap.open").forEach(function (w) {
      w.classList.remove("open");
      syncLangMenuPosition(w);
    });
  });
  window.addEventListener("resize", function () {
    document.querySelectorAll(".yt-lang-wrap.open").forEach(syncLangMenuPosition);
  });
  window.addEventListener(
    "scroll",
    function () {
      document.querySelectorAll(".yt-lang-wrap.open").forEach(function (w) {
        w.classList.remove("open");
        syncLangMenuPosition(w);
      });
    },
    { passive: true }
  );

  var searchToggle = document.querySelector(".yt-search-toggle");
  var searchInput = document.querySelector(".yt-search input");
  if (searchToggle) {
    searchToggle.addEventListener("click", function () {
      document.body.classList.toggle("search-open");
      if (document.body.classList.contains("search-open") && searchInput) {
        searchInput.focus();
      }
    });
  }

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

  var catBlock = document.querySelector(".yt-nav-cat-block");
  if (catBlock) {
    var catCount = parseInt(catBlock.getAttribute("data-cat-count") || "0", 10);
    var catTh = parseInt(catBlock.getAttribute("data-cat-threshold") || "15", 10);
    if (catCount > catTh) {
      var lsKey = "yt-nav-cat-expanded";
      var forceOpen = catBlock.getAttribute("data-active-in-extra") === "1";
      var stored = localStorage.getItem(lsKey);
      if (forceOpen || stored === "1") {
        catBlock.classList.add("expanded");
      } else {
        catBlock.classList.remove("expanded");
      }
      var catToggle = catBlock.querySelector(".yt-nav-cat-toggle");
      function syncCatAria() {
        if (!catToggle) return;
        catToggle.setAttribute("aria-expanded", catBlock.classList.contains("expanded") ? "true" : "false");
      }
      syncCatAria();
      if (catToggle) {
        catToggle.addEventListener("click", function (e) {
          e.preventDefault();
          catBlock.classList.toggle("expanded");
          localStorage.setItem(lsKey, catBlock.classList.contains("expanded") ? "1" : "0");
          syncCatAria();
        });
      }
    }
  }
})();
