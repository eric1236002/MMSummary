import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import InputSection from '../components/InputSection';
import { translations } from '../translations';

describe('InputSection Component', () => {
    const t = translations.en;

    it('should render upload title', () => {
        render(<InputSection onTextLoad={vi.fn()} t={t} />);
        expect(screen.getByText(t.uploadTitle)).toBeDefined();
    });

    it('should show selected filename and call onTextLoad when a file is uploaded', async () => {
        const mockOnTextLoad = vi.fn();
        render(<InputSection onTextLoad={mockOnTextLoad} t={t} />);

        const file = new File(['hello world'], 'test.txt', { type: 'text/plain' });
        const input = screen.getByLabelText(new RegExp(t.chooseFile, 'i')) as HTMLInputElement;

        // Simulate file selection
        fireEvent.change(input, { target: { files: [file] } });

        // Check if filename is displayed
        expect(await screen.findByText(new RegExp(file.name, 'i'))).toBeDefined();

        // Wait for FileReader to complete and callback to be called
        await waitFor(() => {
            expect(mockOnTextLoad).toHaveBeenCalledWith('hello world');
        });
    });
});
