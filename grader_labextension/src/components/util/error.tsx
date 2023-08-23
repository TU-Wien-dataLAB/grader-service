import * as React from 'react';
import { useRouteError } from "react-router-dom";
import { storeString } from '../../services/storage.service';

export default function ErrorPage({id}: {id: string}) {
  const error: any = useRouteError();
  console.error(error);
  storeString(`${id}-react-router-path`, "/");

  return (
    <div id="error-page">
      <h1>Oops!</h1>
      <p>Sorry, an unexpected error has occurred.</p>
      <p>
        <i>{error.statusText || error.message}</i>
      </p>
    </div>
  );
}
