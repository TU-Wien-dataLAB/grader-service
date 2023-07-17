import * as React from 'react';
import Link, { LinkProps } from '@mui/material/Link';
import {
  Link as RouterLink,
  useMatches,
  useParams,
  useLoaderData,
  Outlet
} from 'react-router-dom';
import { Breadcrumbs, Typography } from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';


export const Page = () => {
  return (
    <>
      <RouterBreadcrumbs />
      <Outlet />
    </>
  );
};

interface LinkRouterProps extends LinkProps {
  to: string;
  replace?: boolean;
}

export function LinkRouter(props: LinkRouterProps) {
  return <Link {...props} component={RouterLink as any} />;
}

export const RouterBreadcrumbs = () => {
  const data = useLoaderData();
  const params = useParams();
  let matches = useMatches();

  let crumbs = matches
    // first get rid of any matches that don't have handle and crumb
    .filter((match: any) => Boolean(match.handle?.crumb))
    // now map them into an array of elements, passing the loader
    // data to each one
    .map((match: any) => match.handle.crumb(match.data));

  console.log(crumbs);

  let links = matches
    .filter((match: any) => Boolean(match.handle?.link))
    .map((match: any) => match.handle.link(match.params));

  console.log(links);

  return (
    <Breadcrumbs
      sx={{ m: 1 }}
      aria-label='breadcrumb'
      separator={<NavigateNextIcon fontSize='small' />}
    >
      {links.map((value, index) => {
        const last = index === links.length - 1;
        const to = links.slice(0, index + 1).join('');
        return last ? (
          <Typography color='text.primary' key={to}>
            {crumbs[index]}
          </Typography>
        ) : (
          <LinkRouter underline='hover' color='inherit' to={to} key={to}>
            {crumbs[index]}
          </LinkRouter>
        );
      })}
    </Breadcrumbs>
  );
};