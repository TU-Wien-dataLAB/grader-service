import { render, screen } from '@testing-library/react';
import { AssignmentDetail } from '../../../../model/assignmentDetail';
import React from 'react';
import { createAllProvidersWrapper } from '../../../../test/utils';
import { DeleteDialog } from './delete-dialog';

const assignment: AssignmentDetail = {
  id: 1,
  name: 'Assignment1',
  settings: { autograde_type: 'unassisted' },
  status: 'created',
  points: 3,
  submissions: []
};

describe('Delete dialog', () => {
  it('should show correct data', async () => {
    const Wrapper = createAllProvidersWrapper();
    const setOpenDialog = jest.fn();

    render(
      <DeleteDialog
        assignment={assignment}
        lectureId={2}
        openDialog={true}
        setOpenDialog={setOpenDialog}
      />,
      { wrapper: Wrapper }
    );
    expect(screen.getByRole('dialog')).toBeInTheDocument();
    expect(screen.getByText('Delete assignment'));
    const completeBtn = screen.getByRole('button', {
      name: 'Delete permanently'
    });
    const cancelBtn = screen.getByRole('button', { name: 'Cancel' });
    expect(completeBtn).toBeInTheDocument();
    expect(cancelBtn).toBeInTheDocument();
    expect(await screen.findByText('Assignment1'));
  });
});
