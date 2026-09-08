import { createApiKeyLogin } from "./api-key-login";
import type { OAuthLoginCallbacks } from "./oauth/types";
import type { ProviderDefinition } from "./types";
import { streamGroq, streamSimpleGroq, listGroqModelsLive } from "../providers/groq";

const GROQ_BASE_URL = "https://api.groq.com/openai/v1";
const GROQ_AUTH_URL = "https://console.groq.com/keys";

export { streamGroq, streamSimpleGroq, listGroqModelsLive };

export const loginGroq = createApiKeyLogin({
	providerLabel: "Groq",
	authUrl: GROQ_AUTH_URL,
	instructions: "Copy your API key from Groq Console → API Keys",
	promptMessage: "Paste your Groq API key",
	placeholder: "gsk_...",
	validation: {
		kind: "chat-completions",
		provider: "Groq",
		baseUrl: GROQ_BASE_URL,
		model: "openai/gpt-oss-20b",
	},
});

export const groqProvider: ProviderDefinition = {
	id: "groq",
	name: "Groq",
	login: (cb: OAuthLoginCallbacks) => loginGroq(cb),
	envKeys: "GROQ_API_KEY",
};

export { GROQ_BASE_URL, GROQ_AUTH_URL };