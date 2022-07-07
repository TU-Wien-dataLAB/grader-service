import {Lecture} from "../../../model/lecture";
import {Assignment} from "../../../model/assignment";
import {Submission} from "../../../model/submission";
import {Box, Grid, IconButton, Tooltip} from "@mui/material";
import {ModalTitle} from "../../util/modal-title";
import ReplayIcon from "@mui/icons-material/Replay";
import * as React from "react";
import {getAllSubmissions} from "../../../services/submissions.service";
import {SubmissionTimeSeries} from "./submission-timeseries";
import {GradingProgress} from "./grading-progress";
import {StudentSubmissions} from "./student-submissions";
import {ScoreDistribution} from "./score-distribution";
import {getUsers} from "../../../services/lectures.service";

export const filterUserSubmissions = (submissions: Submission[], users: string[]): Submission[] => {
  return submissions.filter((v, i, a) => !users.includes(v.username))
}


export interface IStatsProps {
  lecture: Lecture;
  assignment: Assignment;
  allSubmissions: Submission[];
  latestSubmissions: Submission[];
  users: { students: string[]; tutors: string[]; instructors: string[] };
  root: HTMLElement;
  showAlert: (severity: string, msg: string) => void;
}

export const StatsComponent = (props: IStatsProps) => {
  const [submissions, setSubmissions] = React.useState(props.allSubmissions);
  const [latestSubmissions, setLatestSubmissions] = React.useState(props.latestSubmissions);
  const [users, setUsers] = React.useState(props.users);

  const updateSubmissions = () => {
    getAllSubmissions(props.lecture, props.assignment, "none", true).then(
      response => {
        setSubmissions(response);
      }
    );
    getAllSubmissions(props.lecture, props.assignment, "latest", true).then(
      response => {
        setLatestSubmissions(response);
      }
    );
    getUsers(props.lecture).then(response => {
      setUsers(response);
    });
  };

  return (
    <Box>
      <ModalTitle title={`${props.assignment.name} Stats`}>
        <Box sx={{ml: 2}} display="inline-block">
          <Tooltip title="Reload">
            <IconButton aria-label="reload" onClick={updateSubmissions}>
              <ReplayIcon/>
            </IconButton>
          </Tooltip>
        </Box>
      </ModalTitle>
      <Box sx={{ml: 3, mr: 3, mb: 3, mt: 3}}>
        <Grid container spacing={2} alignItems="stretch">
          <Grid item xs={12}>
            <SubmissionTimeSeries lecture={props.lecture} assignment={props.assignment} allSubmissions={submissions}
                                  latestSubmissions={latestSubmissions} users={users} root={props.root}
                                  showAlert={props.showAlert}/>
          </Grid>
          <Grid item xs={6}>
            <GradingProgress lecture={props.lecture} assignment={props.assignment} allSubmissions={submissions}
                             latestSubmissions={latestSubmissions} users={users} root={props.root}
                             showAlert={props.showAlert}/>
          </Grid>
          <Grid item xs={6}>
            <StudentSubmissions lecture={props.lecture} assignment={props.assignment} allSubmissions={submissions}
                                latestSubmissions={latestSubmissions} users={users} root={props.root}
                                showAlert={props.showAlert}/>
          </Grid>
          <Grid item xs={12}>
            <ScoreDistribution lecture={props.lecture} assignment={props.assignment} allSubmissions={submissions}
                               latestSubmissions={latestSubmissions} users={users} root={props.root}
                               showAlert={props.showAlert}/>
          </Grid>
        </Grid>
      </Box>
    </Box>
  )
}