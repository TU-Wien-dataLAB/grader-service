import * as React from 'react';
import { Alert, Collapse } from '@mui/material';

export interface IHintComponentProps {
  hint: string;
  show: boolean;
}

export const HintComponent = (props: IHintComponentProps) => {
  return (
    <Collapse in={props.show}>
      <Alert sx={{ mt: 1, mb: 1 }} severity="info">
        {props.hint}
      </Alert>
    </Collapse>
  );
};
