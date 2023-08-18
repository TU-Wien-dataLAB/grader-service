import {
    Alert,
  AlertTitle,
  Box,
  Button,
  IconButton,
  Stack,
  TextField,
  Tooltip,
  Typography
} from '@mui/material';
import * as React from 'react';
import { Lecture } from '../../../model/lecture';
import { Assignment } from '../../../model/assignment';
import { Submission } from '../../../model/submission';
import { FilesList } from '../../util/file-list';
import { lectureBasePath } from '../../../services/file.service';
import { Link, useOutletContext, useRouteLoaderData } from 'react-router-dom'
import { showDialog } from '../../util/dialog-provider';
import Autocomplete from '@mui/material/Autocomplete';
import moment from 'moment';
import { Contents } from '@jupyterlab/services';
import { GlobalObjects } from '../../../index';
import { openBrowser } from '../overview/util';
import ReplayIcon from '@mui/icons-material/Replay';


export const CreateSubmission = () => {
  const {
    assignment,
    rows,
    setRows,
  } = useOutletContext() as {
    lecture: Lecture,
    assignment: Assignment,
    rows: Submission[],
    setRows: React.Dispatch<React.SetStateAction<Submission[]>>,
    manualGradeSubmission: Submission,
    setManualGradeSubmission: React.Dispatch<React.SetStateAction<Submission>>
  };
  const { lecture, assignments, users } = useRouteLoaderData('lecture') as {
    lecture: Lecture,
    assignments: Assignment[],
    users: { instructors: string[], tutors: string[], students: string[] }
  };
  const path = `${lectureBasePath}${lecture.code}/edit/${assignment.id}/create`;
  const submissionsLink = `/lecture/${lecture.id}/assignment/${assignment.id}/submissions`;

  const [srcChangedTimestamp, setSrcChangeTimestamp] = React.useState(
    moment().valueOf()
  ); // now
  
  React.useEffect(() => {
    const srcPath = `${lectureBasePath}${lecture.code}/edit/${assignment.id}/create`;
    GlobalObjects.docManager.services.contents.fileChanged.connect(
      (sender: Contents.IManager, change: Contents.IChangedArgs) => {
        const { oldValue, newValue } = change;
        if (!newValue.path.includes(srcPath)) {
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
  
  openBrowser(`${lectureBasePath}${lecture.code}/edit/${assignment.id}/create`);

  const createSubmission = async () => {
   
  };

  const [reloadFilesToggle, setReloadFiles] = React.useState(false);

  const reloadFiles = () => {
    setReloadFiles(!reloadFilesToggle);
  };

  return (
    <Stack direction={'column'} sx={{ flex: '1 1 100%' }}>
      <Alert severity="info" sx = {{m: 2}}>
        <AlertTitle>Info</AlertTitle>
        If you want to create a submission for a student manually, make sure to follow these steps: <br/><br/> 
        1. &ensp; By loading this page, directory 'edit/create/' is automatically opened in File Browser on your left-hand side.<br/>
        2. &ensp; Upload the desired files here. They will automatically appear in the Submission Files below.<br/>
        3. &ensp; Choose the student for whom you want to create the submission.<br/>
        4. &ensp; Push the submission.
      </Alert>
      <Typography sx={{ m: 2, mb: 0 }}>Select a student</Typography>
      <Autocomplete
        id="country-select-demo"
        options={users["students"]}
        autoHighlight
        sx={{m: 2}}
        renderInput={(params) => (
            <TextField
            {...params}
            label="Choose Student"
            inputProps={{
                ...params.inputProps,
                autoComplete: 'new-password', 
            }}
            />
        )}
    />
      <Stack direction={'row'} justifyContent={'flex-start'} alignItems={'center'} spacing={2} sx={{ml: 2}} >
        <Typography>Submission Files</Typography>
        <Tooltip title='Reload Files'>
          <IconButton aria-label='reload' onClick={() => reloadFiles()}>
            <ReplayIcon />
          </IconButton>
        </Tooltip>
      </Stack>
      
      <FilesList path={path} sx={{m: 2}}/>
      <Stack direction={'row'} sx={{ ml: 2 }} spacing={2}>
        <Button
          variant='outlined'
          color='success'
          onClick={async () => {
            showDialog(
              'Manual Submission',
              'Do you want to push new submission?',
              async () => {
                await createSubmission();
              }
            );
          }}
          sx={{ ml: 2 }}
        >
          Push Submission
        </Button>
      </Stack>
      <Stack sx={{ml: 2, mt: 3, mb: 5}} direction={'row'}>
        <Button variant='outlined' component={Link as any} to={submissionsLink}>Back</Button>
      </Stack>
    </Stack>
  );
};
