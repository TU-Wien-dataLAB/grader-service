import * as React from 'react';
import { Typography, Button, Container, Grid, Box } from '@mui/material';
import { useNavigate, useRouteError } from 'react-router-dom';
import { storeString } from '../../services/storage.service';

export default function ErrorPage({ id }: { id: string }) {
  const error: any = useRouteError();
  const navigate = useNavigate();
  console.error(error);
  storeString(`${id}-react-router-path`, '/');

  return (
    <Container maxWidth="md" style={{ marginTop: '50px' }}>
      <Grid container spacing={2} justifyContent="center">
        <Grid size={{ xs: 6 }}>
          <Typography sx={{ mb: 2 }} variant={'h2'}>
            Sorry!
          </Typography>
          <Typography variant={'subtitle1'} sx={{ mb: 4 }}>
            An unexpected error has occurred.
          </Typography>
          <span
            style={{
              textDecoration: 'underline',
              fontWeight: 'bold'
            }}
          >
            Details
          </span>
          <Box sx={{ ml: 2 }}>
            <i>{error.statusText || error.message}</i>
          </Box>
          <p>
            <Button
              size={'small'}
              variant={'contained'}
              sx={{ mt: 1 }}
              onClick={() => navigate(-1)}
            >
              Back
            </Button>
          </p>
        </Grid>
        <Grid size={{ xs: 6 }}>
          <svg
            width="100%"
            height="auto"
            viewBox="0 0 64 64"
            xmlns="http://www.w3.org/2000/svg"
            xmlnsXlink="http://www.w3.org/1999/xlink"
            aria-hidden="true"
            role="img"
            className="iconify iconify--emojione"
            preserveAspectRatio="xMidYMid meet"
          >
            <path
              d="M62 40.3C62 46.2 48.6 51 32 51h-1l-2.7-2.7l-3 2.4c-4-.3-7.7-.9-11-1.8l-3.2-3.3l-2.2 1.5C4.6 45.3 2 42.9 2 40.3c0-5.9 13.4-10.7 30-10.7s30 4.8 30 10.7"
              fill="#63a1ba"
            ></path>
            <path
              d="M32 43.5c9.2 0 17.3 1.5 22.8 3.8c2.4-1 4.3-2.2 5.5-3.5c-4-4.2-15.2-7.2-28.4-7.2s-24.3 3-28.4 7.2c1.2 1.2 3 2.4 5.2 3.3l1.6-3.3l3.3 1.9c5.2-1.4 11.5-2.2 18.4-2.2"
              fill="#538aa5"
            ></path>
            <path
              d="M14.4 49c3.2.8 6.9 1.4 10.9 1.8l2.6-2L31 51h1c9.2 0 17.3-1.5 22.8-3.8c-5.5-2.3-13.7-3.8-22.8-3.8c-6.9 0-13.3.8-18.3 2.2c-1.7.5.7 3.4.7 3.4"
              fill="#467591"
            ></path>
            <path
              d="M26.4 16.1l-2.9.4l5 34.3c.8 0 1.7.1 2.5.1l-4.6-34.8"
              fill="#dfe9ef"
            ></path>
            <path
              d="M24.3 16.6h-2.9l3.9 34.2c1 .1 2.1.2 3.2.2l-4.2-34.4"
              fill="#b0bdc6"
            ></path>
            <path
              d="M12 32.6l11.6-3.3s1-.1 1.3.6c.3 1.1-.6 1.7-.6 1.7l-12.1 2.3l-.2-1.3"
              fill="#dfe9ef"
            ></path>
            <path
              d="M12.2 33.8L25 30.3c0 .8-.7 1.3-.7 1.3l-11.9 3.6l-.2-1.4"
              fill="#8b979e"
            ></path>
            <path
              d="M13.7 45.8l11.6-3.3s1-.1 1.3.6c.3 1.1-.6 1.7-.6 1.7L13.8 47l-.1-1.2"
              fill="#dfe9ef"
            ></path>
            <path
              d="M13.8 47l12.8-3.6c0 .8-.7 1.3-.7 1.3L14 48.3l-.2-1.3"
              fill="#8b979e"
            ></path>
            <path
              d="M10.4 19.3l-2.6.5L12 48.3c.7.2 1.5.5 2.3.7l-3.9-29.7"
              fill="#dfe9ef"
            ></path>
            <path
              d="M8.3 19.7H5.4l3.4 27.4c1 .4 2 .8 3.2 1.2L8.3 19.7"
              fill="#b0bdc6"
            ></path>
            <path fill="#333" d="M8.1 16.1l-3.6.3l.4 3.7l3.7.4l.5-2.5z"></path>
            <path fill="#484a4c" d="M10.5 16.1H8.1l.5 4.4l2.1-.8z"></path>
            <path fill="#333" d="M20.5 13.2l.4 3.8l3.6.2l.6-2.4l-1-1.8z"></path>
            <path fill="#484a4c" d="M24.1 13h2.4l.2 3.6l-2.2.6"></path>
          </svg>
        </Grid>
      </Grid>
    </Container>
  );
}
