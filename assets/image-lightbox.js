(function () {
  "use strict";

  var selector = "main img:not([data-no-lightbox])";
  var images = [];
  var currentIndex = -1;
  var previousFocus = null;
  var closeTimer = null;

  var style = document.createElement("style");
  style.textContent = [
    "body.site-lightbox-open { overflow: hidden; }",
    ".site-lightbox-trigger { cursor: zoom-in; }",
    ".site-lightbox-trigger:focus-visible { outline: 3px solid #5fd0c8; outline-offset: 4px; }",
    ".site-lightbox[hidden] { display: none; }",
    ".site-lightbox {",
    "  position: fixed; inset: 0; z-index: 2147483000;",
    "  display: grid; grid-template-columns: 72px minmax(0, 1fr) 72px;",
    "  grid-template-rows: 64px minmax(0, 1fr) 56px;",
    "  color: #f5f7fa; background: rgba(4, 8, 15, .94);",
    "  -webkit-backdrop-filter: blur(16px); backdrop-filter: blur(16px);",
    "  opacity: 0; transition: opacity 160ms ease;",
    "}",
    ".site-lightbox.is-open { opacity: 1; }",
    ".site-lightbox-stage {",
    "  grid-column: 2; grid-row: 2; min-width: 0; min-height: 0;",
    "  display: flex; align-items: center; justify-content: center;",
    "}",
    ".site-lightbox-figure {",
    "  margin: 0; max-width: 100%; max-height: 100%;",
    "  display: flex; align-items: center; justify-content: center;",
    "}",
    ".site-lightbox-image {",
    "  display: block; width: auto; height: auto; max-width: 100%;",
    "  max-height: calc(100vh - 136px); object-fit: contain;",
    "  border-radius: 8px; box-shadow: 0 24px 80px rgba(0, 0, 0, .55);",
    "}",
    ".site-lightbox-figure.is-cropped { overflow: hidden; border-radius: 8px; }",
    ".site-lightbox-figure.is-cropped .site-lightbox-image {",
    "  width: 100%; height: 100%; max-height: none; border-radius: 0;",
    "  object-fit: cover; object-position: var(--site-lightbox-position, center);",
    "}",
    ".site-lightbox-button {",
    "  width: 44px; height: 44px; padding: 0; border: 1px solid rgba(255,255,255,.2);",
    "  border-radius: 999px; color: #fff; background: rgba(17, 24, 39, .72);",
    "  font: 24px/1 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;",
    "  cursor: pointer; -webkit-tap-highlight-color: transparent;",
    "  transition: background 120ms ease, border-color 120ms ease, transform 120ms ease;",
    "}",
    ".site-lightbox-button:hover { background: rgba(45, 55, 72, .92); border-color: rgba(255,255,255,.42); }",
    ".site-lightbox-button:active { transform: scale(.94); }",
    ".site-lightbox-button:focus-visible { outline: 3px solid #5fd0c8; outline-offset: 3px; }",
    ".site-lightbox-close { grid-column: 3; grid-row: 1; align-self: center; justify-self: center; }",
    ".site-lightbox-prev { grid-column: 1; grid-row: 2; align-self: center; justify-self: center; }",
    ".site-lightbox-next { grid-column: 3; grid-row: 2; align-self: center; justify-self: center; }",
    ".site-lightbox-caption {",
    "  grid-column: 2; grid-row: 3; align-self: center; justify-self: center;",
    "  max-width: min(920px, 100%); overflow: hidden; text-overflow: ellipsis;",
    "  white-space: nowrap; color: rgba(245,247,250,.78); font: 13px/1.4 -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;",
    "}",
    ".site-lightbox-count { margin-left: 10px; color: rgba(245,247,250,.48); }",
    "@media (max-width: 720px) {",
    "  .site-lightbox { grid-template-columns: 52px minmax(0,1fr) 52px; grid-template-rows: 56px minmax(0,1fr) 52px; }",
    "  .site-lightbox-button { width: 38px; height: 38px; font-size: 21px; }",
    "  .site-lightbox-stage { grid-column: 1 / 4; padding: 0 12px; }",
    "  .site-lightbox-prev, .site-lightbox-next { z-index: 1; }",
    "  .site-lightbox-caption { grid-column: 1 / 4; max-width: calc(100vw - 32px); font-size: 12px; }",
    "  .site-lightbox-image { max-height: calc(100vh - 120px); }",
    "}",
    "@media (prefers-reduced-motion: reduce) { .site-lightbox, .site-lightbox-button { transition: none; } }"
  ].join("\n");
  document.head.appendChild(style);

  var lightbox = document.createElement("div");
  lightbox.className = "site-lightbox";
  lightbox.hidden = true;
  lightbox.setAttribute("role", "dialog");
  lightbox.setAttribute("aria-modal", "true");
  lightbox.setAttribute("aria-label", "图片查看器");
  lightbox.innerHTML = [
    '<button class="site-lightbox-button site-lightbox-close" type="button" aria-label="关闭图片">×</button>',
    '<button class="site-lightbox-button site-lightbox-prev" type="button" aria-label="上一张图片">‹</button>',
    '<div class="site-lightbox-stage">',
    '  <figure class="site-lightbox-figure"><img class="site-lightbox-image" alt="" /></figure>',
    '</div>',
    '<button class="site-lightbox-button site-lightbox-next" type="button" aria-label="下一张图片">›</button>',
    '<div class="site-lightbox-caption" aria-live="polite"><span class="site-lightbox-caption-text"></span><span class="site-lightbox-count"></span></div>'
  ].join("");
  document.body.appendChild(lightbox);

  var stage = lightbox.querySelector(".site-lightbox-stage");
  var figure = lightbox.querySelector(".site-lightbox-figure");
  var viewerImage = lightbox.querySelector(".site-lightbox-image");
  var caption = lightbox.querySelector(".site-lightbox-caption-text");
  var count = lightbox.querySelector(".site-lightbox-count");
  var closeButton = lightbox.querySelector(".site-lightbox-close");
  var prevButton = lightbox.querySelector(".site-lightbox-prev");
  var nextButton = lightbox.querySelector(".site-lightbox-next");

  function imageLabel(image) {
    var figureElement = image.closest("figure");
    var figcaption = figureElement && figureElement.querySelector("figcaption");
    return (figcaption && figcaption.textContent.trim()) || image.alt || "图片";
  }

  function collectImages() {
    images = Array.prototype.filter.call(document.querySelectorAll(selector), function (image) {
      return !image.closest("a[href]");
    });
    images.forEach(function (image) {
      image.classList.add("site-lightbox-trigger");
      if (!image.hasAttribute("tabindex")) image.tabIndex = 0;
      image.setAttribute("role", "button");
      image.setAttribute("aria-label", "放大图片：" + imageLabel(image));
    });
  }

  function parseRatio(value) {
    var parts = value.split("/").map(Number);
    if (parts.length === 2 && parts[0] > 0 && parts[1] > 0) return parts[0] / parts[1];
    var number = Number(value);
    return number > 0 ? number : null;
  }

  function renderImage() {
    var source = images[currentIndex];
    if (!source) return;

    var computed = window.getComputedStyle(source);
    var ratio = parseRatio(computed.aspectRatio);
    var isCropped = computed.objectFit === "cover" && ratio;
    figure.classList.toggle("is-cropped", Boolean(isCropped));
    if (isCropped) {
      var horizontalSpace = window.innerWidth <= 720 ? 24 : 144;
      var verticalSpace = window.innerWidth <= 720 ? 120 : 136;
      var width = Math.min(1280, window.innerWidth - horizontalSpace, (window.innerHeight - verticalSpace) * ratio);
      figure.style.width = Math.max(0, width) + "px";
      figure.style.height = Math.max(0, width / ratio) + "px";
      figure.style.setProperty("--site-lightbox-position", computed.objectPosition);
    } else {
      figure.style.removeProperty("width");
      figure.style.removeProperty("height");
      figure.style.removeProperty("--site-lightbox-position");
    }

    viewerImage.src = source.currentSrc || source.src;
    viewerImage.alt = source.alt || "";
    caption.textContent = imageLabel(source);
    count.textContent = images.length > 1 ? (currentIndex + 1) + " / " + images.length : "";
    prevButton.hidden = images.length < 2;
    nextButton.hidden = images.length < 2;
  }

  function openAt(image) {
    collectImages();
    currentIndex = images.indexOf(image);
    if (currentIndex < 0) return;
    window.clearTimeout(closeTimer);
    previousFocus = document.activeElement;
    renderImage();
    lightbox.hidden = false;
    document.body.classList.add("site-lightbox-open");
    window.requestAnimationFrame(function () {
      lightbox.classList.add("is-open");
      closeButton.focus();
    });
  }

  function close() {
    if (lightbox.hidden) return;
    lightbox.classList.remove("is-open");
    document.body.classList.remove("site-lightbox-open");
    closeTimer = window.setTimeout(function () {
      lightbox.hidden = true;
      viewerImage.removeAttribute("src");
      if (previousFocus && document.contains(previousFocus)) previousFocus.focus();
    }, 160);
  }

  function move(step) {
    if (images.length < 2) return;
    currentIndex = (currentIndex + step + images.length) % images.length;
    renderImage();
  }

  document.addEventListener("click", function (event) {
    var image = event.target.closest && event.target.closest(selector);
    if (!image || image.closest("a[href]")) return;
    event.preventDefault();
    openAt(image);
  });

  document.addEventListener("keydown", function (event) {
    var image = event.target.matches && event.target.matches(selector) ? event.target : null;
    if (lightbox.hidden && image && (event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      openAt(image);
      return;
    }
    if (lightbox.hidden) return;
    if (event.key === "Escape") close();
    else if (event.key === "ArrowLeft") move(-1);
    else if (event.key === "ArrowRight") move(1);
    else if (event.key === "Tab") {
      var controls = [closeButton, prevButton, nextButton].filter(function (button) { return !button.hidden; });
      var position = controls.indexOf(document.activeElement);
      if (event.shiftKey && position <= 0) {
        event.preventDefault();
        controls[controls.length - 1].focus();
      } else if (!event.shiftKey && position === controls.length - 1) {
        event.preventDefault();
        controls[0].focus();
      }
    }
  });

  closeButton.addEventListener("click", close);
  prevButton.addEventListener("click", function () { move(-1); });
  nextButton.addEventListener("click", function () { move(1); });
  lightbox.addEventListener("click", function (event) {
    if (event.target === lightbox || event.target === stage) close();
  });
  window.addEventListener("resize", function () {
    if (!lightbox.hidden) renderImage();
  });

  collectImages();
})();
