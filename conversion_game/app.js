const express = require("express");
const { MongoClient } = require("mongodb");
const generateQuestions = require("./gameLogic");
const crypto = require("crypto");
const { gradeAnswers } = require("./grading");

const app = express();
app.use(express.json());
app.use((req, res, next) => {
  if (!["POST", "PUT", "PATCH", "DELETE"].includes(req.method)) return next();
  const origin = req.get("origin");
  if (origin && new URL(origin).host !== req.get("host")) return res.status(403).json({ error: "Cross-origin request rejected" });
  next();
});
app.use(express.static("public"));

const mongoUri = process.env.MONGO_URI || "mongodb://localhost:27017";
const dbName = "auth_db";
let db;
const games = new Map();
const ALLOWED_MODES = new Set(["easy", "medium", "hard", "custom"]);
const ALLOWED_TYPES = new Set(["bin-to-dec", "dec-to-bin", "hex-to-bin", "bin-to-hex", "dec-to-hex", "hex-to-dec"]);

MongoClient.connect(mongoUri).then(client => {
  db = client.db(dbName);
  console.log("✅ Connected to MongoDB:", dbName);
});

app.get("/api/questions", (req, res) => {
  const mode = req.query.mode || "easy";
  if (!ALLOWED_MODES.has(mode)) return res.status(400).json({ error: "Invalid mode" });
  const count = Math.min(Math.max(Number.parseInt(req.query.count, 10) || 10, 1), 30);
  const customTypes = (req.query.types || "").split(",").filter(type => ALLOWED_TYPES.has(type));
  if (mode === "custom" && customTypes.length === 0) return res.status(400).json({ error: "Choose at least one conversion type" });
  const questions = generateQuestions(mode, count, customTypes);
  const gameId = crypto.randomUUID();
  games.set(gameId, { mode, questions, createdAt: Date.now() });
  res.json({ gameId, questions: questions.map(({ question }) => ({ question })) });
});

app.post("/api/submit", async (req, res) => {
  const { gameId, answers, times } = req.body;

  let username;
  try {
    const authResponse = await fetch("http://auth:5002/api/session-user", {
      headers: { Cookie: req.headers.cookie || "" },
      signal: AbortSignal.timeout(3000),
    });
    if (!authResponse.ok) return res.status(401).json({ error: "Not logged in" });
    const authUser = await authResponse.json();
    username = authUser.username;
  } catch (err) {
    return res.status(503).json({ error: "Authentication unavailable" });
  }

  if (!username || username === "guest") {
    return res.status(401).json({ error: "Not logged in" });
  }

  const game = games.get(gameId);
  if (!game || Date.now() - game.createdAt > 30 * 60 * 1000) {
    games.delete(gameId);
    return res.status(400).json({ error: "Game has expired" });
  }
  if (!Array.isArray(answers) || !Array.isArray(times) || answers.length !== game.questions.length || times.length !== game.questions.length) {
    return res.status(400).json({ error: "Invalid payload" });
  }
  if (!times.every(value => Number.isFinite(value) && value >= 0 && value <= 3600)) return res.status(400).json({ error: "Invalid timing data" });
  const correct = gradeAnswers(game.questions, answers);
  const score = correct.filter(Boolean).length;
  const correctTimes = times.filter((_, index) => correct[index]);
  const mode = game.mode;
  games.delete(gameId);

  const totalTime = correctTimes.reduce((a, b) => a + b, 0);
  const fastest = correctTimes.length ? Math.min(...correctTimes) : 0;

  const data = {
    score,
    question_count: game.questions.length,
    total_time: Number(totalTime.toFixed(2)),
    fastest_time: Number(fastest.toFixed(2)),
    date: new Date()
  };

  try {
    await db.collection("users").updateOne(
      { username },
      {
        $set: {
          [`activities.conversion_game.${mode}`]: data,
        }
      },
      { upsert: true }
    );

    console.log("📥 Saved result for", username, ":", data);
    res.json({
      message: "Result saved",
      stats: data,
      results: correct.map((isCorrect, index) => ({
        correct: isCorrect,
        answer: game.questions[index].answer,
      })),
    });
  } catch (err) {
    console.error("❌ Error saving result:", err);
    res.status(500).json({ error: "Failed to save result" });
  }
});

app.listen(5003, () => console.log("🚀 Conversion Game API running on port 5003"));
