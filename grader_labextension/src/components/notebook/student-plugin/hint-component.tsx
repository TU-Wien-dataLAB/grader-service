import * as React from 'react';
import { Alert, Collapse } from '@mui/material';

export interface IHintComponentProps {
  hint: string;
  show: boolean;
}

export const HintComponent = (props: IHintComponentProps) => {
  const [alert, setAlert] = React.useState(props.show);
  React.useEffect(() => {
    setAlert(props.show);
  }, [props]);
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
