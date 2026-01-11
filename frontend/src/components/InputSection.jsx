import React, { useState } from 'react';
import { Box, Typography, Button } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import { styled } from '@mui/material/styles';

const VisuallyHiddenInput = styled('input')({
    clip: 'rect(0 0 0 0)',
    clipPath: 'inset(50%)',
    height: 1,
    overflow: 'hidden',
    position: 'absolute',
    bottom: 0,
    left: 0,
    whiteSpace: 'nowrap',
    width: 1,
});

function InputSection({ onTextLoad, t }) {
    const [fileName, setFileName] = useState("");

    const handleFileChange = (e) => {
        const file = e.target.files[0];
        if (!file) return;

        setFileName(file.name);
        const reader = new FileReader();
        reader.onload = (event) => {
            const text = event.target.result;
            onTextLoad(text);
        };

        reader.readAsText(file);
        console.log("File selected:", file.name);
    };

    return (
        <Box className="input-content-wrapper" sx={{ textAlign: 'center', p: 4, border: '2px dashed rgba(255,255,255,0.1)', borderRadius: '20px' }}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 700, color: 'var(--text-main)' }}>
                {t.uploadTitle}
            </Typography>

            <Button
                component="label"
                variant="contained"
                startIcon={<CloudUploadIcon />}
                sx={{
                    bgcolor: 'var(--primary)',
                    '&:hover': { bgcolor: 'var(--secondary)' },
                    borderRadius: '12px',
                    px: 4,
                    py: 1.5,
                    textTransform: 'none',
                    fontSize: '1rem'
                }}
            >
                {t.chooseFile}
                <VisuallyHiddenInput
                    type="file"
                    accept=".txt,.md"
                    onChange={handleFileChange}
                />
            </Button>

            {fileName && (
                <Typography variant="body2" sx={{ mt: 2, color: 'var(--primary)', fontWeight: 600 }}>
                    {t.selectedFile}{fileName}
                </Typography>
            )}

            <Typography className="hint" variant="caption" sx={{ display: 'block', mt: 2, color: 'rgba(255,255,255,0.5)' }}>
                {t.hintFile}
            </Typography>
        </Box>
    );
}

export default InputSection;
