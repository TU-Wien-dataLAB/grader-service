import React from 'react';
import { render, screen } from '@testing-library/react';
import { createAllProvidersWrapper } from '../../../test/utils';
import { Header } from './header';
import { getCurrentUser } from '../../../services/user.service';

jest.mock('../../../services/user.service');

const mockedGetCurrentUser = jest.mocked(getCurrentUser);

test('should render the correct label with username natively', async () => {
  const Wrapper = createAllProvidersWrapper();
  mockedGetCurrentUser.mockResolvedValue('Mark');

  render(<Header />, { wrapper: Wrapper });

  expect(await screen.findByText('Hello, Mark')).toBeInTheDocument();
});
