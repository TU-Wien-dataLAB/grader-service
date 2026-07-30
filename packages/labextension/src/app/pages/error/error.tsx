import React from 'react';
import { useRouteError } from 'react-router';

export const Error = () => {
  const error: unknown = useRouteError();
  return (
    <div>
      Oops!
      <h1>An unexpected error has occured</h1>
    </div>
  );
};
