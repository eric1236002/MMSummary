import { render, screen } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import SettingsSection from '../pages/SettingsSection';
import { translations } from '../translations';

describe('SettingsSection Component', () => {
    it('should render correct title in English', () => {
        const t = translations.en;
        const mockOnChange = vi.fn();

        const settings = {
            model: "google/gemma-3-27b-it:free",
            chunk_size_1: 16000,
            chunk_size_2: 8000,
            token_max: 16000,
            temperature: 0.0,
            strategy: "map",
            reduce_temple: "",
            map_temple: "",
            reduce_temperature: 0.0,
            test_mode: false,
            language: "en"
        };

        render(<SettingsSection settings={ settings } onChange = { mockOnChange } t = { t } />);

        expect(screen.getByText(t.title)).toBeDefined();
    });
});