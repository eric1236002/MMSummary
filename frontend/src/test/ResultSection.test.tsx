import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import React from 'react';
import ResultSection from '../components/ResultSection';
import { translations } from '../translations';

describe('ResultSection Component', () => {
    const t = translations.en;

    it('should show placeholder text when no result and not loading', () => {
        const result = { summary: "", processing_time: 0 };
        render(<ResultSection result={result} loading={false} t={t} />);
        expect(screen.getByText(t.placeholderResult)).toBeDefined();
    });

    it('should show loading spinner and text when loading', () => {
        const result = { summary: "", processing_time: 0 };
        render(<ResultSection result={result} loading={true} t={t} />);
        expect(screen.getByText(t.summarizing)).toBeDefined();
    });

    it('should show summary text and processing time when result is present', () => {
        const result = { summary: "# My Summary\nThis is a test.", processing_time: 5.5 };
        render(<ResultSection result={result} loading={false} t={t} />);
        
        expect(screen.getByText('My Summary')).toBeDefined();
        expect(screen.getByText(/5.5s/)).toBeDefined();
    });

    it('should copy summary to clipboard and show alert when copy button is clicked', async () => {
        const result = { summary: "Content to copy", processing_time: 5.5 };
        render(<ResultSection result={result} loading={false} t={t} />);

        const copyButton = screen.getByRole('button', { name: t.copy });
        fireEvent.click(copyButton);

        expect(navigator.clipboard.writeText).toHaveBeenCalledWith("Content to copy");
        
        expect(window.alert).toHaveBeenCalledWith(t.copySuccess);
    });

    it('should trigger download when download button is clicked', () => {
        const result = { summary: "Markdown Content", processing_time: 5.5 };
        render(<ResultSection result={result} loading={false} t={t} />);

        const downloadButton = screen.getByRole('button', { name: t.saveSummary });
        fireEvent.click(downloadButton);

        expect(window.URL.createObjectURL).toHaveBeenCalled();
    });
});
