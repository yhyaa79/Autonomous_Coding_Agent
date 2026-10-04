/**
 * Animated ACA mascot in the status bar (blinks, glances, breathes; reacts to pointer when idle).
 */
(() => {
  const REDUCED =
    typeof matchMedia !== "undefined" &&
    matchMedia("(prefers-reduced-motion: reduce)").matches;

  const PROXIMITY_RADIUS_PX = 300;

  const ANIM_CLASS = [
    "is-blinking",
    "is-looking-left",
    "is-looking-right",
    "is-surprised",
    "is-wiggle",
    "is-breathe-once",
    "is-double-blink",
    "is-scan",
    "is-dart",
    "is-sleepy",
    "is-hop",
    "is-shy",
    "is-spark",
    "is-squint",
  ];

  function rand(min, max) {
    return min + Math.random() * (max - min);
  }

  function pick(arr) {
    return arr[Math.floor(Math.random() * arr.length)];
  }

  function init({ barEl, mascotEl, statusEl, onVisibilityChange }) {
    if (!barEl || !mascotEl || !statusEl) return;

    const eyes = mascotEl.querySelector(".status-mascot__eyes");
    let idleTimer = null;
    let lookTimer = null;
    let disposed = false;
    let pointerTracking = false;

    function hasStatusText() {
      return !!statusEl.textContent.trim();
    }

    function syncBarState() {
      const busy = hasStatusText();
      barEl.classList.toggle("status-bar--has-text", busy);
      barEl.classList.toggle("status-bar--idle", !busy);
      if (typeof onVisibilityChange === "function") onVisibilityChange(!busy);
      if (busy) {
        stopIdleLife();
        resetPointerFollow();
        resetEyes();
      } else {
        scheduleIdleLife();
      }
    }

    function clearAnimClasses() {
      mascotEl.classList.remove(...ANIM_CLASS);
    }

    function playAnim(className, ms) {
      clearAnimClasses();
      mascotEl.classList.add(className);
      window.setTimeout(() => mascotEl.classList.remove(className), ms);
    }

    function resetPointerFollow() {
      mascotEl.classList.remove("is-proximity");
      mascotEl.style.setProperty("--prox", "0");
      if (eyes) eyes.style.removeProperty("transform");
    }

    function resetEyes() {
      resetPointerFollow();
      clearAnimClasses();
    }

    function blink() {
      if (hasStatusText() || REDUCED) return;
      playAnim("is-blinking", 240);
    }

    function look(side) {
      if (hasStatusText() || REDUCED) return;
      clearAnimClasses();
      mascotEl.classList.add(side === "left" ? "is-looking-left" : "is-looking-right");
      lookTimer = window.setTimeout(() => {
        mascotEl.classList.remove("is-looking-left", "is-looking-right");
      }, 920);
    }

    function playfulBurst() {
      if (hasStatusText() || REDUCED) return;
      const action = pick([
        "blink",
        "double-blink",
        "look-left",
        "look-right",
        "scan",
        "dart",
        "surprise",
        "wiggle",
        "breathe",
        "sleepy",
        "hop",
        "shy",
        "spark",
        "squint",
        "combo",
      ]);

      if (action === "blink") blink();
      else if (action === "double-blink") playAnim("is-double-blink", 500);
      else if (action === "look-left") look("left");
      else if (action === "look-right") look("right");
      else if (action === "scan") playAnim("is-scan", 1180);
      else if (action === "dart") playAnim("is-dart", 440);
      else if (action === "surprise") playAnim("is-surprised", 620);
      else if (action === "wiggle") playAnim("is-wiggle", 540);
      else if (action === "breathe") playAnim("is-breathe-once", 920);
      else if (action === "sleepy") playAnim("is-sleepy", 1120);
      else if (action === "hop") playAnim("is-hop", 640);
      else if (action === "shy") playAnim("is-shy", 980);
      else if (action === "spark") playAnim("is-spark", 780);
      else if (action === "squint") playAnim("is-squint", 380);
      else if (action === "combo") {
        playAnim("is-hop", 640);
        window.setTimeout(() => {
          if (!hasStatusText()) playAnim("is-double-blink", 500);
        }, 420);
      }
    }

    function scheduleIdleLife() {
      stopIdleLife();
      if (REDUCED) return;
      const delay = rand(1200, 3400);
      idleTimer = window.setTimeout(() => {
        playfulBurst();
        scheduleIdleLife();
      }, delay);
    }

    function stopIdleLife() {
      if (idleTimer) window.clearTimeout(idleTimer);
      idleTimer = null;
      if (lookTimer) window.clearTimeout(lookTimer);
      lookTimer = null;
    }

    function mascotCenter() {
      const rect = mascotEl.getBoundingClientRect();
      return {
        x: rect.left + rect.width / 2,
        y: rect.top + rect.height / 2,
      };
    }

    function onDocumentPointerMove(e) {
      if (hasStatusText() || !eyes || REDUCED) return;

      const { x: cx, y: cy } = mascotCenter();
      const dx = e.clientX - cx;
      const dy = e.clientY - cy;
      const dist = Math.hypot(dx, dy);

      if (dist > PROXIMITY_RADIUS_PX) {
        if (pointerTracking) resetPointerFollow();
        pointerTracking = false;
        return;
      }

      pointerTracking = true;
      const strength = 1 - dist / PROXIMITY_RADIUS_PX;
      const eased = strength * strength;
      mascotEl.style.setProperty("--prox", String(eased));
      mascotEl.classList.add("is-proximity");

      const maxEx = 4.8 * eased;
      const maxEy = 3.4 * eased;
      const nx = dist > 0.5 ? dx / dist : 0;
      const ny = dist > 0.5 ? dy / dist : 0;
      eyes.style.transform = `translate(${nx * maxEx}px, ${ny * maxEy}px)`;
    }

    function onDocumentPointerLeave() {
      pointerTracking = false;
      resetPointerFollow();
    }

    document.addEventListener("pointermove", onDocumentPointerMove, { passive: true });
    document.addEventListener("pointerleave", onDocumentPointerLeave);

    mascotEl.addEventListener("pointerenter", () => {
      if (hasStatusText() || REDUCED) return;
      if (Math.random() < 0.45) blink();
      else playAnim("is-squint", 380);
    });
    mascotEl.addEventListener("click", () => {
      if (hasStatusText() || REDUCED) return;
      playAnim("is-hop", 640);
      window.setTimeout(() => {
        if (!hasStatusText()) playAnim("is-spark", 780);
      }, 280);
    });

    syncBarState();

    return {
      sync: syncBarState,
      dispose() {
        disposed = true;
        stopIdleLife();
        document.removeEventListener("pointermove", onDocumentPointerMove);
        document.removeEventListener("pointerleave", onDocumentPointerLeave);
      },
      get disposed() {
        return disposed;
      },
    };
  }

  window.AcaStatusMascot = { init };
})();
