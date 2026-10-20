import { createRoutesFromElements, Route } from 'react-router';
import { Root } from './app/root';
import { Dashboard } from './app/pages/instructor-view/dashboard';
import React from 'react';
import { Lecture } from './app/pages/instructor-view/lecture';
import {
  activeInstructorLecturesQuery,
  lectureQuery
} from './services/queries/lectures.queries';
import { queryClient } from './widget';
import { getCurrentUserQuery } from './services/queries/users.queries';
import { Assignment } from './app/pages/instructor-view/assignment';
import EditSubmission from './app/components/grader-service/submissions/edit-submission';
import {
  assignmentQuery,
  assignmentsQuery
} from './services/queries/assignments.queries';
import { selectedDirQuery } from './services/queries/files.queries';

export const getRoutes = () => {
  return createRoutesFromElements(
    <Route
      element={<Root />}
      path={'/*'}
      loader={async () => {
        await queryClient.query(activeInstructorLecturesQuery());
        return null;
      }}
    >
      <Route
        index
        element={<Dashboard />}
        loader={async () => {
          await queryClient.query(getCurrentUserQuery());
          return null;
        }}
      ></Route>
      <Route
        path={'lectures/:id'}
        element={<Lecture />}
        loader={async ({ params }) => {
          await queryClient.query(lectureQuery(Number(params.id)));
          await queryClient.query(assignmentsQuery(Number(params.id)));
          return null;
        }}
      ></Route>
      <Route
        path={'lectures/:lid/assignments/:aid'}
        element={<Assignment />}
        loader={async ({ params }) => {
          await Promise.all([
            queryClient.query(
              selectedDirQuery(Number(params.lid), Number(params.aid))
            ),
            queryClient.query(
              assignmentQuery(Number(params.lid), Number(params.aid))
            )
          ]);
          return null;
        }}
      />
      <Route
        path={'lectures/:lid/assignments/:aid/submissions/:sid/edit'}
        element={<EditSubmission />}
        // loader={async ({ params }) => {
        //   await Promise.all([
        //     queryClient.query(
        //       selectedDirQuery(Number(params.lid), Number(params.aid))
        //     ),
        //     queryClient.query(
        //       assignmentQuery(Number(params.lid), Number(params.aid))
        //     )
        //   ]);
        //   return null;
        // }}
      />
    </Route>
  );
};
