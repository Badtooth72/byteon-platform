function getRandomInt(max) {
  return Math.floor(Math.random() * max);
}

function toBinary(n) {
  return n.toString(2); //no padding to make it 8 bits
}

function toHex(n) {
  return n.toString(16).toUpperCase().padStart(2, "0");
}

function fromBinary(bin) {
  return parseInt(bin, 2);
}

function fromHex(hex) {
  return parseInt(hex, 16);
}

function randomConversion(type) {
  const value = getRandomInt(256); // Max 1 byte
  let question, answer;

  switch (type) {
    case "bin-to-dec":
      question = `Convert binary ${toBinary(value)} to decimal`;
      answer = String(value);
      break;
    case "dec-to-bin":
      question = `Convert decimal ${value} to binary`;
      answer = toBinary(value);
      break;
    case "hex-to-bin":
      question = `Convert hex ${toHex(value)} to binary`;
      answer = toBinary(value);
      break;
    case "bin-to-hex":
      question = `Convert binary ${toBinary(value)} to hex`;
      answer = toHex(value);
      break;
    case "dec-to-hex":
      question = `Convert decimal ${value} to hex`;
      answer = toHex(value);
      break;
    case "hex-to-dec":
      question = `Convert hex ${toHex(value)} to decimal`;
      answer = String(value);
      break;
    default:
      question = "Invalid type";
      answer = "";
  }

  return { question, answer };
}

function generateQuestions(mode, count = 10, customTypes = []) {
  let types = [];

  switch (mode) {
    case "easy":
      types = ["bin-to-dec", "dec-to-bin"];
      count = 10;
      break;
    case "medium":
      types = ["bin-to-dec", "dec-to-bin", "hex-to-bin", "bin-to-hex"];
      count = 20;
      break;
    case "hard":
      types = [
        "bin-to-dec",
        "dec-to-bin",
        "hex-to-bin",
        "bin-to-hex",
        "dec-to-hex",
        "hex-to-dec"
      ];
      count = 20;
      break;
    case "custom":
      types = customTypes.filter(Boolean);
      break;
    default:
      types = ["bin-to-dec", "dec-to-bin"];
  }

  const questions = [];
  for (let i = 0; i < count; i++) {
    const type = types[getRandomInt(types.length)];
    questions.push(randomConversion(type));
  }

  return questions;
}

module.exports = generateQuestions;

