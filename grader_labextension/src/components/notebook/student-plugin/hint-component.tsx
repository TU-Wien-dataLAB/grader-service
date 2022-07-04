import * as React from 'react';
import { Alert, Collapse } from '@mui/material';

export interface IHintComponentProps {
  hint: string;
}

export const HintCompontent = (props: IHintComponentProps) => {
  const [alert, setAlert] = React.useState(true);

  return (
    <Collapse in={alert}>
      <Alert
        sx={{ mt: 1, mb: 1 }}
        severity="info"
        onClose={() => {
          setAlert(false);
        }}
      >
        {props.hint}
      </Alert>
    </Collapse>
  );
};
