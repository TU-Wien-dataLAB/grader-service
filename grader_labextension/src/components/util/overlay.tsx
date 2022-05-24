// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import Modal from '@mui/material/Modal';
import Fade from '@mui/material/Fade';
import Box from '@mui/material/Box';
import CloseIcon from '@mui/icons-material/Close';
import IconButton from '@mui/material/IconButton';
import { SxProps } from '@mui/system';
import { Theme } from '@mui/material/styles';
import Zoom from '@mui/material/Zoom';
import CircularProgress from '@mui/material/CircularProgress';

interface IOverlayProps {
  open: boolean;
  onClose: () => void;
  loading?: boolean;
  skeleton?: React.ReactNode;
  timeout?: number;
  container?: Element | (() => Element);
  keepMounted?: boolean;
  disableEscapeKeyDown?: boolean;
  sx?: SxProps<Theme>;
  transition: 'fade' | 'zoom';
  children: React.ReactNode;
}

export default function LoadingOverlay(props: IOverlayProps) {
  const baseStyle: SxProps<Theme> = {
    position: 'absolute',
    top: 0,
    bottom: 0,
    width: '100%',
    height: '100%',
    bgcolor: 'background.paper'
  };

  const style = { ...baseStyle, ...props.sx };

  const Transitions = {
    fade: Fade,
    zoom: Zoom
  };
  const Transition = Transitions[props.transition];

  let content;
  if (props.loading) {
    if (props.skeleton === null) {
      content = (
        <CircularProgress
          sx={{
            position: 'absolute',
            top: '50%',
            left: '50%'
          }}
        />
      );
    } else {
      content = props.skeleton;
    }
  } else {
    content = props.children;
  }

  return (
    <Modal
      open={props.open}
      onClose={props.onClose}
      hideBackdrop
      aria-labelledby="modal-modal-title"
      aria-describedby="modal-modal-description"
      container={props.container}
      keepMounted={props.keepMounted}
      disableEnforceFocus={true}
      disableEscapeKeyDown={props.disableEscapeKeyDown}
      sx={{ position: 'absolute', width: '100%', height: '100%' }}
    >
      <Transition in={props.open} timeout={props.timeout}>
        <Box sx={style} className={'.mui-fixed'}>
          <IconButton
            className={'.mui-fixed'}
            size="small"
            sx={{
              position: 'absolute',
              right: '20px',
              top: '20px',
              zIndex: 1000000
            }}
            onClick={props.onClose} // only use props.onClose here
          >
            <CloseIcon />
          </IconButton>
          {content}
        </Box>
      </Transition>
    </Modal>
  );
}

LoadingOverlay.defaultProps = {
  loading: false,
  skeleton: null,
  timeout: 200,
  transition: 'fade',
  sx: {}
};
