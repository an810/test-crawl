import React, { useState } from 'react';
import { useFormik } from 'formik';
import * as yup from 'yup';
import {
  Container,
  Typography,
  TextField,
  Button,
  Paper,
  Box,
  Alert,
  CircularProgress,
} from '@mui/material';
import axios from 'axios';

const validationSchema = yup.object({
  area: yup
    .number()
    .required('Area is required')
    .positive('Area must be positive'),
  bedrooms: yup
    .number()
    .required('Number of bedrooms is required')
    .integer('Must be a whole number')
    .min(0, 'Must be 0 or greater'),
  bathrooms: yup
    .number()
    .required('Number of bathrooms is required')
    .integer('Must be a whole number')
    .min(0, 'Must be 0 or greater'),
  location: yup
    .string()
    .required('Location is required'),
  property_type: yup
    .string(),
  age: yup
    .number()
    .integer('Must be a whole number')
    .min(0, 'Must be 0 or greater'),
});

function Predict() {
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const formik = useFormik({
    initialValues: {
      area: '',
      bedrooms: '',
      bathrooms: '',
      location: '',
      property_type: '',
      age: '',
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      setLoading(true);
      setError(null);
      try {
        const response = await axios.post('http://localhost:8000/predict', values);
        setResult(response.data);
      } catch (err) {
        setError(err.response?.data?.detail || 'An error occurred');
      } finally {
        setLoading(false);
      }
    },
  });

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Property Price Prediction
      </Typography>

      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <form onSubmit={formik.handleSubmit}>
          <Box sx={{ display: 'grid', gap: 2 }}>
            <TextField
              fullWidth
              id="area"
              name="area"
              label="Area (m²)"
              value={formik.values.area}
              onChange={formik.handleChange}
              error={formik.touched.area && Boolean(formik.errors.area)}
              helperText={formik.touched.area && formik.errors.area}
            />

            <TextField
              fullWidth
              id="bedrooms"
              name="bedrooms"
              label="Number of Bedrooms"
              value={formik.values.bedrooms}
              onChange={formik.handleChange}
              error={formik.touched.bedrooms && Boolean(formik.errors.bedrooms)}
              helperText={formik.touched.bedrooms && formik.errors.bedrooms}
            />

            <TextField
              fullWidth
              id="bathrooms"
              name="bathrooms"
              label="Number of Bathrooms"
              value={formik.values.bathrooms}
              onChange={formik.handleChange}
              error={formik.touched.bathrooms && Boolean(formik.errors.bathrooms)}
              helperText={formik.touched.bathrooms && formik.errors.bathrooms}
            />

            <TextField
              fullWidth
              id="location"
              name="location"
              label="Location"
              value={formik.values.location}
              onChange={formik.handleChange}
              error={formik.touched.location && Boolean(formik.errors.location)}
              helperText={formik.touched.location && formik.errors.location}
            />

            <TextField
              fullWidth
              id="property_type"
              name="property_type"
              label="Property Type (Optional)"
              value={formik.values.property_type}
              onChange={formik.handleChange}
            />

            <TextField
              fullWidth
              id="age"
              name="age"
              label="Property Age (years, Optional)"
              value={formik.values.age}
              onChange={formik.handleChange}
              error={formik.touched.age && Boolean(formik.errors.age)}
              helperText={formik.touched.age && formik.errors.age}
            />

            <Button
              color="primary"
              variant="contained"
              fullWidth
              type="submit"
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Predict Price'}
            </Button>
          </Box>
        </form>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {result && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Estimated Price: {result.estimated_price.toLocaleString()} VND
          </Alert>
        )}
      </Paper>
    </Container>
  );
}

export default Predict; 