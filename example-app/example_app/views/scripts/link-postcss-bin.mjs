import { existsSync, rmSync, symlinkSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const viewsRoot = resolve(scriptDir, "..");
const binPath = resolve(viewsRoot, "node_modules/.bin/postcss");
const targetPath = resolve(viewsRoot, "node_modules/postcss-cli/index.js");

if (!existsSync(targetPath)) {
  process.exit(0);
}

rmSync(binPath, { force: true });
symlinkSync("../postcss-cli/index.js", binPath);
