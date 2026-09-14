import React from 'react';
import { render, screen } from '@testing-library/react';
import { ErrorBanner } from './error-banner';

describe('Error Banner states', () => {
  it('error banner shows passed props text', () => {
    render(<ErrorBanner message="Error message!!!" />);
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(screen.getByText('Error message!!!')).toBeInTheDocument();
  });
  it('error banner without props text', () => {
    render(<ErrorBanner message={null} />);
    expect(screen.getByText('Error')).toBeInTheDocument();
    expect(
      screen.getByText('Something went wrong. Please try again.')
    ).toBeInTheDocument();
  });
});
