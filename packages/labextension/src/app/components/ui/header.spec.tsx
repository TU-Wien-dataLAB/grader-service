import React from 'react';
import { render, screen } from '@testing-library/react';
import { createAllProvidersWrapper } from '../../../test/utils';
import { Header } from './header';

describe('Dashboard Component', () => {
  it('should render the correct label natively', () => {
    const Wrapper = createAllProvidersWrapper();

    render(<Header />, { wrapper: Wrapper });

    expect(screen.getByText(/Hello,/)).toBeInTheDocument();
  });
});
