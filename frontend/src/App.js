import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import Predict from './pages/Predict';
import Subscribe from './pages/Subscribe';
import Map from './pages/Map';
import VisualizationsPage from './pages/Visualizations';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/predict" element={<Predict />} />
          <Route path="/subscribe" element={<Subscribe />} />
          <Route path="/map" element={<Map />} />
          <Route path="/visualizations" element={<VisualizationsPage />} />
        </Routes>
      </Router>
    </ThemeProvider>
  );
}

export default App;