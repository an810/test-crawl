import React from 'react';
import { Link as RouterLink } from 'react-router-dom';
import {
  Container,
  Typography,
  Grid,
  Card,
  CardContent,
  CardActions,
  Button,
  Box,
} from '@mui/material';
import CalculateIcon from '@mui/icons-material/Calculate';
import NotificationsIcon from '@mui/icons-material/Notifications';

function Home() {
  return (
    <Container maxWidth="lg" sx={{ mt: 4 }}>
      <Box textAlign="center" mb={6}>
        <Typography variant="h3" component="h1" gutterBottom>
          Welcome to Real Estate Bot
        </Typography>
        <Typography variant="h6" color="text.secondary" paragraph>
          Your AI-powered real estate assistant
        </Typography>
      </Box>

      <Grid container spacing={4}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Price Prediction
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Get accurate price estimates for properties based on various factors
                including area, location, number of bedrooms, and more.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                component={RouterLink}
                to="/predict"
                startIcon={<CalculateIcon />}
              >
                Try Prediction
              </Button>
            </CardActions>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h5" component="h2" gutterBottom>
                Daily Updates
              </Typography>
              <Typography variant="body1" color="text.secondary">
                Subscribe to receive daily real estate news and personalized
                property recommendations based on your preferences.
              </Typography>
            </CardContent>
            <CardActions>
              <Button
                size="large"
                component={RouterLink}
                to="/subscribe"
                startIcon={<NotificationsIcon />}
              >
                Subscribe Now
              </Button>
            </CardActions>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
}

export default Home; 