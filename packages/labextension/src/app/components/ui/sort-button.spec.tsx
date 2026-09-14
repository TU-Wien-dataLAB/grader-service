import React from 'react';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { SortButton } from './sort-button';

test('should show correct sort options', async () => {
  const user = userEvent.setup();
  render(<SortButton sortBy={{ key: '', dir: '' }} setSortBy={() => {}} />);
  const trigger = screen.getByTestId('sort-btn');

  expect(screen.queryByRole('menu')).not.toBeInTheDocument();
  expect(trigger).toHaveTextContent('Sort');

  await user.click(trigger);

  expect(
    await screen.findByRole('menuitemradio', { name: 'Date: new to old' })
  ).toBeInTheDocument();
  expect(
    screen.getByRole('menuitemradio', { name: 'Date: old to new' })
  ).toBeInTheDocument();
  expect(
    screen.getByRole('menuitemradio', { name: 'Title: A-Z' })
  ).toBeInTheDocument();
  expect(
    screen.getByRole('menuitemradio', { name: 'Title: Z-A' })
  ).toBeInTheDocument();
});
