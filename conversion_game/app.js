const express = require("express");
const cors = require("cors");
const { MongoClient } = require("mongodb");
const generateQuestions = require("./gameLogic");

const app = express();
app.use(cors());
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
  const { username, mode, score, times, forename, surname, class_name, current_yeargroup } = req.body;

  if (!username || !mode || !Array.isArray(times)) {
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

  // Only set metadata if available
  const userMetadata = {};
  if (forename) userMetadata["forename"] = forename;
  if (surname) userMetadata["surname"] = surname;
  if (class_name) userMetadata["class_name"] = class_name;
  if (current_yeargroup) userMetadata["current_yeargroup"] = current_yeargroup;

  try {
    await db.collection("users").updateOne(
      { username },
      {
        $set: {
          [`activities.conversion_game.${mode}`]: data,
          ...userMetadata
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
