/**
 * Resolve API keys from environment variables.
 * Used by provider auth configurations to check credentials are present.
 * Delegates to stream.ts getEnvApiKey for single-source-of-truth env resolution.
 */
import { getEnvApiKey } from "../../stream";

export function envApiKeyAuth(label: string, envVars: string[]) {
  return () => {
    for (const v of envVars) {
      const k = getEnvApiKey(v) ?? process.env[v];
      if (k) return k;
    }
    return undefined;
  };
}