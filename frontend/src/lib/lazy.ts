/**
 * React.lazy adapter for modules that use named exports (#102).
 *
 * React.lazy expects a default export, but our convention is named
 * exports (`export const PlayersPage = ...`). This helper bridges the
 * gap so route definitions stay readable.
 *
 *   const PlayersPage = lazyNamed(
 *     () => import('@/pages/Players/PlayersPage'),
 *     'PlayersPage',
 *   );
 *
 * Throws an explicit error if the named export isn't found (typo /
 * rename) — a silent `undefined` would otherwise turn into a cryptic
 * "Element type is invalid" runtime crash inside React.lazy.
 */
import { lazy, type ComponentType, type LazyExoticComponent } from 'react';

// Exported so it can be tested without driving React.lazy's internals,
// which have shifted across React versions. The wrapper below stays
// the public API; this function is the unit under test.
export async function resolveNamedExport<T extends ComponentType<any>>(
  loader: () => Promise<Record<string, unknown>>,
  name: string,
): Promise<{ default: T }> {
  const mod = await loader();
  const exported = mod[name];
  if (typeof exported !== 'function' && typeof exported !== 'object') {
    throw new Error(
      `lazyNamed: module has no exported component named "${name}". ` +
        `Available exports: ${Object.keys(mod).join(', ') || '(none)'}`,
    );
  }
  return { default: exported as T };
}

export function lazyNamed<T extends ComponentType<any>>(
  loader: () => Promise<Record<string, unknown>>,
  name: string,
): LazyExoticComponent<T> {
  return lazy(() => resolveNamedExport<T>(loader, name));
}
