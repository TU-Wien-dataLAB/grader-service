// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { getAllLectures } from '../../services/lectures.service';
import { Scope, UserPermissions } from '../../services/permission.service';
import { LectureComponent } from './lecture';
import { Alert, AlertProps, AlertTitle, Portal, Snackbar } from '@mui/material';

export interface ICourseManageProps {
  // lectures: Array<Lecture>;
  root: HTMLElement;
}

export const CourseManageComponent = (props: ICourseManageProps) => {
  const [alert, setAlert] = React.useState(false);
  const [severity, setSeverity] = React.useState('success');
  const [alertMessage, setAlertMessage] = React.useState('');

  const showAlert = (severity: string, msg: string) => {
    setSeverity(severity);
    setAlertMessage(msg);
    setAlert(true);
  };

  const handleAlertClose = (
    event?: React.SyntheticEvent | Event,
    reason?: string
  ) => {
    if (reason === 'clickaway') {
      return;
    }
    setAlert(false);
  };

  const [lectures, setLectures] = React.useState([] as Lecture[]);
  const [completedLectures, setCompletedLectures] = React.useState(
    [] as Lecture[]
  );
  React.useEffect(() => {
    UserPermissions.loadPermissions()
      .then(() => {
        getAllLectures().then(l => setLectures(l));
        getAllLectures(true).then(l => setCompletedLectures(l));
      })
      .catch(() => showAlert('error', 'Error Loading Permissions'));
  }, [props]);

  return (
    <div className="course-list">
      <h1>
        <p className="course-header">Course Management</p>
      </h1>
      {lectures
        .filter(el => UserPermissions.getScope(el) > Scope.student)
        .map((el, index) => (
          <LectureComponent
            lecture={el}
            root={props.root}
            showAlert={showAlert}
            expanded={true}
          />
        ))}
      {completedLectures
        .filter(el => UserPermissions.getScope(el) > Scope.student)
        .map((el, index) => (
          <LectureComponent
            lecture={el}
            root={props.root}
            showAlert={showAlert}
            expanded={false}
          />
        ))}
      <Portal container={document.body}>
        {alert && (
          <Snackbar
            open={alert}
            anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
            autoHideDuration={6000}
            onClose={handleAlertClose}
          >
            <Alert
              onClose={handleAlertClose}
              severity={severity as AlertProps['severity']}
            >
              <AlertTitle>{alertMessage}</AlertTitle>
            </Alert>
          </Snackbar>
        )}
      </Portal>
    </div>
  );
};
