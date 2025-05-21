import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { Box, Typography, CircularProgress } from '@mui/material';

const MapVisualization = () => {
  const [mapData, setMapData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch the map data from your backend
    const fetchMapData = async () => {
      try {
        const response = await fetch('/api/map-data');
        const data = await response.json();
        setMapData(data);
      } catch (error) {
        console.error('Error fetching map data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchMapData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Real Estate Price Map
      </Typography>
      <Box sx={{ height: '600px', width: '100%' }}>
        <Plot
          data={mapData?.data || []}
          layout={{
            mapbox: {
              style: 'open-street-map',
              center: { lat: 21.0285, lon: 105.8542 },
              zoom: 9
            },
            margin: { r: 0, t: 40, l: 0, b: 0 },
            height: 600,
            title: 'Average Real Estate Price by District (tỷ VND)',
            showlegend: false
          }}
          config={{ responsive: true }}
          style={{ width: '100%', height: '100%' }}
        />
      </Box>
    </Box>
  );
};

export default MapVisualization;
