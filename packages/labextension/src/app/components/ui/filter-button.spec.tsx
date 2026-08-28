import React from 'react';
import { render, screen } from '@testing-library/react';
import { userEvent } from '@testing-library/user-event';
import { FilterLecturesButton } from './filter-button';

describe('Dashboard Component', () => {
  it('filter button default/empty state', async () => {
    const user = userEvent.setup();
    render(<FilterLecturesButton filterBy="" setFilterBy={() => {}} />);
    const trigger = screen.getByTestId('filter-btn');

    // state before user click the button and open the options
    expect(screen.queryByRole('menu')).not.toBeInTheDocument();
    expect(trigger).toHaveTextContent('Filter');

    await user.click(trigger);

    // state after button clicked and opened options
    expect(await screen.findByText(/Status/i)).toBeInTheDocument();
    expect(
      await screen.findByRole('menuitem', { name: 'Active' })
    ).toBeInTheDocument();
    expect(
      screen.getByRole('menuitem', { name: 'Completed' })
    ).toBeInTheDocument();
  });
});
