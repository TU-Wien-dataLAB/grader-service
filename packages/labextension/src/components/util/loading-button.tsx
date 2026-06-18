import { Button, ButtonProps } from '@mui/material';
import * as React from 'react';

interface GraderLoadingButtonProps extends ButtonProps {
  onClick: () => void | Promise<void>;
}

export function GraderLoadingButton({
  onClick,
  ...props
}: GraderLoadingButtonProps) {
  const [loading, setLoading] = React.useState(false);

  const handleClick = async () => {
    setLoading(true);
    const result = onClick();
    if (result instanceof Promise) {
      result.finally(() => setLoading(false));
    } else {
      setLoading(false);
    }
  };

  return <Button loading={loading} onClick={handleClick} {...props}></Button>;
}
