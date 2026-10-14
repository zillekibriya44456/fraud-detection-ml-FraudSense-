import '@testing-library/jest-dom';

// Node can expose an incomplete process-level localStorage implementation before
// jsdom is installed. Use a small, browser-compatible in-memory store so audio
// preference tests exercise the same Storage API used by the application.
const values = new Map<string, string>();
const storage: Storage = {
  get length() {
    return values.size;
  },
  clear() {
    values.clear();
  },
  getItem(key: string) {
    return values.get(key) ?? null;
  },
  key(index: number) {
    return Array.from(values.keys())[index] ?? null;
  },
  removeItem(key: string) {
    values.delete(key);
  },
  setItem(key: string, value: string) {
    values.set(key, String(value));
  },
};

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: storage,
});
