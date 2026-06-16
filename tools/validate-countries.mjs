import { existsSync, readFileSync } from "node:fs";
import { dirname, join } from "node:path";
import { fileURLToPath, pathToFileURL } from "node:url";

const ROOT = join(dirname(fileURLToPath(import.meta.url)), "..");
const countriesPath = join(ROOT, "data", "countries.json");
const continentsPath = join(ROOT, "data", "continents.json");
const publicCountriesPath = join(ROOT, "public", "countries.js");

const REQUIRED = [
  "id",
  "iso2",
  "iso3",
  "name",
  "capital",
  "continent",
  "languages",
  "flag_asset",
  "theme_colors",
  "flag_regions",
  "flag_colors",
  "difficulty",
  "landmark",
  "foods",
  "animals",
  "fun_facts",
  "currency",
  "population",
];

const ID_RE = /^[a-z0-9]+(?:-[a-z0-9]+)*$/;
const ISO2_RE = /^[A-Z]{2}$/;
const ISO3_RE = /^[A-Z]{3}$/;
const HEX_RE = /^#[0-9A-Fa-f]{6}$/;
const DIFFICULTIES = new Set(["easy", "medium", "hard", "expert"]);

const countries = JSON.parse(readFileSync(countriesPath, "utf8"));
const continents = JSON.parse(readFileSync(continentsPath, "utf8"));
const { COUNTRIES: runtimeCountries } = await import(pathToFileURL(publicCountriesPath));
const continentNames = new Set(continents.map(continent => continent.name));
const errors = [];

function add(message) {
  errors.push(message);
}

function unique(label, records, getter) {
  const seen = new Map();
  for (const record of records) {
    const value = getter(record);
    if (!value) continue;
    if (seen.has(value)) add(`${label} "${value}" duplicated by ${seen.get(value)} and ${record.id}`);
    else seen.set(value, record.id);
  }
}

function sameSet(label, left, right) {
  const a = new Set(left);
  const b = new Set(right);
  for (const value of a) if (!b.has(value)) add(`${label} missing from runtime: ${value}`);
  for (const value of b) if (!a.has(value)) add(`${label} missing from data: ${value}`);
}

if (!Array.isArray(countries)) add("countries.json must be an array");
if (!Array.isArray(continents)) add("continents.json must be an array");
if (!Array.isArray(runtimeCountries)) add("public/countries.js must export COUNTRIES array");

unique("country id", countries, country => country.id);
unique("iso2", countries, country => country.iso2);
unique("iso3", countries, country => country.iso3);
unique("country name", countries, country => country.name);

for (const country of countries) {
  for (const field of REQUIRED) {
    if (!(field in country)) add(`${country.id || "(missing id)"} missing required field: ${field}`);
  }

  if (!ID_RE.test(country.id || "")) add(`${country.id || "(missing id)"} has invalid id`);
  if (!ISO2_RE.test(country.iso2 || "")) add(`${country.id} has invalid iso2`);
  if (!ISO3_RE.test(country.iso3 || "")) add(`${country.id} has invalid iso3`);
  if (!continentNames.has(country.continent)) add(`${country.id} has unknown continent: ${country.continent}`);
  if (!Array.isArray(country.languages) || country.languages.length === 0) add(`${country.id} needs at least one language`);
  if (!Array.isArray(country.theme_colors) || country.theme_colors.length === 0) add(`${country.id} needs theme_colors`);
  if (!Array.isArray(country.flag_colors) || country.flag_colors.length === 0) add(`${country.id} needs flag_colors`);
  for (const color of [...(country.theme_colors || []), ...(country.flag_colors || [])]) {
    if (!HEX_RE.test(color)) add(`${country.id} has invalid color: ${color}`);
  }
  if (!DIFFICULTIES.has(country.difficulty)) add(`${country.id} has invalid difficulty: ${country.difficulty}`);
  for (const listField of ["foods", "animals", "fun_facts"]) {
    if (!Array.isArray(country[listField])) add(`${country.id}.${listField} must be an array`);
  }

  const assetPath = join(ROOT, "public", country.flag_asset || "");
  if (!country.flag_asset || !existsSync(assetPath)) add(`${country.id} missing flag asset: public/${country.flag_asset}`);

  if (!Array.isArray(country.flag_regions)) {
    add(`${country.id}.flag_regions must be an array`);
    continue;
  }

  const regionIds = new Set();
  for (const region of country.flag_regions) {
    if (!region.id) add(`${country.id} has a flag region without id`);
    if (regionIds.has(region.id)) add(`${country.id} has duplicate flag region: ${region.id}`);
    regionIds.add(region.id);
    if (!Number.isInteger(region.color) || region.color < 0 || region.color >= country.flag_colors.length) {
      add(`${country.id}.${region.id} has invalid color index`);
    }
    if (!Array.isArray(region.shapes) || region.shapes.length === 0) add(`${country.id}.${region.id} needs shapes`);
  }
}

sameSet("country id", countries.map(country => country.id), runtimeCountries.map(country => country.id));

if (errors.length) {
  console.error(`Country validation failed with ${errors.length} issue(s):`);
  for (const error of errors) console.error(`- ${error}`);
  process.exit(1);
}

console.log(`Country validation passed: ${countries.length} countries, ${continents.length} continents`);
