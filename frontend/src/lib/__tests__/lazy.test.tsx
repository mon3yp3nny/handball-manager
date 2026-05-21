/**
 * Tests for lazyNamed (#102).
 *
 * The helper bridges our named-export convention to React.lazy's
 * default-export contract. Failure modes to cover:
 *   - happy path: a real named export renders after Suspense resolves
 *   - dev-time guardrail: bad name throws an explicit error rather
 *     than the cryptic "Element type is invalid" we'd get from a
 *     silent `undefined` export
 *   - loader rejection (network failure) propagates to the caller
 *
 * The throw/reject paths are tested against `resolveNamedExport`
 * directly rather than through `React.lazy`, because `React.lazy`'s
 * internal _payload/_init shape varies across React versions and is
 * not part of the public API.
 */
import { Suspense } from 'react';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { lazyNamed, resolveNamedExport } from '../lazy';

afterEach(() => {
  cleanup();
});

describe('lazyNamed', () => {
  it('renders a component exported by its given name once the chunk resolves', async () => {
    const NamedHello = () => <p>hello from named</p>;
    const Lazy = lazyNamed(
      () => Promise.resolve({ NamedHello }),
      'NamedHello',
    );

    render(
      <Suspense fallback={<span>loading…</span>}>
        <Lazy />
      </Suspense>,
    );

    // Suspense fallback shows first synchronously.
    expect(screen.getByText('loading…')).toBeInTheDocument();
    // Then the lazy module resolves and the named export mounts.
    await waitFor(() => {
      expect(screen.getByText('hello from named')).toBeInTheDocument();
    });
  });
});

describe('resolveNamedExport', () => {
  it('returns { default: <component> } when the named export exists', async () => {
    const Comp = () => <span />;
    const out = await resolveNamedExport(
      () => Promise.resolve({ Comp }),
      'Comp',
    );
    expect(out.default).toBe(Comp);
  });

  it('throws a useful error when the named export is missing', async () => {
    await expect(
      resolveNamedExport(
        // Module that exports OtherThing, not WrongName.
        () => Promise.resolve({ OtherThing: () => <span /> }),
        'WrongName',
      ),
    ).rejects.toThrow(/lazyNamed: module has no exported component named "WrongName".*OtherThing/s);
  });

  it('propagates loader rejections (network failure surfaces to caller)', async () => {
    await expect(
      resolveNamedExport(
        () => Promise.reject(new Error('network down')),
        'X',
      ),
    ).rejects.toThrow('network down');
  });
});
