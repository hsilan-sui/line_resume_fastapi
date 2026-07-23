// scripts/test-resolve-section.js
require("dotenv").config();
const { resolveSection } = require("../helpers/sections/resolve-section");

const city = process.env.CITY || "桃園市";
const district = process.env.DISTRICT || "13"; // townCode
const section = process.env.SECTION || "大利段";

const sec = resolveSection({ city, townCode: String(district), section });
console.log(sec);
console.log("resolvedSectionId =", sec?.sectionId || sec?.id);
