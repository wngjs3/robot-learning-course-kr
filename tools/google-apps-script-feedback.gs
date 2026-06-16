const DEFAULT_REPO = "wngjs3/robot-learning-course-kr";

function doGet() {
  return json_({ ok: true, service: "robot-learning-feedback" });
}

function doPost(e) {
  const raw = e && e.postData && e.postData.contents ? e.postData.contents : "{}";
  const payload = JSON.parse(raw);

  if (payload.website) return json_({ ok: true, skipped: true });
  if (!payload.message || String(payload.message).trim().length < 2) {
    return json_({ ok: false, error: "message_required" });
  }
  if (isRateLimited_(payload.clientId || "anonymous")) {
    return json_({ ok: false, error: "rate_limited" });
  }

  const props = PropertiesService.getScriptProperties();
  const token = props.getProperty("GITHUB_TOKEN");
  const repo = props.getProperty("GITHUB_REPO") || DEFAULT_REPO;
  if (!token) return json_({ ok: false, error: "missing_github_token" });

  const title = makeTitle_(payload);
  const body = makeBody_(payload);
  const request = {
    method: "post",
    contentType: "application/json",
    headers: {
      Authorization: "Bearer " + token,
      Accept: "application/vnd.github+json",
      "X-GitHub-Api-Version": "2022-11-28"
    },
    payload: JSON.stringify({ title: title, body: body }),
    muteHttpExceptions: true
  };

  const response = UrlFetchApp.fetch("https://api.github.com/repos/" + repo + "/issues", request);
  const status = response.getResponseCode();
  return json_({
    ok: status >= 200 && status < 300,
    status: status,
    response: response.getContentText().slice(0, 500)
  });
}

function makeTitle_(payload) {
  const pageTitle = payload.page && payload.page.title ? payload.page.title : "Robot Learning";
  const cleanTitle = pageTitle.replace(/\s+/g, " ").slice(0, 70);
  return "[site feedback] " + cleanTitle;
}

function makeBody_(payload) {
  const page = payload.page || {};
  const selection = payload.selection || {};
  const browser = payload.browser || {};
  const lines = [
    "## 내용",
    String(payload.message || "").trim(),
    "",
    "## 페이지",
    "- URL: " + (page.url || ""),
    "- 제목: " + (page.title || ""),
    "- 위치: " + (page.heading || ""),
    "",
    "## 선택된 텍스트",
    selection.text ? quote_(selection.text) : "_선택된 텍스트 없음_",
    "",
    "## 선택 정보",
    "- Anchor: " + (selection.anchorPath || ""),
    "- Focus: " + (selection.focusPath || ""),
    "- Offset: " + [selection.anchorOffset, selection.focusOffset].join(" / "),
    "- Rect: " + JSON.stringify(selection.rect || {}),
    "",
    "## 환경",
    "- Viewport: " + (browser.viewport || ""),
    "- ScrollY: " + (browser.scrollY || ""),
    "- Language: " + (browser.language || ""),
    "- Created: " + (payload.createdAt || ""),
    "",
    payload.email ? "Reply email: " + payload.email : ""
  ];
  return lines.join("\n");
}

function quote_(text) {
  return String(text)
    .split("\n")
    .map(function (line) { return "> " + line; })
    .join("\n");
}

function isRateLimited_(clientId) {
  const cache = CacheService.getScriptCache();
  const key = "rl_feedback_" + String(clientId).slice(0, 80);
  if (cache.get(key)) return true;
  cache.put(key, "1", 30);
  return false;
}

function json_(obj) {
  return ContentService
    .createTextOutput(JSON.stringify(obj))
    .setMimeType(ContentService.MimeType.JSON);
}
