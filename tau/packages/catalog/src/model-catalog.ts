/**
 * Model catalog utilities for tau providers.
 * Provides flattenModelCatalog and ModelCatalog type that upstream pi-ai
 * used to provide via @oh-my-pi/pi-catalog/model-catalog.
 * 
 * Types based on pi-ai v0.84.1 model-catalog.d.ts
 */
import type { Api, Model, ProviderId } from "./types";

export type ModelGroups = Record<string, Record<string, object>>;
type ModelId<TGroups extends ModelGroups> = {
    [TApi in keyof TGroups]: keyof TGroups[TApi];
}[keyof TGroups] & string;
type ModelApi<TGroups extends ModelGroups, TModelId extends ModelId<TGroups>> = {
    [TApi in keyof TGroups]: TModelId extends keyof TGroups[TApi] ? TApi : never;
}[keyof TGroups] & Api;
export type ModelCatalog<TGroups extends ModelGroups, TProvider extends ProviderId> = {
    [TModelId in ModelId<TGroups>]: Model<ModelApi<TGroups, TModelId>> & {
        id: TModelId;
        provider: TProvider;
    };
};

export function flattenModelCatalog<const TProvider extends ProviderId, const TGroups extends ModelGroups>(
    _provider: TProvider,
    groups: TGroups,
): ModelCatalog<TGroups, TProvider> {
    return Object.assign({}, ...Object.values(groups)) as ModelCatalog<TGroups, TProvider>;
}