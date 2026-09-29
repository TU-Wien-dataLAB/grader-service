import { render, screen } from '@testing-library/react';
import { CompleteDialog } from './complete-dialog';
import { AssignmentDetail } from '../../../../model/assignmentDetail';
import React from 'react';
import { createAllProvidersWrapper } from '../../../../test/utils';

const assignment: AssignmentDetail = {
  id: 1,
  name: 'Assignment1',
  settings: { autograde_type: 'unassisted' },
  status: 'created',
  points: 3,
  submissions: []
};

describe('Complete dialog', () => {
  it('should show correct data', async () => {
    const Wrapper = createAllProvidersWrapper();
    const setOpenDialog = jest.fn();

    render(
      <CompleteDialog
        assignment={assignment}
        lectureId={2}
        openDialog={true}
        setOpenDialog={setOpenDialog}
      />,
      { wrapper: Wrapper }
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Complete assignment'));
    const completeBtn = screen.getByRole('button', { name: 'Complete' });
    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    expect(completeBtn).toBeInTheDocument();
    expect(cancelBtn).toBeInTheDocument();
    expect(await screen.findByText('Assignment1'));
  });
});
