import { createRoutesFromElements, redirect, Route } from 'react-router';
import { Root } from './app/root';
import { Dashboard } from './app/pages/instructor-view/dashboard';
import { Dashboard as StudentDashboard } from './app/pages/student-view/dashboard';
import React from 'react';
import { Lecture } from './app/pages/instructor-view/lecture';
import { Lecture as StudentLecture } from './app/pages/student-view/lecture';
import {
  lectureQuery
} from './services/queries/lectures.queries';
import { queryClient } from './widget';
import { getCurrentUserQuery } from './services/queries/users.queries';
import { assignmentsQuery } from './services/queries/assignments.queries';
import { UserPermissions } from './services/permission.service';
import { Assignment } from './app/pages/student-view/assignment';

type Role = 'instructor' | 'student';

const getRole = (): Role =>
  UserPermissions.hasElevatedPermissions() ? 'instructor' : 'student';

const roleHome = (role: Role) => `/${role}`;

// Redirects if the user is in the wrong view.
const requireRole = (role: Role) => {
  const actual = getRole();
  if (actual !== role) throw redirect(roleHome(actual));
};

export const getRoutes = () => {
  return createRoutesFromElements(
    <Route
      element={<Root />}
      path={'/'}
      loader={async () => {
        await queryClient.query(activeInstructorLecturesQuery());
        return null;
      }}
    >
      <Route index loader={() => redirect(roleHome(getRole()))} />
      <Route
        index
        element={<Dashboard />}
        path={'instructor'}
        loader={async () => {
          requireRole('instructor');
          await queryClient.ensureQueryData(getCurrentUserQuery());
          return null;
        }}
      ></Route>
      <Route
        path={'instructor/lectures/:id'}
        element={<Lecture />}
        loader={async ({ params }) => {
          requireRole('instructor');
          await queryClient.ensureQueryData(lectureQuery(Number(params.id)));
          await queryClient.ensureQueryData(
            assignmentsQuery(Number(params.id))
          );
          return null;
        }}
      ></Route>
      <Route
        index
        element={<StudentDashboard />}
        path={'student'}
        loader={async () => {
          requireRole('student');
          await queryClient.ensureQueryData(getCurrentUserQuery());
          return null;
        }}
      ></Route>
      <Route
        path={'student/lectures/:id'}
        element={<StudentLecture />}
        loader={async ({ params }) => {
          requireRole('student');
          await queryClient.ensureQueryData(lectureQuery(Number(params.id)));
          await queryClient.ensureQueryData(assignmentsQuery(Number(params.id)));
          return null;
        }}
      ></Route>
      <Route
        path={'student/lectures/:lectureId/assignments/:assignmentId'}
        element={<Assignment />}
        loader={async ({ params }) => {
          requireRole('student');
          const lectureId = Number(params.lectureId);
          await queryClient.ensureQueryData(lectureQuery(lectureId));
          await queryClient.ensureQueryData(assignmentsQuery(lectureId));
          return null;
        }}
      ></Route>
    </Route>
  );
};


