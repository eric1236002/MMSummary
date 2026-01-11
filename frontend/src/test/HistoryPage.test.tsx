import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { describe, it, expect, vi, beforeEach } from 'vitest';
import React from 'react';
import axios from 'axios';
import HistoryPage from '../pages/HistoryPage';
import { translations } from '../translations';

vi.mock('axios');
const mockedAxios = vi.mocked(axios);


window.confirm = vi.fn();

describe('HistoryPage Component', () => {
    const t = translations.en;

    beforeEach(() => {
        vi.clearAllMocks();
    });

    it('should show empty state message when no history exists', async () => {
        mockedAxios.get.mockResolvedValue({ data: [] } as any);

        render(<HistoryPage t={t} />);

        expect(await screen.findByText(t.noHistory)).toBeDefined();
    });

    it('should show history items when API returns data', async () => {
        const mockData = [
            {
                id: "1",
                summary: "Test Summary 1",
                model: "gpt-4",
                processing_time: 10.2,
                created_at: "2024-01-01 12:00:00",
                original_text: "Original content 1"
            }
        ];
        mockedAxios.get.mockResolvedValue({ data: mockData } as any);

        render(<HistoryPage t={t} />);

        expect(await screen.findByText("Test Summary 1")).toBeDefined();
        expect(screen.getByText("gpt-4")).toBeDefined();
        expect(screen.getByText(/10.2s/)).toBeDefined();
    });

    it('should handle delete record', async () => {
        const mockData = [{ id: "1", summary: "Summary", model: "m", processing_time: 1, created_at: "t", original_text: "o" }];
        mockedAxios.get.mockResolvedValue({ data: mockData } as any);
        mockedAxios.delete.mockResolvedValue({ data: { status: "ok" } } as any);
        vi.mocked(window.confirm).mockReturnValue(true);

        render(<HistoryPage t={t} />);

        // 等待資料載入
        const deleteButton = await screen.findByRole('button', { name: t.delete });
        fireEvent.click(deleteButton);

        expect(window.confirm).toHaveBeenCalledWith(t.confirm_delete);
        expect(mockedAxios.delete).toHaveBeenCalledWith("http://127.0.0.1:8001/history/1");
        await waitFor(() => {
            expect(window.alert).toHaveBeenCalledWith(t.deleteSuccess);
        });
    });

    it('should handle copy summary', async () => {
        const mockData = [{ id: "1", summary: "Test Content 123", model: "m", processing_time: 1, created_at: "t", original_text: "o" }];
        mockedAxios.get.mockResolvedValue({ data: mockData } as any);

        render(<HistoryPage t={t} />);

        const copyButton = await screen.findByRole('button', { name: t.copy });
        fireEvent.click(copyButton);

        expect(navigator.clipboard.writeText).toHaveBeenCalledWith("Test Content 123");
        expect(window.alert).toHaveBeenCalledWith(t.copySuccess);
    });

    it('should handle download summary', async () => {
        const mockData = [{ id: "1", summary: "Content", model: "m", processing_time: 1, created_at: "t", original_text: "o" }];
        mockedAxios.get.mockResolvedValue({ data: mockData } as any);

        render(<HistoryPage t={t} />);

        const downloadButton = await screen.findByRole('button', { name: t.downloadName });
        fireEvent.click(downloadButton);

        expect(window.URL.createObjectURL).toHaveBeenCalled();
    });
});
