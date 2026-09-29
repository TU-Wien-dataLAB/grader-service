import { SubmissionRow } from './submissions-data-table';

export const tableMockData: Array<SubmissionRow> = [
  {
    id: 'lina',
    student: 'Lina Hoffmann',
    subRows: [
      {
        id: 'lina-2',
        student: 'Lina Hoffmann',
        label: 'Submission 2',
        score: 283,
        grading: 'failed',
        feedback: false
      },
      {
        id: 'lina-1',
        student: 'Lina Hoffmann',
        label: 'Submission 1',
        score: 750,
        grading: 'graded',
        feedback: true
      }
    ]
  },
  {
    id: 'mateo',
    student: 'Mateo Alvarez',
    score: 0,
    grading: 'not_graded',
    feedback: false
  },
  {
    id: 'aisha',
    student: 'Aisha Rahman',
    score: 800,
    grading: 'graded',
    feedback: true
  }
];
