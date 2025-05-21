import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Container,
} from '@mui/material';
import HomeIcon from '@mui/icons-material/Home';
import CalculateIcon from '@mui/icons-material/Calculate';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MapIcon from '@mui/icons-material/Map';
import BarChartIcon from '@mui/icons-material/BarChart';

function Navbar() {
  return (
    <AppBar position="static">
      <Container maxWidth="lg">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Real Estate Bot
          </Typography>
          <Button
            color="inherit"
            component={RouterLink}
            to="/"
            startIcon={<HomeIcon />}
          >
            Home
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/visualizations"
            startIcon={<BarChartIcon />}
          >
            Visualizations
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/map"
            startIcon={<MapIcon />}
          >
            Map
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/predict"
            startIcon={<CalculateIcon />}
          >
            Predict Price
          </Button>
          <Button
            color="inherit"
            component={RouterLink}
            to="/subscribe"
            startIcon={<NotificationsIcon />}
          >
            Subscribe
          </Button>
        </Toolbar>
      </Container>
    </AppBar>
  );
}

export default Navbar; 