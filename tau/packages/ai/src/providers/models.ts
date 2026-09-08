/**
 * Provider model definitions and createProvider utility for tau providers.
 * 
 * This file provides a createProvider utility for constructing provider definitions.
 */

export function createProvider<T extends Partial<Provider>>(
	config: T
): Provider & T {
	// Identity function - the type system handles the rest
	return config as unknown as Provider & T;
}