// 메인 페이지: 강의 일정 카드 + 실습 테이블 렌더링
(function () {
  const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  // 본강의와 게스트 강연을 동등한 '강의 행'으로 렌더링
  function lectureRow(badge, badgeClass, titleHtml, subHtml, key, video) {
    const actions = [];
    if (key) actions.push(`<a class="chip play" href="lecture.html?id=${key}">▶ 강의 보기</a>`);
    if (video) actions.push(`<a class="chip" href="https://www.youtube.com/watch?v=${video}" target="_blank" rel="noopener">유튜브 원본 ↗</a>`);

    // 썸네일: 한국어 번역 타이틀 슬라이드 → 없으면 유튜브 썸네일 → 그것도 없으면 플레이스홀더
    let thumb;
    if (key || video) {
      const fallback = video ? `this.onerror=null;this.src='https://i.ytimg.com/vi/${video}/hqdefault.jpg';` : "this.style.display='none';";
      const src = key ? `data/slides/${key}/web/000.webp` : `https://i.ytimg.com/vi/${video}/hqdefault.jpg`;
      const img = `<img loading="lazy" src="${src}" alt="" onerror="${fallback}" />`;
      thumb = key
        ? `<a class="lec-thumb" href="lecture.html?id=${key}">${img}<span class="lec-thumb-play">▶</span></a>`
        : `<span class="lec-thumb">${img}</span>`;
    } else {
      thumb = `<span class="lec-thumb empty"></span>`;
    }

    return `<div class="lec-row">
      ${thumb}
      <div class="lec-row-main">
        <span class="lec-badge ${badgeClass}">${badge}</span>
        <div class="lec-row-title">${titleHtml}</div>
        ${subHtml ? `<div class="lec-row-sub">${subHtml}</div>` : ""}
      </div>
      <div class="lec-row-actions">${actions.join("")}</div>
    </div>`;
  }

  const list = document.getElementById("week-list");
  if (list) {
    list.innerHTML = COURSE.weeks.map((w) => {
      const rows = [];
      rows.push(lectureRow(
        "강의", "main",
        w.key
          ? `<a href="lecture.html?id=${w.key}">${esc(w.title_ko)}</a><span class="en">${esc(w.title_en)}</span>`
          : `${esc(w.title_ko)}<span class="en">${esc(w.title_en)}</span>`,
        "", w.key, w.video
      ));
      if (w.guest) {
        const g = w.guest;
        const sub = `${esc(g.affil)} · <a href="${g.url}" target="_blank" rel="noopener">발표자 홈페이지 ↗</a>`;
        rows.push(lectureRow(
          "게스트", "guest",
          g.key
            ? `<a href="lecture.html?id=${g.key}">${esc(g.name)}</a>`
            : `<a href="${g.url}" target="_blank" rel="noopener">${esc(g.name)}</a>`,
          sub, g.key, g.video
        ));
      }

      const koMap = window.__PAPERS_KO || {};
      const papers = w.papers.length
        ? `<details class="week-papers">
             <summary><span class="arr">▶</span> 논문 토론 (${w.papers.length}편)</summary>
             <ul>${w.papers.map((p) => {
               const ko = koMap[p.u] ? ` <a class="paper-ko-link" href="${koMap[p.u]}">[한국어 번역]</a>` : "";
               return `<li><a href="${p.u}" target="_blank" rel="noopener">${esc(p.t)}</a> <span class="auth">— ${esc(p.a)}</span>${ko}</li>`;
             }).join("")}</ul>
           </details>`
        : "";

      return `<article class="week-card">
        <div class="week-head">
          <div class="week-num"><b>${w.week}</b><span>WEEK</span></div>
          <div class="week-main">
            <div class="lec-rows">${rows.join("")}</div>
            ${papers}
          </div>
        </div>
      </article>`;
    }).join("");
  }

  const tut = document.getElementById("tut-body");
  if (tut) {
    tut.innerHTML = COURSE.tutorials.map((t) => `<tr>
        <td style="white-space:nowrap;color:var(--ink-faint);font-weight:700;">${esc(t.week)}</td>
        <td style="font-weight:700;">${esc(t.topic)}</td>
        <td><a href="${t.url}" target="_blank" rel="noopener">한국어판 코드 ↗</a> &nbsp;·&nbsp; <a href="${t.orig}" target="_blank" rel="noopener" style="color:var(--ink-faint);">원본</a></td>
      </tr>`).join("");
  }
})();
