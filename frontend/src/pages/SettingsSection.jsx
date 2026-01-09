import React from 'react';
import { 
  Box, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem, 
  TextField, 
  Slider, 
  Typography 
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';

// 建立一個深色主題來適應您的背景
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#6366f1' },
  },
});

function SettingsSection({ settings, onChange }) {
  const handleChange = (key, value) => {
    onChange({ ...settings, [key]: value });
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Box className="section settings-section" sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
        <h2>設定參數</h2>

        {/* 1. Model 選擇器 (MUI Select) */}
        <FormControl fullWidth>
          <TextField 
            labelId="model-select-label"
            label="Model"
            type="text"
            value={settings.model}
            onChange={(e) => handleChange('model', e.target.value)}
            slotProps={{ input: { sx: { borderRadius: '12px' , padding: '10px 12px' } } }}
          />
        </FormControl>

        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
          <TextField 
            label="Chunk Size 1"
            type="number"
            value={settings.chunk_size_1}
            onChange={(e) => handleChange('chunk_size_1', parseInt(e.target.value) || 0)}
            slotProps={{ input: { sx: { borderRadius: '12px' , padding: '10px 12px' } } }}
          />
          <TextField 
            label="Chunk Size 2"
            type="number"
            value={settings.chunk_size_2}
            onChange={(e) => handleChange('chunk_size_2', parseInt(e.target.value) || 0)}
            slotProps={{ input: { sx: { borderRadius: '12px' , padding: '10px 12px' } } }}
          />
        </Box>

        
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
          <TextField 
            label="Token Max"
            type="number"
            value={settings.token_max}
            onChange={(e) => handleChange('token_max', parseInt(e.target.value) || 0)}
            slotProps={{ input: { sx: { borderRadius: '12px' , padding: '10px 12px' ,fontSize: '16px'   } } }}
          />
        </Box>

        <Box sx={{ px: 1 }}>
          <Typography gutterBottom variant="caption">溫度 (Temperature): {settings.temperature}</Typography>
          <Slider
            value={settings.temperature}
            min={0}
            max={2}
            step={0.1}
            marks
            valueLabelDisplay="auto"
            onChange={(e, val) => handleChange('temperature', val)}
          />
        </Box>

        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
          <FormControl fullWidth>
            <InputLabel id="strategy-select-label">Strategy</InputLabel>
            <Select
              labelId="strategy-select-label"
              label="Strategy"
              value={settings.strategy}
              onChange={(e) => handleChange('strategy', e.target.value)}
              sx={{ borderRadius: '12px' }}
            >
              <MenuItem value="map">Map</MenuItem>
              <MenuItem value="nomap">NoMap</MenuItem>
              <MenuItem value="original">Original</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Box>
    </ThemeProvider>
  );
}

export default SettingsSection;