import * as os from "node:os";
import * as path from "node:path";
import { getProjectDir, setProjectDir } from "@oh-my-pi/pi-utils";
import type { Args } from "./args";

function isTempDir(dir: string): boolean {
	const normalized = path.resolve(dir);
	const osTmp = path.resolve(os.tmpdir());
	return (
		normalized === "/tmp" ||
		normalized === "/var/tmp" ||
		normalized.startsWith("/tmp/") ||
		normalized.startsWith("/var/tmp/") ||
		normalized === osTmp ||
		normalized.startsWith(`${osTmp}/`)
	);
}

export async function applyStartupCwd(parsed: Args): Promise<void> {
	if (parsed.cwd) {
		try {
			setProjectDir(parsed.cwd);
		} catch (error) {
			const reason = error instanceof Error ? error.message : String(error);
			const code = (error as NodeJS.ErrnoException | null)?.code;
			const hint =
				code === "EACCES" || code === "EPERM"
					? " On macOS, grant omp Files & Folders or Full Disk Access permission for the target directory."
					: "";
			throw new Error(`Cannot change working directory to ${parsed.cwd}: ${reason}.${hint}`);
		}
		parsed.cwd = getProjectDir();
		return;
	}

	const current = getProjectDir();
	if (isTempDir(current)) {
		const home = os.homedir();
		try {
			setProjectDir(home);
			parsed.cwd = getProjectDir();
		} catch {
			// Fallback silently if home is unreachable
		}
	}
}
