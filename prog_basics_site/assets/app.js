
(function(){
  const preferred = localStorage.getItem("theme") || "dark";
  if (preferred === "light") document.documentElement.classList.add("light");
  document.querySelectorAll(".theme-toggle").forEach(btn => {
    btn.addEventListener("click", () => {
      document.documentElement.classList.toggle("light");
      const isLight = document.documentElement.classList.contains("light");
      localStorage.setItem("theme", isLight ? "light" : "dark");
    });
  });

  const here = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll(".nav a").forEach(a => {
    const target = a.getAttribute("href");
    if (target.endsWith(here)) a.classList.add("active");
  });

  const scoresRaw = localStorage.getItem("topicScores");
  if (scoresRaw) {
    const scores = JSON.parse(scoresRaw);
    for (const [topic, s] of Object.entries(scores)) {
      const link = document.querySelector(`.nav a[data-topic="${topic}"]`);
      if (!link) continue;
      if (s.total && s.total > 0) {
        const pct = Math.round((s.correct / s.total) * 100);
        link.classList.remove("rag-green","rag-amber","rag-red");
        if (pct === 100) link.classList.add("rag-green");
        else if (pct >= 50) link.classList.add("rag-amber");
        else link.classList.add("rag-red");
        link.title = `${pct}% on ${topic} quiz`;
      }
    }
  }
})();

window.Quiz = (function(){
  const KEY = "topicScores";
  function getScores(){ try{ return JSON.parse(localStorage.getItem(KEY)) || {}; }catch(e){ return {}; } }
  function saveScores(data){ localStorage.setItem(KEY, JSON.stringify(data)); }
  function record(topic, correct, total){
    const scores = getScores();
    scores[topic] = {correct, total};
    saveScores(scores);
  }
  return { record, getScores };
})();
