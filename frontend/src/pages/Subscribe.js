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
  FormControl,
  FormLabel,
  FormGroup,
  FormControlLabel,
  Checkbox,
} from '@mui/material';
import axios from 'axios';

const validationSchema = yup.object({
  email: yup
    .string()
    .email('Enter a valid email')
    .required('Email is required'),
});

const propertyTypes = [
  'Apartments',
  'Houses',
  'Villas',
  'Land',
  'Commercial',
];

function Subscribe() {
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [preferences, setPreferences] = useState([]);

  const formik = useFormik({
    initialValues: {
      email: '',
    },
    validationSchema: validationSchema,
    onSubmit: async (values) => {
      setLoading(true);
      setError(null);
      try {
        await axios.post('http://localhost:8000/subscribe', {
          email: values.email,
          preferences: preferences,
        });
        setSuccess(true);
        formik.resetForm();
        setPreferences([]);
      } catch (err) {
        setError(err.response?.data?.detail || 'An error occurred');
      } finally {
        setLoading(false);
      }
    },
  });

  const handlePreferenceChange = (propertyType) => {
    setPreferences((prev) =>
      prev.includes(propertyType)
        ? prev.filter((type) => type !== propertyType)
        : [...prev, propertyType]
    );
  };

  return (
    <Container maxWidth="md" sx={{ mt: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom align="center">
        Subscribe to Daily Updates
      </Typography>

      <Paper elevation={3} sx={{ p: 4, mt: 4 }}>
        <form onSubmit={formik.handleSubmit}>
          <Box sx={{ display: 'grid', gap: 3 }}>
            <TextField
              fullWidth
              id="email"
              name="email"
              label="Email Address"
              value={formik.values.email}
              onChange={formik.handleChange}
              error={formik.touched.email && Boolean(formik.errors.email)}
              helperText={formik.touched.email && formik.errors.email}
            />

            <FormControl component="fieldset">
              <FormLabel component="legend">Property Preferences</FormLabel>
              <FormGroup>
                {propertyTypes.map((type) => (
                  <FormControlLabel
                    key={type}
                    control={
                      <Checkbox
                        checked={preferences.includes(type)}
                        onChange={() => handlePreferenceChange(type)}
                      />
                    }
                    label={type}
                  />
                ))}
              </FormGroup>
            </FormControl>

            <Button
              color="primary"
              variant="contained"
              fullWidth
              type="submit"
              disabled={loading}
              sx={{ mt: 2 }}
            >
              {loading ? <CircularProgress size={24} /> : 'Subscribe'}
            </Button>
          </Box>
        </form>

        {error && (
          <Alert severity="error" sx={{ mt: 2 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mt: 2 }}>
            Successfully subscribed! You will receive daily updates about real estate content.
          </Alert>
        )}
      </Paper>
    </Container>
  );
}

export default Subscribe; 