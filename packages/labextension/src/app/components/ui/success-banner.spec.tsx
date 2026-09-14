import React from 'react';
import { render, screen } from '@testing-library/react';
import { SuccessBanner } from './success-banner';

test('success banner shows passed props text', () => {
  render(<SuccessBanner message="Success message!!!" />);
  expect(screen.getByText('Success')).toBeInTheDocument();
  expect(screen.getByText('Success message!!!')).toBeInTheDocument();
});
