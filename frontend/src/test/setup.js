import '@testing-library/jest-dom';
import { vi } from 'vitest';

window.alert = vi.fn();

Object.defineProperty(navigator, 'clipboard', {
    value: {
        writeText: vi.fn(),
    },
    configurable: true
});

if (typeof window !== 'undefined') {
    window.URL.createObjectURL = vi.fn();
    window.URL.revokeObjectURL = vi.fn();
}
