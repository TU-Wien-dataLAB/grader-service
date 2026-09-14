import { userEvent } from '@testing-library/user-event';
import { render, screen } from '@testing-library/react';
import { AssignmentActions } from './assignment-actions';
import React from 'react';
import { createAllProvidersWrapper } from '../../../../test/utils';

describe('AssignmentActions', () => {
  it('shows the correct actions for a created assignment', async () => {
    const Wrapper = createAllProvidersWrapper();
    const user = userEvent.setup();

    render(
      <AssignmentActions
        assignment={{
          status: 'created'
        }}
      />,
      { wrapper: Wrapper }
    );

    await user.click(screen.getByTestId('option-btn'));

    expect(screen.getByText('Edit')).toBeInTheDocument();
    expect(screen.getByText('Release')).toBeInTheDocument();
    expect(screen.getByText('Delete')).toBeInTheDocument();

    expect(screen.getByText('Undo release')).not.toBeVisible();
    expect(screen.getByText('Complete')).not.toBeVisible();
    expect(screen.getByText('Undo Complete')).not.toBeVisible();
  });
});
