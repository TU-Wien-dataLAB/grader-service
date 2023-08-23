// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Assignment } from '../../../model/assignment';
import { Lecture } from '../../../model/lecture';
import {
  pullAssignment,
  pushAssignment,
  resetAssignment
} from '../../../services/assignments.service';
import {
  submitAssignment
} from '../../../services/submissions.service';
import { Button, Stack, Tooltip } from '@mui/material';
import { FilesList } from '../../util/file-list';
import PublishRoundedIcon from '@mui/icons-material/PublishRounded';
import GetAppRoundedIcon from '@mui/icons-material/GetAppRounded';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import GradingIcon from '@mui/icons-material/Grading';
import { Submission } from '../../../model/submission';
import { RepoType } from '../../util/repo-type';
import { enqueueSnackbar } from 'notistack';
import { lectureBasePath } from '../../../services/file.service';
import { showDialog } from '../../util/dialog-provider';
import { openBrowser } from '../../coursemanage/overview/util';
import { GlobalObjects } from '../../..';
import { Contents } from '@jupyterlab/services';
import moment from 'moment';

/**
 * Props for Files.
 */
export interface IFilesProps {
  lecture: Lecture;
  assignment: Assignment;

}

/**
 * Renders the file view and additional buttons to submit, push, pull or reset the assignment.
 * @param props Props of the assignment files component
 */
export const Files = (
  props: IFilesProps
) => {
  const path = `${lectureBasePath}${props.lecture.code}/assignments/${props.assignment.id}`;

 

  /**
   * Opens file assignment folder directly by rendering page.
  */
  openBrowser(path);
  
  const [srcChangedTimestamp, setSrcChangeTimestamp] = React.useState(
    moment().valueOf()
  );

  React.useEffect(() => {
    GlobalObjects.docManager.services.contents.fileChanged.connect(
      (sender: Contents.IManager, change: Contents.IChangedArgs) => {
        const { oldValue, newValue } = change;
        if (!newValue.path.includes(path)) {
          return;
        }

        const modified = moment(newValue.last_modified).valueOf();
        if (srcChangedTimestamp === null || srcChangedTimestamp < modified) {
          setSrcChangeTimestamp(modified);
        }
      },
      this
    );
  });

  

  return (
    <div>
      <FilesList path={path} sx={{ m: 2, mt: 1}} />
      
    </div>
  );
};
