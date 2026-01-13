import { describe, it, expect, vi } from 'vitest';
import axios from 'axios';

vi.mock('axios');

const mockedAxios = vi.mocked(axios);

describe('API outgoing requests', () => {
    it('should send correct parameters when handleSummarize is called', async () => {
        mockedAxios.post.mockResolvedValue({
            data: { summary: 'Fake Summary', processing_time: 1.5 },
            status: 200,
            statusText: 'OK',
            headers: {},
            config: {}
        } as any);

        const samplePayload = {
            text: "Hello World",
            model: "google/gemma-3-27b-it:free",
            temperature: 0.0
        };

        await mockedAxios.post("/api/summarize", samplePayload);

        expect(mockedAxios.post).toHaveBeenCalledWith(
            "/api/summarize",
            expect.objectContaining({
                text: "Hello World",
                model: "google/gemma-3-27b-it:free"
            })
        );
    });
});