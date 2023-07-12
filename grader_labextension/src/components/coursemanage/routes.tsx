import * as React from 'react';
import { createRoutesFromElements, Route, useNavigation } from 'react-router-dom';
import Box from '@mui/material/Box';
import { Typography } from '@mui/material';
import { LinkRouter, Page } from '../util/breadcrumbs';
import ErrorPage from '../util/error';
import { CourseManageComponent } from './coursemanage.component';
import { UserPermissions } from '../../services/permission.service';
import { getAllLectures, getLecture, getUsers } from '../../services/lectures.service';
import { enqueueSnackbar } from 'notistack';
import { getAllAssignments, getAssignment } from '../../services/assignments.service';
import { LectureComponent } from './lecture';
import { getAllSubmissions } from '../../services/submissions.service';
import { AssignmentModalComponent } from './assignment-modal';

const loadPermissions = async () => {
  try {
    await UserPermissions.loadPermissions();
    const lectures = await getAllLectures();
    const completedLectures = await getAllLectures(true);
    return { lectures, completedLectures };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
  }
};

const loadLecture = async (lectureId: number) => {
  try {
    const lecture = await getLecture(lectureId);
    const assignments = await getAllAssignments(lecture.id);
    const users = await getUsers(lecture);

    return { lecture, assignments, users };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
  }
  return { lecture: { id: lectureId, name: 'Recommender Systems' } };
};

// TODO: remove test code
const loadAssignment = async (lectureId: number, assignmentId: number) => {
  try {
    const assignment = await getAssignment(lectureId, assignmentId);
    const allSubmissions = await getAllSubmissions(lectureId, assignmentId, 'none', true);
    const latestSubmissions = await getAllSubmissions(lectureId, assignmentId, 'latest', true);
    return { assignment, allSubmissions, latestSubmissions };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
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

export const getRoutes = (root: HTMLElement) => {
  const routes = createRoutesFromElements(
    // this is a layout route without a path (see: https://reactrouter.com/en/main/start/concepts#layout-routes)
    <Route element={<Page />} errorElement={<ErrorPage />}>
      <Route
        id={'root'}
        path={'/*'}
        loader={loadPermissions}
        handle={{
          crumb: (data) => 'Lectures',
          link: (params) => '/'
        }}
      >
        <Route index element={<CourseManageComponent root={root} />}></Route>
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
            element={<LectureComponent root={root} />}
          ></Route>
          <Route
            id={'assignment'}
            path={'assignment/:aid/*'}
            loader={({ params }) => loadAssignment(+params.lid, +params.aid)}
            handle={{
              // functions in handle have to handle undefined data (error page is displayed afterwards)
              crumb: (data) => data?.assignment.name,
              link: (params) =>
                `assignment/${params.aid}`
            }}
          >
            <Route index element={<AssignmentModalComponent root={root} />}></Route>
          </Route>
        </Route>
      </Route>
    </Route>
  );
  return routes;
};
