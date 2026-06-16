(function () {
  const ENDPOINT = "https://script.google.com/macros/s/AKfycbzgCfWG6Qm04B-NBUc1a_z-KoRNkMlzEMnxqPKC2vIbi7d8wmz7Z_i-ycqXhDFYqBHeiQ/exec";
  const STORAGE_KEY = "robot-learning-feedback-drafts";
  const CLIENT_KEY = "robot-learning-feedback-client";
  const MAX_SELECTION = 2000;

  function onReady(fn) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", fn, { once: true });
    } else {
      fn();
    }
  }

  function getClientId() {
    try {
      const existing = localStorage.getItem(CLIENT_KEY);
      if (existing) return existing;
      const id = crypto && crypto.randomUUID ? crypto.randomUUID() : String(Date.now()) + "-" + Math.random().toString(16).slice(2);
      localStorage.setItem(CLIENT_KEY, id);
      return id;
    } catch (e) {
      return "anonymous";
    }
  }

  function nodePath(node) {
    const parts = [];
    let current = node && (node.nodeType === Node.TEXT_NODE ? node.parentElement : node);
    while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.body) {
      const tag = current.tagName.toLowerCase();
      const id = current.id ? "#" + current.id : "";
      let index = 1;
      let sibling = current;
      while ((sibling = sibling.previousElementSibling)) {
        if (sibling.tagName === current.tagName) index += 1;
      }
      parts.unshift(tag + id + ":nth-of-type(" + index + ")");
      current = current.parentElement;
    }
    return parts.join(" > ");
  }

  function elementFromNode(node) {
    if (!node) return null;
    return node.nodeType === Node.TEXT_NODE ? node.parentElement : node;
  }

  function selectionMeta() {
    const selection = window.getSelection && window.getSelection();
    if (!selection || selection.rangeCount === 0 || !selection.toString().trim()) return null;
    const range = selection.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    const anchorElement = elementFromNode(selection.anchorNode);
    const focusElement = elementFromNode(selection.focusNode);
    return {
      text: selection.toString().trim().slice(0, MAX_SELECTION),
      anchorPath: nodePath(selection.anchorNode),
      focusPath: nodePath(selection.focusNode),
      anchorOffset: selection.anchorOffset,
      focusOffset: selection.focusOffset,
      inFeedbackWidget: !!(
        (anchorElement && anchorElement.closest(".feedback-widget")) ||
        (focusElement && focusElement.closest(".feedback-widget"))
      ),
      rect: {
        x: Math.round(rect.x),
        y: Math.round(rect.y),
        width: Math.round(rect.width),
        height: Math.round(rect.height)
      }
    };
  }

  function cleanSelection(meta) {
    if (!meta) return null;
    return {
      text: meta.text,
      anchorPath: meta.anchorPath,
      focusPath: meta.focusPath,
      anchorOffset: meta.anchorOffset,
      focusOffset: meta.focusOffset,
      rect: meta.rect
    };
  }

  function closestHeading() {
    const headings = Array.from(document.querySelectorAll("h1, h2, h3"));
    const currentY = window.scrollY + 96;
    let best = null;
    for (const heading of headings) {
      if (heading.getBoundingClientRect().top + window.scrollY <= currentY) best = heading;
    }
    return best ? best.textContent.trim().slice(0, 160) : "";
  }

  function payloadFrom(message, email, pageType, website, capturedSelection) {
    return {
      message: message.trim(),
      email: email.trim(),
      website: website.trim(),
      page: {
        url: location.href,
        path: location.pathname + location.search + location.hash,
        title: document.title,
        heading: closestHeading(),
        type: pageType
      },
      selection: capturedSelection || selectionMeta(),
      browser: {
        language: navigator.language,
        userAgent: navigator.userAgent,
        viewport: window.innerWidth + "x" + window.innerHeight,
        scrollY: Math.round(window.scrollY)
      },
      clientId: getClientId(),
      createdAt: new Date().toISOString()
    };
  }

  function saveMock(payload) {
    window.__RL_FEEDBACK_LAST_PAYLOAD__ = payload;
    let debugNode = document.getElementById("feedback-debug-payload");
    if (!debugNode) {
      debugNode = document.createElement("script");
      debugNode.type = "application/json";
      debugNode.id = "feedback-debug-payload";
      document.body.appendChild(debugNode);
    }
    debugNode.textContent = JSON.stringify(payload);
    try {
      const prev = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
      prev.push(payload);
      localStorage.setItem(STORAGE_KEY, JSON.stringify(prev.slice(-20)));
    } catch (e) {
      // Local mock storage is best-effort only.
    }
    console.info("[Robot Learning feedback mock]", payload);
  }

  async function submitFeedback(payload) {
    if (!ENDPOINT) {
      saveMock(payload);
      return { mock: true };
    }
    await fetch(ENDPOINT, {
      method: "POST",
      mode: "no-cors",
      body: JSON.stringify(payload)
    });
    return { mock: false };
  }

  function buildWidget() {
    const root = document.createElement("div");
    root.className = "feedback-widget";
    root.innerHTML = [
      '<button class="feedback-fab" type="button" aria-label="오타 또는 문제 신고" title="오타 또는 문제 신고">!</button>',
      '<section class="feedback-panel" aria-hidden="true">',
      '  <div class="feedback-head">',
      '    <strong>문제 신고</strong>',
      '    <button class="feedback-close" type="button" aria-label="닫기">×</button>',
      '  </div>',
      '  <p class="feedback-guide">문제 부분을 드래그한 뒤 신고하면 선택한 텍스트와 페이지 정보가 함께 접수됩니다.</p>',
      '  <div class="feedback-selection" data-empty="true">',
      '    <span class="feedback-selection-label">선택한 내용</span>',
      '    <p class="feedback-selection-text">드래그한 텍스트가 여기에 표시됩니다.</p>',
      '  </div>',
      '  <form class="feedback-form">',
      '    <input class="feedback-hidden" name="website" tabindex="-1" autocomplete="off" />',
      '    <label>내용<textarea name="message" rows="5" placeholder="오타, 번역 오류, 링크 문제 등을 적어주세요." required></textarea></label>',
      '    <label>이메일 선택 입력<input name="email" type="email" placeholder="답변이 필요하면 입력" /></label>',
      '    <div class="feedback-actions">',
      '      <span class="feedback-status">로컬 테스트 모드</span>',
      '      <button type="submit">등록</button>',
      '    </div>',
      '  </form>',
      '</section>'
    ].join("");
    document.body.appendChild(root);

    const fab = root.querySelector(".feedback-fab");
    const panel = root.querySelector(".feedback-panel");
    const close = root.querySelector(".feedback-close");
    const form = root.querySelector(".feedback-form");
    const textarea = form.elements.message;
    const email = form.elements.email;
    const website = form.elements.website;
    const status = root.querySelector(".feedback-status");
    const selectionBox = root.querySelector(".feedback-selection");
    const selectionText = root.querySelector(".feedback-selection-text");
    const pageType = document.body.className || "page";
    let capturedSelection = null;
    let lastSelection = null;

    function rememberSelection() {
      const meta = selectionMeta();
      if (!meta || !meta.text || meta.inFeedbackWidget) return false;
      lastSelection = cleanSelection(meta);
      root.classList.add("has-selection");
      fab.setAttribute("title", "선택한 텍스트와 함께 신고");
      return true;
    }

    function rememberSelectionSoon() {
      rememberSelection();
      window.setTimeout(rememberSelection, 0);
      window.setTimeout(rememberSelection, 80);
      window.setTimeout(rememberSelection, 180);
    }

    function renderSelection(selection) {
      if (selection && selection.text) {
        selectionBox.dataset.empty = "false";
        selectionText.textContent = selection.text.slice(0, 420);
      } else {
        selectionBox.dataset.empty = "true";
        selectionText.textContent = "드래그한 텍스트가 여기에 표시됩니다.";
      }
    }

    document.addEventListener("selectionchange", rememberSelectionSoon);
    document.addEventListener("mouseup", rememberSelectionSoon);
    document.addEventListener("pointerup", rememberSelectionSoon);
    document.addEventListener("touchend", rememberSelectionSoon);
    document.addEventListener("keyup", rememberSelectionSoon);
    window.setInterval(rememberSelection, 600);

    function openPanel() {
      rememberSelection();
      const currentSelection = selectionMeta();
      const selectionSource = currentSelection && !currentSelection.inFeedbackWidget
        ? cleanSelection(currentSelection)
        : lastSelection;
      capturedSelection = selectionSource || null;
      renderSelection(capturedSelection);
      root.classList.add("open");
      panel.setAttribute("aria-hidden", "false");
      status.textContent = capturedSelection && capturedSelection.text
        ? "선택한 텍스트도 함께 접수됩니다"
        : (ENDPOINT ? "GitHub issue로 등록됩니다" : "로컬 테스트 모드");
      setTimeout(() => textarea.focus(), 0);
    }

    function closePanel() {
      root.classList.remove("open");
      panel.setAttribute("aria-hidden", "true");
    }

    fab.addEventListener("pointerdown", rememberSelection);
    fab.addEventListener("mousedown", rememberSelection);
    fab.addEventListener("click", () => {
      if (root.classList.contains("open")) closePanel();
      else openPanel();
    });
    close.addEventListener("click", closePanel);
    document.addEventListener("keydown", (event) => {
      if (event.key === "Escape" && root.classList.contains("open")) closePanel();
    });

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = textarea.value;
      if (website.value) {
        closePanel();
        return;
      }
      if (message.trim().length < 2) {
        status.textContent = "내용을 조금 더 적어주세요";
        return;
      }

      const submit = form.querySelector('button[type="submit"]');
      submit.disabled = true;
      status.textContent = "등록 중...";
      try {
        const payload = payloadFrom(message, email.value, pageType, website.value, capturedSelection);
        const result = await submitFeedback(payload);
        status.textContent = result.mock ? "로컬에 저장했습니다" : "접수했습니다";
        textarea.value = "";
        email.value = "";
        setTimeout(closePanel, 900);
      } catch (error) {
        status.textContent = "전송 실패. 잠시 후 다시 시도해주세요.";
      } finally {
        submit.disabled = false;
      }
    });
  }

  onReady(buildWidget);
})();
