import React, { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';
import { Box, Typography, CircularProgress, Grid, Paper, Alert } from '@mui/material';

const Visualizations = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchData = async () => {
      try {
        console.log('Fetching visualization data...');
        const response = await fetch('http://localhost:8000/api/visualizations');
        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch visualization data');
        }
        const visualizationData = await response.json();
        console.log('Received data:', visualizationData);
        setData(visualizationData);
      } catch (error) {
        console.error('Error fetching visualization data:', error);
        setError(error.message);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="error">
          Error loading visualizations: {error}
        </Alert>
      </Box>
    );
  }

  if (!data) {
    return (
      <Box sx={{ p: 3 }}>
        <Alert severity="warning">
          No visualization data available
        </Alert>
      </Box>
    );
  }

  const renderPlot = (plotData, height = 400) => {
    if (!plotData) {
      console.warn('Missing plot data');
      return null;
    }

    console.log('Rendering plot:', plotData.type);

    const layout = {
      height,
      margin: { t: 40, r: 20, l: 60, b: 40 },
      title: {
        text: plotData.title,
        font: { size: 16 }
      },
      xaxis: { 
        title: plotData.xaxis_title,
        automargin: true
      },
      yaxis: { 
        title: plotData.yaxis_title,
        automargin: true
      },
      showlegend: true,
      autosize: true,
      paper_bgcolor: 'rgba(0,0,0,0)',
      plot_bgcolor: 'rgba(0,0,0,0)',
    };

    const config = {
      responsive: true,
      displayModeBar: true,
      displaylogo: false,
      modeBarButtonsToRemove: ['lasso2d', 'select2d'],
    };

    switch (plotData.type) {
      case 'histogram':
        return (
          <Plot
            data={[
              {
                type: 'histogram',
                x: plotData.x,
                nbinsx: plotData.nbins,
                marker: {
                  color: plotData.color
                }
              },
            ]}
            layout={layout}
            config={config}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        );

      case 'pie':
        return (
          <Plot
            data={[
              {
                type: 'pie',
                labels: plotData.labels,
                values: plotData.values,
                marker: {
                  colors: plotData.colors
                },
                textinfo: 'label+percent',
                textposition: 'outside',
                automargin: true,
                domain: {
                  x: [0.1, 0.9],
                  y: [0.1, 0.9]
                }
              },
            ]}
            layout={{
              ...layout,
              height: height,
              margin: { t: 40, r: 20, l: 20, b: 40 },
              showlegend: true,
              legend: {
                orientation: 'h',
                y: -0.1
              }
            }}
            config={config}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        );

      case 'bar':
        return (
          <Plot
            data={[
              {
                type: 'bar',
                x: plotData.x,
                y: plotData.y,
                marker: {
                  color: plotData.color
                }
              },
            ]}
            layout={{
              ...layout,
              xaxis: { 
                ...layout.xaxis,
                tickangle: -45,
                automargin: true
              }
            }}
            config={config}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        );

      case 'scatter':
        // Create separate traces for each property type
        const scatterTraces = plotData.property_types.map(type => ({
          type: 'scatter',
          mode: 'markers',
          x: plotData.x.filter((_, i) => plotData.hover_data.property_type[i] === type),
          y: plotData.y.filter((_, i) => plotData.hover_data.property_type[i] === type),
          marker: { 
            color: plotData.colors[type],
            size: 8,
            opacity: 0.7
          },
          text: plotData.hover_data.title.filter((_, i) => plotData.hover_data.property_type[i] === type),
          customdata: plotData.hover_data.district
            .filter((_, i) => plotData.hover_data.property_type[i] === type)
            .map((district, i) => [district, type]),
          hovertemplate: 
            '<b>%{text}</b><br>' +
            'Area: %{x:.0f} m²<br>' +
            'Price: %{y:.1f} tỷ VND<br>' +
            'District: %{customdata[0]}<br>' +
            'Type: %{customdata[1]}<extra></extra>',
          hoverlabel: {
            bgcolor: 'white',
            font: { size: 12 }
          },
          name: type,
          showlegend: true
        }));

        return (
          <Plot
            data={scatterTraces}
            layout={{
              ...layout,
              showlegend: true,
              legend: {
                title: {
                  text: 'Property Type',
                  font: { size: 14 }
                },
                orientation: 'v',
                y: 0.5,
                x: 1.02,
                xanchor: 'left',
                yanchor: 'middle',
                bgcolor: 'rgba(255, 255, 255, 0.8)',
                bordercolor: 'rgba(0, 0, 0, 0.2)',
                borderwidth: 1
              }
            }}
            config={config}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        );

      case 'scattermapbox':
        return (
        <Plot
            data={[
              {
                type: 'scattermapbox',
                lat: plotData.lat,
                lon: plotData.lon,
                mode: 'markers',
                marker: {
                  size: plotData.size,
                  color: plotData.color,
                  opacity: 0.7,
                },
                text: plotData.hover_name,
                customdata: plotData.hover_data.district.map((_, i) => [
                    plotData.hover_data.district[i],
                    plotData.hover_data.price[i],
                    plotData.hover_data.area[i],
                    plotData.hover_data.property_type[i],
                ]),                  
                hovertemplate: 
                  '<b>%{text}</b><br>' +
                  'District: %{customdata[0]}<br>' +
                  'Price: %{customdata[1]:.1f} tỷ VND<br>' +
                  'Area: %{customdata[2]:.0f} m²<br>' +
                  'Type: %{customdata[3]}<extra></extra>',
                hoverlabel: {
                  bgcolor: 'white',
                  font: { size: 12 }
                }
              },
            ]}
        // // Create separate traces for each property type
        // const mapboxTraces = plotData.property_types.map(type => {
        //   const typeIndices = plotData.hover_data.property_type.map((pt, i) => pt === type ? i : -1).filter(i => i !== -1);
        //   return {
        //     type: 'scattermapbox',
        //     lat: typeIndices.map(i => plotData.lat[i]),
        //     lon: typeIndices.map(i => plotData.lon[i]),
        //     mode: 'markers',
        //     marker: {
        //       size: typeIndices.map(i => plotData.size[i]),
        //       color: plotData.colors[type],
        //       opacity: 0.7,
        //     },
        //     text: typeIndices.map(i => plotData.hover_name[i]),
        //     customdata: typeIndices.map(i => [
        //       plotData.hover_data.district[i],
        //       plotData.hover_data.price[i],
        //       plotData.hover_data.area[i],
        //       type
        //     ]),
        //     hovertemplate: 
        //       '<b>%{text}</b><br>' +
        //       'District: %{customdata[0]}<br>' +
        //       'Price: %{customdata[1]:.1f} tỷ VND<br>' +
        //       'Area: %{customdata[2]:.0f} m²<br>' +
        //       'Type: %{customdata[3]}<extra></extra>',
        //     hoverlabel: {
        //       bgcolor: 'white',
        //       font: { size: 12 }
        //     },
        //     name: type,
        //     showlegend: true
        //   };
        // });

        // return (
        //   <Plot
        //     data={mapboxTraces}
            layout={{
              ...layout,
              mapbox: {
                style: 'open-street-map',
                center: { lat: 21.0285, lon: 105.8542 },
                zoom: plotData.zoom,
              },
              margin: { r: 0, t: 40, l: 0, b: 40 },
              showlegend: true,
              legend: {
                title: {
                  text: 'Property Type',
                  font: { size: 14 }
                },
                orientation: 'v',
                y: 0.5,
                x: 1.02,
                xanchor: 'left',
                yanchor: 'middle',
                bgcolor: 'rgba(255, 255, 255, 0.8)',
                bordercolor: 'rgba(0, 0, 0, 0.2)',
                borderwidth: 1
              }
            }}
            config={config}
            // config={{
            //   ...config,
            //   mapboxAccessToken: 'pk.eyJ1IjoiZHVjYW4iLCJhIjoiY2x2M2J0Z2RqMDF0YzJqbnR2Z2J0Z2RqIn0.2J0Z2RqMDF0YzJqbnR2Z2J0Z2Rq'
            // }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        );

      case 'choroplethmapbox':
        return (
          <Plot
            data={[
              {
                type: 'choroplethmapbox',
                geojson: plotData.geojson,
                locations: plotData.locations,
                z: plotData.z,
                colorscale: plotData.colorscale,
                marker: plotData.marker,
                colorbar: plotData.colorbar,
              },
              {
                type: 'scattermapbox',
                lat: plotData.district_labels.lat,
                lon: plotData.district_labels.lon,
                mode: 'text',
                text: plotData.district_labels.text,
                textfont: { size: 11, color: 'black' },
                hoverinfo: 'skip',
              },
            ]}
            layout={{
              ...layout,
              mapbox: {
                style: 'open-street-map',
                center: plotData.center,
                zoom: plotData.zoom,
              },
              margin: { r: 0, t: 40, l: 0, b: 0 },
            }}
            config={{
              ...config,
              mapboxAccessToken: 'pk.eyJ1IjoiZHVjYW4iLCJhIjoiY2x2M2J0Z2RqMDF0YzJqbnR2Z2J0Z2RqIn0.2J0Z2RqMDF0YzJqbnR2Z2J0Z2Rq'
            }}
            style={{ width: '100%', height: '100%' }}
            useResizeHandler={true}
          />
        );

      default:
        console.warn('Unknown plot type:', plotData.type);
        return null;
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        Real Estate Data Visualizations
      </Typography>
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: 400, overflow: 'hidden' }}>
            {renderPlot(data?.price_distribution)}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: 400, overflow: 'hidden' }}>
            {renderPlot(data?.area_distribution)}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: 400, overflow: 'hidden' }}>
            {renderPlot(data?.property_type_distribution)}
          </Paper>
        </Grid>
        <Grid item xs={12} md={6}>
          <Paper elevation={3} sx={{ p: 2, height: 400, overflow: 'hidden' }}>
            {renderPlot(data?.district_distribution)}
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 2, height: 500, overflow: 'hidden' }}>
            {renderPlot(data?.price_area_scatter, 500)}
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 2, height: 600, overflow: 'hidden' }}>
            {renderPlot(data?.listings_map, 600)}
          </Paper>
        </Grid>
        <Grid item xs={12}>
          <Paper elevation={3} sx={{ p: 2, height: 600, overflow: 'hidden' }}>
            {renderPlot(data?.choropleth_map, 600)}
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Visualizations;
