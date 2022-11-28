import * as React from 'react';
import { Typography } from '@mui/material';
import { SxProps } from '@mui/system';
import { Theme } from '@mui/material/styles';

export interface ICardDescriptorProps {
  value: number | React.ReactNode;
  ofTotal?: number;
  descriptor: string;
  fontSize: number;
  fontSizeTotal: number;
  fontSizeDescriptor: number;
  sx?: SxProps<Theme>;
}

export const CardDescriptor = (props: ICardDescriptorProps) => {
  return (
    <Typography sx={{ fontSize: props.fontSize, ...props.sx }}>
      {props.value}
      {props.ofTotal ? (
        <Typography
          sx={{ fontSize: props.fontSizeTotal, ml: 0, display: 'inline-block' }}
        >
          {'/' + props.ofTotal}
        </Typography>
      ) : null}

      <Typography
        color="text.secondary"
        sx={{
          display: 'inline-block',
          ml: 0.75,
          fontSize: props.fontSizeDescriptor
        }}
      >
        {props.descriptor +
          (props.value === 1 || React.isValidElement(props.value) ? '' : 's')}
      </Typography>
    </Typography>
  );
};

CardDescriptor.defaultProps = {
  fontSize: 16,
  fontSizeTotal: 10,
  fontSizeDescriptor: 14,
  sx: { mt: 0.5, ml: 0.5 }
};
