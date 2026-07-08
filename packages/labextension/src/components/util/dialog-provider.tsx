import * as React from 'react';
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle
} from '@mui/material';
import { LoadingButton } from '@mui/lab';
import { enqueueSnackbar } from 'notistack';

interface ProviderContext {
  showDialog: (
    title: string,
    message: string,
    onAgree: (() => Promise<void>) | (() => void)
  ) => void;
}

const DialogContext = React.createContext<ProviderContext>({
  showDialog: (
    title: string,
    message: string,
    onAgree: (() => Promise<void>) | (() => void)
  ) => {
    return;
  }
});

export let showDialog: ProviderContext['showDialog'];

interface IDialogProviderProps {
  children: React.ReactNode;
}

export const DialogProvider = (props: IDialogProviderProps) => {
  const [loading, setLoading] = React.useState(false);
  const [open, setOpen] = React.useState(false);
  const [title, setTitle] = React.useState('');
  const [message, setMessage] = React.useState('');
  const [onAgree, setOnAgree] = React.useState<
    (() => Promise<void>) | (() => void)
  >(undefined);

  showDialog = (
    title: string,
    message: string,
    onAgree: (() => Promise<void>) | (() => void)
  ) => {
    setTitle(title);
    setMessage(message);
    setOnAgree(() => onAgree);
    setOpen(true);
  };

  const closeDialog = () => setOpen(false);

  return (
    <DialogContext.Provider value={{ showDialog }}>
      <Dialog
        open={open}
        onClose={closeDialog}
        aria-labelledby="alert-dialog-title"
        aria-describedby="alert-dialog-description"
      >
        <DialogTitle id="alert-dialog-title">{title}</DialogTitle>
        <DialogContent>
          <DialogContentText id="alert-dialog-description">
            <div
              id="alert-dialog-description"
              dangerouslySetInnerHTML={{ __html: message }}
            />
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={closeDialog}>Disagree</Button>
          <LoadingButton
            loading={loading}
            onClick={async () => {
              setLoading(true);

              try {
                await onAgree();
              } catch (e: any) {
                const m = e?.message ? e?.message : 'An Error occurred!';
                enqueueSnackbar('error', m);
              }

              setLoading(false);
              setOpen(false);
            }}
            autoFocus
          >
            <span>Agree</span>
          </LoadingButton>
        </DialogActions>
      </Dialog>
      {props.children}
    </DialogContext.Provider>
  );
};
