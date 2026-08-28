import React from 'react';
import { render, screen } from '@testing-library/react';
import { createAllProvidersWrapper } from '../../../test/utils';
import { SearchField } from './search';
import { userEvent } from '@testing-library/user-event';

describe('Dashboard Component', () => {
  it('search default/empty state', async () => {
    const Wrapper = createAllProvidersWrapper();
    const user = userEvent.setup();

    render(
      <SearchField
        searchQuery={''}
        setSearchQuery={() => {}}
        placeholder="search"
      />,
      {
        wrapper: Wrapper
      }
    );

    const input = screen.getByPlaceholderText('search');
    await user.click(input);

    expect(await screen.findByText('No results found.')).toBeInTheDocument();

    //   To be continued...
    //   Need to be done fully for all cases
  });
});
