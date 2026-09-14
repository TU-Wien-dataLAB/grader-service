import React from 'react';
import { fireEvent, render, screen } from '@testing-library/react';
import { EditLectureDialog } from './edit-lecture-dialog';
import { createAllProvidersWrapper } from '../../../../test/utils';
import { useUpdateLecture } from '../../../hooks/lecture/update-lecture-hook';
import { userEvent } from '@testing-library/user-event';

jest.mock('../../../hooks/lecture/update-lecture-hook');
const mockedUseUpdateLecture = jest.mocked(useUpdateLecture);

const mockLecture = {
  id: 1,
  code: 'CS101',
  name: 'Intro to CS',
  complete: false
};

const mockMutateAsync = jest.fn();

beforeEach(() => {
  jest.clearAllMocks();

  mockedUseUpdateLecture.mockReturnValue({
    mutateLecture: {
      mutateAsync: mockMutateAsync,
      mutate: jest.fn()
    } as any
  });
});

describe('Edit Lecture Dialog', () => {
  test('should open dialog on click edit pencil icon and all other form fields with action buttons', async () => {
    const Wrapper = createAllProvidersWrapper();
    const user = userEvent.setup({ delay: null, pointerEventsCheck: 0 });
    mockMutateAsync.mockResolvedValue({});

    render(<EditLectureDialog lecture={mockLecture} />, { wrapper: Wrapper });

    const triggerButton = screen.getByTestId('edit-dialog-trigger-btn');
    fireEvent.click(triggerButton);

    expect(screen.getByText('Edit course')).toBeInTheDocument();

    const nameInput = screen.getByLabelText('Name*');
    await user.clear(nameInput);

    await user.type(nameInput, 'New Lecture Name');

    const statusSelectInput = screen.getByRole('combobox');
    await user.click(statusSelectInput);

    const completedOption = await screen.findByRole('option', {
      name: 'Completed'
    });
    const activeOption = await screen.findByRole('option', { name: 'Active' });

    expect(completedOption).toBeInTheDocument();
    expect(activeOption).toBeInTheDocument();

    fireEvent.click(completedOption);

    //   need to finish with select component
  }, 50000);
});
