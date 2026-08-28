import React from 'react';
import { render, screen } from '@testing-library/react';
import { createAllProvidersWrapper } from '../../../test/utils';
import { Dashboard } from './dashboard';

describe('Dashboard Component', () => {
  it('should render the correct label natively', () => {
    const Wrapper = createAllProvidersWrapper();

    render(<Dashboard />, { wrapper: Wrapper });

    expect(screen.getByText(/Courses/)).toBeInTheDocument();
  });

//   To be continued
});
