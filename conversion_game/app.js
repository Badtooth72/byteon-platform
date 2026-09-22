const express = require("express");
const { MongoClient } = require("mongodb");
const generateQuestions = require("./gameLogic");

const app = express();
app.use(express.json());
app.use(express.static("public"));

const mongoUri = process.env.MONGO_URI || "mongodb://localhost:27017";
const dbName = "auth_db";
let db;

MongoClient.connect(mongoUri).then(client => {
  db = client.db(dbName);
  console.log("✅ Connected to MongoDB:", dbName);
});

app.get("/api/questions", (req, res) => {
  const mode = req.query.mode || "easy";
  const count = parseInt(req.query.count) || 10;
  const customTypes = (req.query.types || "").split(",");
  const questions = generateQuestions(mode, count, customTypes);
  res.json({ questions });
});

app.post("/api/submit", async (req, res) => {
  const { mode, score, times } = req.body;

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

  if (!mode || !Array.isArray(times)) {
    return res.status(400).json({ error: "Invalid payload" });
  }

  const totalTime = times.reduce((a, b) => a + b, 0);
  const fastest = Math.min(...times);

  const data = {
    score,
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
    res.json({ message: "Result saved", stats: data });
  } catch (err) {
    console.error("❌ Error saving result:", err);
    res.status(500).json({ error: "Failed to save result" });
  }
});

app.listen(5003, () => console.log("🚀 Conversion Game API running on port 5003"));
