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
import { assignmentsQuery } from './services/queries/assignments.queries';

export const getRoutes = () => {
  return createRoutesFromElements(
    <Route
      element={<Root />}
      path={'/*'}
      loader={async () => {
        await queryClient.ensureQueryData(activeInstructorLecturesQuery());
        return null;
      }}
    >
      <Route
        index
        element={<Dashboard />}
        loader={async () => {
          await queryClient.ensureQueryData(getCurrentUserQuery());
          return null;
        }}
      ></Route>
      <Route
        path={'lectures/:id'}
        element={<Lecture />}
        loader={async ({ params }) => {
          await queryClient.ensureQueryData(lectureQuery(Number(params.id)));
          await queryClient.ensureQueryData(
            assignmentsQuery(Number(params.id))
          );
          return null;
        }}
      ></Route>
    </Route>
  );
};
