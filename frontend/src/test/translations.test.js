import { describe, it, expect } from 'vitest';
import { translations } from '../translations';

describe('Localization Dictionary', () => {
    it('should have consistent keys between Traditional Chinese and English', () => {
        const zhKeys = Object.keys(translations.zh).sort();
        const enKeys = Object.keys(translations.en).sort();

        expect(zhKeys).toEqual(enKeys);
    });

    it('should return correct Chinese title for settings', () => {
        expect(translations.zh.title).toBe('偏好設定');
    });

    it('should return correct English title for settings', () => {
        expect(translations.en.title).toBe('Settings');
    });

    it('should have collapse/expand labels in both languages', () => {
        expect(translations.zh.expand_content).toBeDefined();
        expect(translations.en.expand_content).toBeDefined();
    });
});
