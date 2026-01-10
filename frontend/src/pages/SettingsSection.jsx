import React from 'react';
import {
  Box,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Slider,
  Typography,
  Switch,
  FormControlLabel
} from '@mui/material';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import SettingsIcon from '@mui/icons-material/Settings';
const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#6366f1' },
  },
});

function SettingsSection({ settings, onChange }) {
  const handleChange = (key, value) => {
    const newSettings = { ...settings, [key]: value };
    onChange(newSettings);
    console.log("Settings Updated:", newSettings);
  };

  return (
    <ThemeProvider theme={darkTheme}>
      <Box className="settings-container" sx={{ width: '100%', maxWidth: 800, mx: 'auto', p: 2 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 4 }}>
          <SettingsIcon sx={{ fontSize: 32, color: 'var(--primary)' }} />
          <Typography variant="h4" sx={{ fontWeight: 800, background: 'linear-gradient(45deg, var(--primary), var(--secondary))', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
            設定參數
          </Typography>
        </Box>

        <Box className="section settings-section" sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
          <FormControl fullWidth>
            <TextField
              labelId="model-select-label"
              label="Model"
              type="text"
              value={settings.model}
              onChange={(e) => handleChange('model', e.target.value)}
              slotProps={{ input: { sx: { borderRadius: '12px', padding: '10px 12px' } } }}
            />
          </FormControl>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 2 }}>
            <TextField
              label="Chunk Size 1"
              type="number"
              value={settings.chunk_size_1}
              onChange={(e) => handleChange('chunk_size_1', parseInt(e.target.value) || 0)}
              slotProps={{ input: { sx: { borderRadius: '12px', padding: '10px 12px' } } }}
            />
            <TextField
              label="Chunk Size 2"
              type="number"
              value={settings.chunk_size_2}
              onChange={(e) => handleChange('chunk_size_2', parseInt(e.target.value) || 0)}
              slotProps={{ input: { sx: { borderRadius: '12px', padding: '10px 12px' } } }}
            />
          </Box>


          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
            <TextField
              label="Token Max"
              type="number"
              value={settings.token_max}
              onChange={(e) => handleChange('token_max', parseInt(e.target.value) || 0)}
              slotProps={{ input: { sx: { borderRadius: '12px', padding: '10px 12px', fontSize: '16px' } } }}
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

        <Box sx={{ px: 1 }}>
          <Typography gutterBottom variant="caption">Reduce 溫度 (Reduce Temperature): {settings.reduce_temperature}</Typography>
          <Slider
            value={settings.reduce_temperature}
            min={0}
            max={2}
            step={0.1}
            marks
            valueLabelDisplay="auto"
            onChange={(e, val) => handleChange('reduce_temperature', val)}
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
                <MenuItem value="map">Map-Reduce</MenuItem>
                <MenuItem value="nomap">NoMap-Reduce</MenuItem>
                <MenuItem value="original">Original</MenuItem>
              </Select>
            </FormControl>
          </Box>

          <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Map Template (可選)"
              multiline
              rows={4}
              value={settings.map_temple}
              onChange={(e) => handleChange('map_temple', e.target.value)}
              placeholder="留空則使用預設模板..."
              slotProps={{ input: { sx: { borderRadius: '12px' } } }}
            />
            <TextField
              label="Reduce Template (可選)"
              multiline
              rows={4}
              value={settings.reduce_temple}
              onChange={(e) => handleChange('reduce_temple', e.target.value)}
              placeholder="留空則使用預設模板..."
              slotProps={{ input: { sx: { borderRadius: '12px' } } }}
            />
          </Box>

          <Box sx={{ display: 'grid', gridTemplateColumns: '1fr', gap: 2 }}>
            <FormControlLabel
              control={
                <Switch
                  checked={settings.test_mode}
                  onChange={(e) => handleChange('test_mode', e.target.checked)}
                  color="primary"
                />
              }
              label={
                <Box>
                  <Typography variant="body1" sx={{ color: 'var(--text-main)' }}>測試模式 (Test Mode)</Typography>
                  <Typography variant="caption" sx={{ color: 'rgba(255,255,255,0.5)' }}>開啟後將不消耗 API Token，僅回傳測試文字並存入資料庫</Typography>
                </Box>
              }
            />
          </Box>
        </Box>
      </Box>
    </ThemeProvider>

  );
}


export default SettingsSection;