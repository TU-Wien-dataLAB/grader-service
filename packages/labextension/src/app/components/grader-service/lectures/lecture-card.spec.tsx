import { render, screen } from '@testing-library/react';
import { LectureCard } from './lecture-card';
import { createAllProvidersWrapper } from '../../../../test/utils';
import { getUsers } from '../../../../services/lectures.service';
import { getAllAssignments } from '../../../../services/assignments.service';
import React from 'react';
import { Lecture } from '../../../../model/lecture';
import { userEvent } from '@testing-library/user-event';

jest.mock('../../../../services/lectures.service');
jest.mock('../../../../services/assignments.service');

const mockedGetUsers = jest.mocked(getUsers);
const mockedGetAllAssignments = jest.mocked(getAllAssignments);

const mockLecture: Lecture = {
  id: 1,
  code: 'CS101',
  name: 'Intro to CS',
  complete: false
};

afterEach(() => {
  jest.clearAllMocks();
});

test('shows assignment and student counts once both requests succeed', async () => {
  mockedGetUsers.mockResolvedValue({
    instructors: [],
    tutors: [],
    students: [
      { id: 1, name: 'Student 1', role: 'student' } as any,
      { id: 2, name: 'Student 2', role: 'student' } as any
    ]
  });

  mockedGetAllAssignments.mockResolvedValue([
    { id: 1, title: 'A1' } as any,
    { id: 2, title: 'A2' } as any,
    { id: 3, title: 'A3' } as any
  ]);

  const user = userEvent.setup();

  render(<LectureCard lecture={mockLecture} />, {
    wrapper: createAllProvidersWrapper()
  });

  expect(screen.getByText('CS101')).toBeInTheDocument();
  expect(screen.getByText('Intro to CS')).toBeInTheDocument();
  expect(await screen.findByText('3 Assignments')).toBeInTheDocument();
  expect(await screen.findByText('2 Students')).toBeInTheDocument();

  const referringBtn = screen.getByRole('button', { name: /details/i });

  expect(referringBtn).toBeInTheDocument();
  await user.click(referringBtn);
});
