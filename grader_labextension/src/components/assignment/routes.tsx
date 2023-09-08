import * as React from 'react';
import { createRoutesFromElements, Route, useNavigation } from 'react-router-dom';
import Box from '@mui/material/Box';
import { Typography } from '@mui/material';
import { LinkRouter, Page } from '../util/breadcrumbs';
import ErrorPage from '../util/error';

import { UserPermissions } from '../../services/permission.service';
import { getAllLectures, getLecture, getUsers } from '../../services/lectures.service';
import { getAllAssignments, getAssignment } from '../../services/assignments.service';
import { getAllSubmissions } from '../../services/submissions.service';


import { enqueueSnackbar } from 'notistack';
import { Assignment } from '../../model/assignment';
import { Lecture } from '../../model/lecture';
import { AssignmentManageComponent } from './assignmentmanage.component';
import { LectureComponent } from './lecture';
import { AssignmentComponent } from './assignment';
import { FileView } from './files/file-view';
import { Feedback } from './feedback';

export const loadPermissions = async () => {
  try {
    await UserPermissions.loadPermissions();
    const [lectures, completedLectures] = await Promise.all([
      getAllLectures(),
      getAllLectures(true)
    ]);
    return { lectures, completedLectures };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
    throw new Error('Could not load data!');
  }
};

export const loadLecture = async (lectureId: number) => {
  try {
    const [lecture, assignments] = await Promise.all([
      getLecture(lectureId),
      getAllAssignments(lectureId, false, true)
    ]);
    return { lecture, assignments };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
    throw new Error('Could not load data!');
  }
};

/*
 * Load submissions for all assignments in a lecture
 * */
export const loadSubmissions = async (lecture: Lecture, assignments: Assignment[]) => {
  try {
    const submissions = await Promise.all(
      assignments.map(async (assignment) => {
        const submissions = await getAllSubmissions(lecture.id, assignment.id, 'none', false);
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

export const loadAssignment = async (lectureId: number, assignmentId: number) => {
  try {
    const [lecture, assignment, submissions] = await Promise.all([
      getLecture(lectureId),
      getAssignment(lectureId, assignmentId),
      getAllSubmissions(lectureId, assignmentId, 'none', false)
    ]);
    return { lecture, assignment, submissions };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
    throw error;
  }
};

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
      <LinkRouter underline='hover' color='inherit' to={to} key={to}>
        {to}
      </LinkRouter>
    </Box>
  );
}

// TODO: remove test code

const testFetchAssignment = async (lectureId: number, assignmentId: number) => {
  console.log(lectureId, assignmentId);
  const { lecture } = await loadLecture(lectureId);
  // throw lecture;
  return {
    assignment: { id: assignmentId, name: 'Introduction to Python' },
    lecture: lecture
  };
};

export const getRoutes = () => {
  const routes = createRoutesFromElements(
    // this is a layout route without a path (see: https://reactrouter.com/en/main/start/concepts#layout-routes)
    <Route element={<Page id={'assignment-manage'} />} errorElement={<ErrorPage id={'assignment-manage'} />}>
      <Route
        id={'root'}
        path={'/*'}
        loader={loadPermissions}
        handle={{
          crumb: (data) => 'Lectures',
          link: (params) => '/'
        }}
      >
        <Route index element={<AssignmentManageComponent />}></Route>
        <Route
          id={'lecture'}
          path={'lecture/:lid/*'}
          loader={({ params }) => loadLecture(+params.lid)}
          handle={{
            // functions in handle have to handle undefined data (error page is displayed afterwards)
            crumb: (data) => data?.lecture.name,
            link: (params) => `lecture/${params?.lid}/`
          }}
        >
          <Route
            index
            element={<LectureComponent />}
          ></Route>
          <Route
            id={'assignment'}
            path={'assignment/:aid/*'}
            loader={({ params }) => loadAssignment(+params.lid, +params.aid)}
            handle={{
              crumb: (data) => data?.assignment.name,
              link: (params) => `assignment/${params?.aid}/`
            }}
          >
            <Route index element={<AssignmentComponent />} />
            <Route path={'feedback/:sid'} element={<Feedback />} handle={{
              crumb: (data) => 'Feedback',
              link: (params) => `feedback/${params?.sid}/`
            }}></Route>
          </Route>
        </Route>
      </Route>
    </Route>
  );
  return routes;
};
