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
import { AssignmentManageComponent } from './assignmentmanage.component';
import { LectureComponent } from './lecture';
import { AssignmentComponent } from './assignment';

export const loadPermissions = async () => {
    try {
        await UserPermissions.loadPermissions();
        const lectures = await getAllLectures(); 
        const completedLectures = await getAllLectures(true);
        return { lectures, completedLectures };
    } catch (error: any) {
        enqueueSnackbar(error.message, { 
            variant: 'error', 
        });
    }   
};

export const loadLecture = async (lectureId: number) => {
  try {
    const lecture = await getLecture(lectureId);
    const assignments = await getAllAssignments(lecture.id);

    return { lecture, assignments };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
  }
  return { lecture: { id: lectureId, name: 'Recommender Systems' } };
};


export const loadAssignment = async (lectureId: number, assignmentId: number) => {
    const err_assignment = { 
        assignment: { id: -1, name: 'Error loading assignment', }
    };

  try {
    const assignment = await getAssignment(lectureId, assignmentId);
    const submissions = await getAllSubmissions(lectureId, assignmentId, "none", false);
    return { assignment, submissions };
  } catch (error: any) {
    enqueueSnackbar(error.message, {
      variant: 'error'
    });
  }
    return err_assignment;
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

export const getRoutes = (root: HTMLElement) => {
    const routes = createRoutesFromElements(
        // this is a layout route without a path (see: https://reactrouter.com/en/main/start/concepts#layout-routes)
        <Route element={<Page id={"assignment-manage"} />} errorElement={<ErrorPage />}>
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
                        element={<LectureComponent root={root} />}
                    ></Route>
                    <Route
                        id={'assignment'}
                        path={'assignment/:aid/*'}
                        element={<AssignmentComponent root={root} />}
                        loader={({ params }) => loadAssignment(+params.lid, +params.aid)}
                        handle={{
                            crumb: (data) => data?.assignment.name,
                            link: (params) => `assignment/${params?.aid}/`
                        }}
                    >
                    </Route>
                </Route>           
            </Route>
        </Route>
    );
    return routes;
};
