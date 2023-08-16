import { SectionTitle } from '../../util/section-title';
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
import {
  createOrOverrideEditRepository,
  getProperties,
  pullSubmissionFiles,
  pushSubmissionFiles,
  updateSubmission
} from '../../../services/submissions.service';
import { FilesList } from '../../util/file-list';
import { lectureBasePath } from '../../../services/file.service';
import { Link, useOutletContext, useRouteLoaderData } from 'react-router-dom';
import Toolbar from '@mui/material/Toolbar';
import { showDialog } from '../../util/dialog-provider';
import Autocomplete from '@mui/material/Autocomplete';


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

  const [loading, setLoading] = React.useState(false);

  const pushEditedFiles = async () => {
   
  };

  return (
    <Stack direction={'column'} sx={{ flex: '1 1 100%' }}>
      <Alert severity="info" sx = {{m: 2}}>
        <AlertTitle>Info</AlertTitle>
        If you want to create a submission for a student manually, make sure to follow these steps: <br/><br/> 
        1. &ensp; Navigate to the 'edit/create/' folder in the File Browser on the left-hand side.<br/>
        2. &ensp; Upload the desired files here. They will automatically appear in the Submission Files.<br/>
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
      <Typography sx={{ m: 2, mb: 0 }}>Submission Files</Typography>
      <FilesList path={path} sx={{ m: 2 }} />

      <Stack direction={'row'} sx={{ ml: 2 }} spacing={2}>
        
        <Button
          variant='outlined'
          color='success'
          onClick={async () => {
            showDialog(
              'Manual Submission',
              'Do you want to push new submission?',
              async () => {
                await pushEditedFiles();
              }
            );
          }}
          sx={{ ml: 2 }}
        >
          Push Submission
        </Button>
      </Stack>
      <Box sx={{ flex: '1 1 100%' }}></Box>
      <Toolbar>
        <Button variant='outlined' component={Link as any} to={submissionsLink}>Back</Button>
      </Toolbar>
    </Stack>
  );
};
