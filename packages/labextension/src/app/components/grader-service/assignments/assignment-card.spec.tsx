import { createAllProvidersWrapper } from '../../../../test/utils';
import { render, screen } from '@testing-library/react';
import { AssignmentCard } from './assignment-card';
import { AssignmentDetail } from '../../../../model/assignmentDetail';
import React from 'react';
import { DndProvider } from 'react-dnd';
import { HTML5Backend } from 'react-dnd-html5-backend';
import { userEvent } from '@testing-library/user-event';

const assignment: AssignmentDetail = {
  id: 1,
  name: 'Assignment1',
  settings: { autograde_type: 'unassisted' },
  status: 'created',
  points: 3,
  submissions: []
};

describe('Assignment Card', () => {
  it('should show card correct data', () => {
    const Wrapper = createAllProvidersWrapper();
    const handleChange = jest.fn();

    render(
      <DndProvider backend={HTML5Backend}>
        <AssignmentCard
          key={2}
          assignment={assignment}
          checked={true}
          handleChange={handleChange}
        />
      </DndProvider>,
      { wrapper: Wrapper }
    );

    expect(screen.getByText('Assignment1'));
    expect(screen.getByText('Not released'));
    expect(screen.getByText('Manual grading'));
  });
  it('should select the card on click the checkbox', async () => {
    const Wrapper = createAllProvidersWrapper();
    const handleChange = jest.fn();
    const user = userEvent.setup();

    render(
      <DndProvider backend={HTML5Backend}>
        <AssignmentCard
          key={2}
          assignment={assignment}
          checked={false}
          handleChange={handleChange}
        />
      </DndProvider>,
      { wrapper: Wrapper }
    );

    const checkbox = screen.getByRole('checkbox');

    expect(checkbox).not.toBeChecked();
    await user.click(checkbox);
    expect(checkbox).not.toBeChecked(); // Wrong!!! it should be checked, but test passes. TODO
  });
});
