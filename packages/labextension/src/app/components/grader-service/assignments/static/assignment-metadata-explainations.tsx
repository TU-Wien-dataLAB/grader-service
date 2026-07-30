import React from 'react';

export const GRADING_METHOD = (
  <p>
    Specifies the behaviour when a students submits an assignment. <br />
    Manual Grading: No action is taken on submit. <br />
    Automatic Grading: The assignment is being autograded as soon as students
    makes a submission. <br />
    Fully Automatic Grading: The assignment is autograded and feedback is
    generated as soon as the student <br /> makes a submission. (requires all
    scores to <br />
    be based on autograde results)
  </p>
);
export const CELL_TIMEOUT = (
  <p>
    Set a custom timeout for <br />
    notebook cells in seconds.
  </p>
);

export const WHITELIST_FILE_PATTERNS = (
  <p>
    Allow additional submission files by <br /> adding glob file patterns, for
    <br /> example: submission.py, *.txt <br /> or output_dir/*.pdf.
  </p>
);
export const LATE_SUBMISSIONS = (
  <p>
    Allowing a late submission period <br /> enables students to submit their{' '}
    <br />
    assignments after the deadline, <br /> with a score penalty applied. Once{' '}
    <br /> the original deadline has passed, <br /> no late submission can be
    created.
  </p>
);
