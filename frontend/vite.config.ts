/// <reference types="vitest" />
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  // Vitest config lives inline so the test runner inherits vite's
  // module resolution (path aliases, plugins). jsdom gives us a DOM
  // for Testing Library; globals: true lets test files use describe/it
  // without imports; the setup file wires jest-dom matchers.
  test: {
    // happy-dom (not jsdom) — jsdom hangs at startup under Node 25 +
    // Vitest 4. happy-dom is the other Vitest-blessed DOM impl and is
    // faster anyway. If you ever switch back to Node 22 LTS, jsdom
    // works again — happy-dom has near-identical Testing Library
    // compat for everything we test.
    environment: 'happy-dom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    css: false,  // skip CSS parsing — speeds tests up massively
    // Vitest's default include pulls anything matching *.test.* — that
    // grabs Playwright e2e specs too, which crash with "Playwright Test
    // did not expect test.describe() to be called here". Pin Vitest to
    // src/ so unit + e2e suites stay in their own worlds.
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['node_modules', 'dist', 'e2e', 'playwright-report', 'test-results'],
    // Vitest 4's default `threads` pool also hangs on Node 25 in some
    // configurations; `forks` is the proven-stable choice.
    pool: 'forks',
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html'],
      exclude: [
        'node_modules/',
        'dist/',
        'src/test/',
        'src/**/*.d.ts',
        'src/main.tsx',
        '**/*.config.*',
        'e2e/',
      ],
    },
  },
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true,
      },
    },
  },
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:8000',
        ws: true,
      },
    },
  },
})
