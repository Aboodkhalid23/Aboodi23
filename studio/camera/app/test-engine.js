// يقارن محرك JavaScript ويا ملفات .cube الي يصنعها make-luts.py (لازم يطابقها)
const fs = require("fs"), path = require("path");
require("./lut-engine.js");
const looks = JSON.parse(fs.readFileSync(process.argv[2] || path.join(__dirname, "looks.json"), "utf8"));
let worst = 0;
Object.keys(looks).forEach((k, i) => {
  const py = fs.readFileSync(path.join(__dirname, "..", "luts", `${i + 1}.cube`), "utf8").trim().split("\n").slice(4)
    .map((l) => l.split(" ").map(Number));
  const T = LutEngine.buildTable(looks[k], 33);
  let d = 0;
  py.forEach((row, j) => row.forEach((v, c) => { d = Math.max(d, Math.abs(v - T[j * 3 + c])); }));
  LutEngine.cubeText(T, 33, k);
  console.log(`${i + 1} ${k}: أكبر فرق ${d.toExponential(2)}`);
  worst = Math.max(worst, d);
});
if (worst > 2e-4) { console.error("❌ المحرك ما يطابق البايثون"); process.exit(1); }
console.log("✅ يطابق");
