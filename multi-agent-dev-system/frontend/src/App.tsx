import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { Container, Typography, Box } from '@mui/material';

const theme = createTheme({
  palette: {
    mode: 'dark',
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h3" component="h1" gutterBottom>
            Multi-Agent Development System
          </Typography>
          <Typography variant="h6" component="h2" gutterBottom>
            AI-Powered Software Development Pipeline
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;
