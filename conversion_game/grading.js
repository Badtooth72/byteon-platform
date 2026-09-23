function normaliseAnswer(value) {
  return String(value ?? "").trim().toLowerCase();
}

function equivalentAnswer(question, submitted, expected) {
  const prompt = normaliseAnswer(question);
  const actual = normaliseAnswer(submitted);
  const wanted = normaliseAnswer(expected);
  if (prompt.includes("to binary") && /^[01]+$/.test(actual) && /^[01]+$/.test(wanted)) {
    return Number.parseInt(actual, 2) === Number.parseInt(wanted, 2);
  }
  if (prompt.includes("to hex") && /^[0-9a-f]+$/.test(actual) && /^[0-9a-f]+$/.test(wanted)) {
    return Number.parseInt(actual, 16) === Number.parseInt(wanted, 16);
  }
  if (prompt.includes("to decimal") && /^\d+$/.test(actual) && /^\d+$/.test(wanted)) {
    return Number.parseInt(actual, 10) === Number.parseInt(wanted, 10);
  }
  return actual === wanted;
}

function gradeAnswers(questions, answers) {
  if (!Array.isArray(answers) || answers.length !== questions.length) {
    throw new Error("Invalid answers");
  }
  return questions.map((question, index) => equivalentAnswer(
    question.question, answers[index], question.answer
  ));
}

module.exports = { equivalentAnswer, gradeAnswers, normaliseAnswer };
