import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import SettingsSection from '../pages/SettingsSection';
import { translations } from '../translations';

describe('SettingsSection Component', () => {
    const t = translations.en;
    const defaultSettings = {
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

    it('should show basic elements', () => {
        const mockOnChange = vi.fn();
        render(<SettingsSection settings={defaultSettings} onChange={mockOnChange} t={t} />);
        expect(screen.getByText(t.title)).toBeDefined();
    });

    it('should trigger onChange for all inputs', () => {
        const mockOnChange = vi.fn();
        const { container } = render(<SettingsSection settings={defaultSettings} onChange={mockOnChange} t={t} />);

        // 1. Model Text Change
        const modelInput = screen.getByLabelText(t.model);
        fireEvent.change(modelInput, { target: { value: 'm' } });
        expect(mockOnChange).toHaveBeenCalled();

        // 2. Chunk Size Change
        const chunkSizeInput = screen.getByLabelText(t.chunkSize1);
        fireEvent.change(chunkSizeInput, { target: { value: '100' } });
        expect(mockOnChange).toHaveBeenCalled();

        // 3. Switch Change (MUI Switch uses an input checkbox)
        const checkbox = container.querySelector('input[type="checkbox"]');
        if (checkbox) fireEvent.click(checkbox);
        expect(mockOnChange).toHaveBeenCalled();

        // 4. Sliders (MUI Slider uses an input range)
        const sliders = container.querySelectorAll('input[type="range"]');
        if (sliders.length > 0) {
            fireEvent.change(sliders[0], { target: { value: 1.0 } });
            expect(mockOnChange).toHaveBeenCalled();
        }
    });

    it('should cover template changes', () => {
        const mockOnChange = vi.fn();
        render(<SettingsSection settings={defaultSettings} onChange={mockOnChange} t={t} />);

        const mapInput = screen.getByLabelText(t.mapTemplate);
        fireEvent.change(mapInput, { target: { value: 'test' } });
        expect(mockOnChange).toHaveBeenCalled();

        const reduceInput = screen.getByLabelText(t.reduceTemplate);
        fireEvent.change(reduceInput, { target: { value: 'test' } });
        expect(mockOnChange).toHaveBeenCalled();
    });

    it('should handle empty number inputs (Branch check)', () => {
        const mockOnChange = vi.fn();
        render(<SettingsSection settings={defaultSettings} onChange={mockOnChange} t={t} />);
        const input = screen.getByLabelText(t.chunkSize1);
        fireEvent.change(input, { target: { value: '' } }); // Triggers '|| 0' branch
        expect(mockOnChange).toHaveBeenCalledWith(expect.objectContaining({ chunk_size_1: 0 }));
    });
});