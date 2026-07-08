import { SxProps, Tooltip } from '@mui/material';
import React, { ReactElement } from 'react';
import HelpOutlineOutlinedIcon from '@mui/icons-material/HelpOutlineOutlined';

export interface TooltipComponentProps {
  title: string | ReactElement;
  sx?: SxProps;
}

export const TooltipComponent = (props: TooltipComponentProps) => {
  return (
    <Tooltip title={props.title} sx={props.sx}>
      <HelpOutlineOutlinedIcon />
    </Tooltip>
  );
};
