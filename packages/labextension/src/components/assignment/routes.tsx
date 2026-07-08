import * as React from 'react';
import { createRoutesFromElements, Route } from 'react-router-dom';
import { Page } from '../util/breadcrumbs';
import ErrorPage from '../util/error';

import { getLecture } from '../../services/lectures.service';
import { getAssignment } from '../../services/assignments.service';
import { getAllSubmissions } from '../../services/submissions.service';

import { enqueueSnackbar } from 'notistack';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { AssignmentManageComponent } from './assignmentmanage.component';
import { LectureComponent } from './lecture';
import { AssignmentComponent } from './assignment';
import { Feedback } from './feedback';
import { QueryClient } from '@tanstack/react-query';

export const loadLecture = async (
  lectureId: number,
  queryClient: QueryClient
) => {
  const query = {
    queryKey: ['lecture', lectureId],
    queryFn: async () => getLecture(lectureId)
  };
  return (
    queryClient.getQueryData(query.queryKey) ??
    (await queryClient.fetchQuery(query))
  );
};

export const loadAssignment = async (
  lectureId: number,
  assignmentId: number,
  queryClient: QueryClient
) => {
  const query = {
    queryKey: ['assignment', lectureId, assignmentId],
    queryFn: async () => getAssignment(lectureId, assignmentId)
  };
  return (
    queryClient.getQueryData(query.queryKey) ??
    (await queryClient.fetchQuery(query))
  );
};

/*
 * Load submissions for all assignments in a lecture
 * */
export const loadSubmissions = async (
  lecture: Lecture,
  assignments: Assignment[]
) => {
  try {
    const submissions = await Promise.all(
      assignments.map(async assignment => {
        const submissions = await getAllSubmissions(
          lecture.id,
          assignment.id,
          'none',
          false
        );
        return { assignment, submissions };
      })
    );
    return submissions;
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
    throw new Error('Could not load data!');
  }
};

/** Example Page
function ExamplePage({ to }) {
  const navigation = useNavigation(); // router navigates to new route (and loads data)
  const loading = navigation.state === 'loading';
  return (
    <Box>
      {!loading ? (
        <Typography>
          This is an example page where the link below can be used for
          naviagation.
        </Typography>
      ) : (
        <Typography>Loading...</Typography>
      )}

      <span>Next Page: </span>
      <LinkRouter underline="hover" color="inherit" to={to} key={to}>
        {to}
      </LinkRouter>
    </Box>
  );
}
*/

export const getRoutes = (queryClient: QueryClient) => {
  const routes = createRoutesFromElements(
    // this is a layout route without a path (see: https://reactrouter.com/en/main/start/concepts#layout-routes)
    <Route
      element={<Page id={'assignment-manage'} />}
      errorElement={<ErrorPage id={'assignment-manage'} />}
    >
      <Route
        id={'root'}
        path={'/*'}
        // loader={loadPermissions}
        handle={{
          crumb: data => 'Lectures',
          link: params => '/'
        }}
      >
        <Route index element={<AssignmentManageComponent />}></Route>
        <Route
          id={'lecture'}
          path={'lecture/:lid/*'}
          loader={({ params }) => loadLecture(+params.lid, queryClient)}
          handle={{
            // functions in handle have to handle undefined data (error page is displayed afterwards)
            crumb: data => data?.name,
            link: params => `lecture/${params?.lid}/`
          }}
        >
          <Route index element={<LectureComponent />}></Route>
          <Route
            id={'assignment'}
            path={'assignment/:aid/*'}
            loader={({ params }) =>
              loadAssignment(+params.lid, +params.aid, queryClient)
            }
            handle={{
              crumb: data => data?.name,
              link: params => `assignment/${params?.aid}/`
            }}
          >
            <Route index element={<AssignmentComponent />} />
            <Route
              path={'feedback/:sid'}
              element={<Feedback />}
              handle={{
                crumb: data => 'Feedback',
                link: params => `feedback/${params?.sid}/`
              }}
            ></Route>
          </Route>
        </Route>
      </Route>
    </Route>
  );
  return routes;
};
