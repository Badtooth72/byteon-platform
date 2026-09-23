const test = require("node:test");
const assert = require("node:assert/strict");
const { gradeAnswers } = require("./grading");

test("grades answers case insensitively without trusting a supplied score", () => {
  const questions = [
    { question: "Convert decimal 255 to hex", answer: "FF" },
    { question: "Convert decimal 10 to binary", answer: "1010" },
  ];
  assert.deepEqual(gradeAnswers(questions, ["ff", "1011"]), [true, false]);
});

test("accepts equivalent padded binary answers", () => {
  const questions = [{ question: "Convert decimal 2 to binary", answer: "10" }];
  assert.deepEqual(gradeAnswers(questions, ["00000010"]), [true]);
});

test("rejects incomplete submissions", () => {
  assert.throws(() => gradeAnswers([{ answer: "1" }], []), /Invalid answers/);
});
