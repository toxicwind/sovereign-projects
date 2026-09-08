// This file is auto-generated from groq.json. Do not edit manually.

import values from "./groq.json" with { type: "json" };
import { flattenModelCatalog, type ModelCatalog } from "@oh-my-pi/pi-catalog/model-catalog";

export const GROQ_MODELS: ModelCatalog<typeof values, "groq"> = flattenModelCatalog("groq", values);
