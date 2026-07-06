import {
  Button,
  Card,
  CardActions,
  CardContent,
  CardHeader,
  LinearProgress,
  Modal,
  Typography
} from '@mui/material';
import * as React from 'react';
import { useQuery } from '@tanstack/react-query';
import { getLogs } from '../../services/submissions.service';

interface SubmissionLogsProps {
  lectureId: number;
  assignmentId: number;
  submissionId: number;
  onClose: () => void;
  open: boolean;
}

const formatLogs = (logs: string): JSX.Element[] => {
  return logs.split('\n').map((line, index) => {
    const timestampMatch = line.match(
      /^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}]/
    );
    const logLevelMatch = line.match(/\[(INFO|WARNING|ERROR|DEBUG)]/);

    const timestamp = timestampMatch ? timestampMatch[0] : '';
    const logLevel = logLevelMatch ? logLevelMatch[0] : '';
    const message = line.replace(timestamp, '').replace(logLevel, '').trim();

    let logLevelColor = 'white';
    if (logLevelMatch) {
      switch (logLevelMatch[1]) {
        case 'INFO':
          logLevelColor = 'lightGreen';
          break;
        case 'WARNING':
          logLevelColor = 'orange';
          break;
        case 'ERROR':
          logLevelColor = 'red';
          break;
        case 'DEBUG':
          logLevelColor = 'lightBlue';
          break;
        default:
          logLevelColor = 'white';
      }
    }

    return (
      <div key={index} style={{ color: 'white', fontFamily: 'monospace' }}>
        {timestamp && <span style={{ color: 'gray' }}>{timestamp}</span>}{' '}
        {logLevel && <span style={{ color: logLevelColor }}>{logLevel}</span>}{' '}
        {message}
      </div>
    );
  });
};

export const SubmissionLogs = (props: SubmissionLogsProps) => {
  const { data: logs, isLoading: isLoadingLogs } = useQuery({
    queryKey: [
      'submissionLogs',
      props.lectureId,
      props.assignmentId,
      props.submissionId
    ],
    queryFn: () =>
      getLogs(props.lectureId, props.assignmentId, props.submissionId)
  });

  if (isLoadingLogs) {
    return (
      <div>
        <Card>
          <LinearProgress />
        </Card>
      </div>
    );
  }
  return (
    <Modal open={props.open} onClose={props.onClose}>
      <Card
        style={{
          width: '80%',
          maxHeight: '80%',
          margin: '5% auto',
          padding: '16px',
          overflowY: 'auto'
        }}
      >
        <CardHeader title="Logs" />
        <CardContent
          style={{
            backgroundColor: 'black',
            borderRadius: '8px',
            overflowY: 'auto',
            maxHeight: '60vh',
            color: 'white',
            padding: '16px'
          }}
        >
          {logs && logs.length > 0 ? (
            formatLogs(logs)
          ) : (
            <Typography style={{ color: 'red' }}>No Logs found.</Typography>
          )}
        </CardContent>

        <CardActions style={{ justifyContent: 'flex-end' }}>
          <Button variant="contained" onClick={props.onClose}>
            Close
          </Button>
        </CardActions>
      </Card>
    </Modal>
  );
};
