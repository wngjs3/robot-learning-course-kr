// 강의 재생 페이지: 유튜브 임베드 + 시간 동기화 한국어 해설/자막
(function () {
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const fmt = (s) => {
    s = Math.max(0, Math.floor(s));
    const h = Math.floor(s / 3600), m = Math.floor((s % 3600) / 60), sec = s % 60;
    return (h ? h + ":" + String(m).padStart(2, "0") : m) + ":" + String(sec).padStart(2, "0");
  };

  const params = new URLSearchParams(location.search);
  const id = params.get("id") || "lec01";
  const meta = VIDEO_INDEX[id];
  if (!meta) {
    document.getElementById("lec-title").textContent = "강의를 찾을 수 없습니다";
    return;
  }
  const week = meta.week;
  const isGuest = meta.type === "guest";
  const videoId = isGuest ? week.guest.video : week.video;

  // ----- 헤더 / 메타 -----
  const titleKo = isGuest ? `게스트 강연 — ${week.guest.name}` : `${week.week}주차 · ${week.title_ko}`;
  const subEn = isGuest ? `${week.guest.affil} · Week ${week.week} Guest Spotlight` : week.title_en;
  document.getElementById("lec-title").innerHTML = `${esc(titleKo)}<span class="en" id="lec-title-en">${esc(subEn)}</span>`;
  document.getElementById("crumb-here").textContent = titleKo;
  document.title = `${titleKo} — Robot Learning`;

  const metaRow = document.getElementById("lec-meta-row");
  const metaChips = [];
  metaChips.push(`<a class="chip" href="https://www.youtube.com/watch?v=${videoId}" target="_blank" rel="noopener">유튜브 원본 보기 ↗</a>`);
  if (!isGuest && week.guest && week.guest.key) metaChips.push(`<a class="chip guest-chip" href="lecture.html?id=${week.guest.key}">▶ 이 주의 게스트 강연: ${esc(week.guest.name)}</a>`);
  if (isGuest && week.key) metaChips.push(`<a class="chip" href="lecture.html?id=${week.key}">📖 이 주의 본강의: ${esc(week.title_ko)}</a>`);
  metaRow.innerHTML = metaChips.join("");

  // 이전/다음
  const order = PLAY_ORDER, idx = order.indexOf(id);
  const prevBtn = document.getElementById("prev-btn"), nextBtn = document.getElementById("next-btn");
  if (idx > 0) { prevBtn.href = `lecture.html?id=${order[idx - 1]}`; prevBtn.style.display = ""; }
  if (idx >= 0 && idx < order.length - 1) { nextBtn.href = `lecture.html?id=${order[idx + 1]}`; nextBtn.style.display = ""; }

  // ----- 탭 -----
  const panels = { chapters: el("panel-chapters"), subs: el("panel-subs"), slides: el("panel-slides"), summary: el("panel-summary") };
  function el(i) { return document.getElementById(i); }
  document.querySelectorAll(".tab-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      document.querySelectorAll(".tab-btn").forEach((b) => b.classList.toggle("active", b === btn));
      Object.entries(panels).forEach(([k, p]) => (p.style.display = k === btn.dataset.tab ? "" : "none"));
      el("en-toggle-wrap").style.display = btn.dataset.tab === "subs" ? "" : "none";
      scrollActiveIntoView(true);
    });
  });
  el("show-en").addEventListener("change", (e) => panels.subs.classList.toggle("show-en", e.target.checked));

  // ----- 데이터 로드 (data/ko/{id}.js — file:// 에서도 동작) -----
  let DATA = null;
  const s = document.createElement("script");
  s.src = `data/ko/${id}.js`;
  s.onload = () => { DATA = (window.__LECTURES || {})[id]; if (DATA) render(); else showError(); };
  s.onerror = showError;
  document.body.appendChild(s);

  function showError() {
    panels.chapters.innerHTML = `<div class="loading-box">이 영상의 한국어 해설 데이터가 아직 준비되지 않았습니다.<br/>잠시 후 다시 확인해 주세요. 영상은 정상 재생됩니다.</div>`;
  }

  // ----- 한국어 번역 슬라이드 (있는 강의만) -----
  let SLIDES = null, slideEls = [], lastSl = -1;
  const slScript = document.createElement("script");
  slScript.src = `data/slides/${id}/slides.js`;
  slScript.onload = () => {
    SLIDES = (window.__SLIDES || {})[id];
    if (!SLIDES || !SLIDES.length) return;
    el("slides-tab").style.display = "";
    el("stage-pane").style.display = "";
    el("stage").classList.remove("no-slide");
    showStageSlide(0);
    panels.slides.innerHTML =
      `<div class="slides-note">🤖 AI(Gemini)가 원본 슬라이드를 한국어로 번역·재생성한 이미지입니다. 클릭하면 해당 구간으로 이동합니다.</div>` +
      SLIDES.map((s, i) =>
        `<div class="slide-item" data-i="${i}" data-start="${s.start}">
           <div class="slide-meta"><span class="ch-time">${fmt(s.start)}</span></div>
           <img loading="lazy" src="data/slides/${id}/${s.file}" alt="슬라이드 ${i + 1}" />
         </div>`).join("");
    slideEls = [...panels.slides.querySelectorAll(".slide-item")];
    slideEls.forEach((n) => n.addEventListener("click", () => seek(+n.dataset.start)));
  };
  slScript.onerror = () => {};
  document.body.appendChild(slScript);

  // ----- 영상 위 자막 트랙 (블록을 문장 단위로 분할, 길이 비례 시간 배분) -----
  let captions = [];
  function buildCaptions(blocks) {
    const track = [];
    for (let i = 0; i < blocks.length; i++) {
      const b = blocks[i];
      const end = i + 1 < blocks.length ? blocks[i + 1].start : b.start + 45;
      const dur = Math.max(2, end - b.start);
      const sents = (b.ko.match(/[^.?!…]+[.?!…]+["']?\s*|[^.?!…]+$/g) || [b.ko])
        .map((s) => s.trim()).filter(Boolean);
      // 너무 짧은 문장은 앞 문장에 합침 (자막 깜빡임 방지)
      const merged = [];
      for (const s of sents) {
        if (merged.length && (merged[merged.length - 1].length < 18 || s.length < 12)) {
          merged[merged.length - 1] += " " + s;
        } else merged.push(s);
      }
      const totalLen = merged.reduce((a, s) => a + s.length, 0) || 1;
      let t = b.start;
      for (const s of merged) {
        const d = dur * (s.length / totalLen);
        track.push({ start: t, end: t + d, text: s });
        t += d;
      }
    }
    return track;
  }

  const ccStrip = el("cc-strip");
  const ccText = el("cc-text");
  const CC_IDLE = "재생하면 이 자리에 한국어 자막이 표시됩니다";
  function setCaption(text) {
    ccStrip.classList.toggle("empty", !text);
    ccText.textContent = text || CC_IDLE;
  }
  setCaption("");
  const ccToggle = el("cc-toggle");
  ccToggle.checked = localStorage.getItem("cc-on") !== "0";
  ccStrip.classList.toggle("hidden", !ccToggle.checked);
  ccToggle.addEventListener("change", () => {
    localStorage.setItem("cc-on", ccToggle.checked ? "1" : "0");
    ccStrip.classList.toggle("hidden", !ccToggle.checked);
    lastCc = -2;
  });

  // ----- 분할선 드래그 (영상 ↔ 슬라이드 크기 조절) -----
  const stage = el("stage");
  const saved = parseFloat(localStorage.getItem("stage-split"));
  if (saved >= 25 && saved <= 75) stage.style.setProperty("--split", saved + "%");
  const divider = el("stage-divider");
  divider.addEventListener("pointerdown", (e) => {
    e.preventDefault();
    // iframe이 포인터 이벤트를 삼키지 않도록 캡처 + dragging 중 iframe 이벤트 차단(CSS)
    divider.setPointerCapture(e.pointerId);
    stage.classList.add("dragging");
    const rect = stage.getBoundingClientRect();
    const move = (ev) => {
      let pct = ((ev.clientX - rect.left) / rect.width) * 100;
      pct = Math.round(Math.min(75, Math.max(25, pct)) * 10) / 10;
      stage.style.setProperty("--split", pct + "%");
    };
    const up = (ev) => {
      divider.releasePointerCapture(e.pointerId);
      stage.classList.remove("dragging");
      const cur = parseFloat(stage.style.getPropertyValue("--split"));
      if (cur) localStorage.setItem("stage-split", cur);
      divider.removeEventListener("pointermove", move);
      divider.removeEventListener("pointerup", up);
      divider.removeEventListener("pointercancel", up);
    };
    divider.addEventListener("pointermove", move);
    divider.addEventListener("pointerup", up);
    divider.addEventListener("pointercancel", up);
  });

  // ----- 무대 슬라이드 (영상 옆 큰 슬라이드) -----
  let stageIdx = -1, follow = true;
  const stageImg = el("stage-slide-img");
  function showStageSlide(i, fromUser) {
    if (!SLIDES || !SLIDES.length) return;
    i = Math.min(SLIDES.length - 1, Math.max(0, i));
    if (i === stageIdx && !fromUser) return;
    stageIdx = i;
    stageImg.src = `data/slides/${id}/${SLIDES[i].file}`;
    el("slide-pos").textContent = `${i + 1}/${SLIDES.length}`;
  }
  function setFollow(on) {
    follow = on;
    const btn = el("slide-follow");
    btn.textContent = on ? "따라가기 ON" : "따라가기 OFF";
    btn.classList.toggle("on", on);
    btn.classList.toggle("off", !on);
  }
  el("slide-prev").addEventListener("click", () => { setFollow(false); showStageSlide(stageIdx - 1, true); });
  el("slide-next").addEventListener("click", () => { setFollow(false); showStageSlide(stageIdx + 1, true); });
  el("slide-follow").addEventListener("click", () => setFollow(!follow));
  stageImg.addEventListener("click", () => {
    if (SLIDES && stageIdx >= 0) { setFollow(true); seek(SLIDES[stageIdx].start); }
  });

  // ----- 렌더링 -----
  let chapterEls = [], blockEls = [];
  function render() {
    captions = buildCaptions(DATA.blocks);
    // 해설(챕터)
    panels.chapters.innerHTML = DATA.chapters.map((c, i) =>
      `<div class="chapter-item" data-i="${i}" data-start="${c.start}">
         <span class="ch-time">${fmt(c.start)}</span>
         <h4>${esc(c.title)}</h4>
         <p>${esc(c.explain)}</p>
       </div>`).join("");
    chapterEls = [...panels.chapters.querySelectorAll(".chapter-item")];
    chapterEls.forEach((n) => n.addEventListener("click", () => seek(+n.dataset.start)));

    // 자막
    panels.subs.innerHTML = DATA.blocks.map((b, i) =>
      `<div class="sub-item" data-i="${i}" data-start="${b.start}">
         <span class="sub-time">${fmt(b.start)}</span>
         <span class="sub-text">${esc(b.ko)}<span class="en-text">${esc(b.en)}</span></span>
       </div>`).join("");
    blockEls = [...panels.subs.querySelectorAll(".sub-item")];
    blockEls.forEach((n) => n.addEventListener("click", () => seek(+n.dataset.start)));

    // 요약
    panels.summary.innerHTML = `<div class="summary-pane">
      <h4>🧭 강의 한눈에 보기</h4>
      <p>${esc(DATA.summary)}</p>
      <h4>✅ 핵심 포인트</h4>
      <ul class="takeaway-list">${DATA.takeaways.map((t) => `<li>${esc(t)}</li>`).join("")}</ul>
      <h4>📚 핵심 용어</h4>
      ${DATA.terms.map((t) => `<div class="term-item"><b>${esc(t.ko)}</b><span class="term-en">${esc(t.term)}</span><p>${esc(t.desc)}</p></div>`).join("")}
    </div>`;
  }

  // ----- YouTube IFrame API -----
  let player = null, ready = false;
  window.onYouTubeIframeAPIReady = function () {
    player = new YT.Player("yt-player", {
      videoId: videoId,
      playerVars: { rel: 0, modestbranding: 1 },
      events: { onReady: () => { ready = true; window.__player = player; } },
    });
  };
  const yt = document.createElement("script");
  yt.src = "https://www.youtube.com/iframe_api";
  document.body.appendChild(yt);

  function seek(t) {
    if (ready && player) { player.seekTo(t, true); player.playVideo(); }
  }

  // ----- 시간 동기화 -----
  function activeIndex(els, t) {
    let lo = 0, hi = els.length - 1, ans = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (+els[mid].dataset.start <= t) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return ans;
  }
  let lastCh = -1, lastBl = -1, lastCc = -2;
  function findCaption(t) {
    let lo = 0, hi = captions.length - 1, ans = -1;
    while (lo <= hi) {
      const mid = (lo + hi) >> 1;
      if (captions[mid].start <= t) { ans = mid; lo = mid + 1; } else hi = mid - 1;
    }
    return ans >= 0 && t < captions[ans].end ? ans : -1;
  }
  function tick() {
    if (!ready || !player || !DATA || typeof player.getCurrentTime !== "function") return;
    const t = player.getCurrentTime();

    // 자막 줄 갱신
    if (ccToggle.checked && captions.length) {
      const playing = player.getPlayerState && player.getPlayerState() === 1;
      const ci2 = playing ? findCaption(t) : lastCc;
      if (ci2 !== lastCc) {
        lastCc = ci2;
        setCaption(ci2 >= 0 ? captions[ci2].text : "");
      }
    }

    const ci = activeIndex(chapterEls, t);
    if (ci !== lastCh) {
      chapterEls.forEach((n, i) => n.classList.toggle("active", i === ci));
      lastCh = ci;
      const box = el("now-chapter");
      if (ci >= 0) {
        box.style.display = "";
        el("now-title").textContent = DATA.chapters[ci].title;
        el("now-explain").textContent = DATA.chapters[ci].explain;
      }
      scrollActiveIntoView();
    }
    const bi = activeIndex(blockEls, t);
    if (bi !== lastBl) {
      blockEls.forEach((n, i) => n.classList.toggle("active", i === bi));
      lastBl = bi;
      scrollActiveIntoView();
    }
    if (slideEls.length) {
      const si = activeIndex(slideEls, t);
      if (si !== lastSl) {
        slideEls.forEach((n, i) => n.classList.toggle("active", i === si));
        lastSl = si;
        scrollActiveIntoView();
      }
      if (follow && si >= 0) showStageSlide(si);
    }
  }
  setInterval(tick, 500);

  function scrollActiveIntoView(force) {
    if (!el("autoscroll").checked && !force) return;
    const visible = Object.values(panels).find((p) => p.style.display !== "none");
    if (!visible) return;
    const active = visible.querySelector(".active");
    if (!active) return;
    // 패널 내부만 스크롤 (scrollIntoView는 페이지 전체를 움직여서 사용 금지)
    const top = active.getBoundingClientRect().top - visible.getBoundingClientRect().top
      + visible.scrollTop - visible.clientHeight / 2 + active.offsetHeight / 2;
    visible.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
  }
})();
