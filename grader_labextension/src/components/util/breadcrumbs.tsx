import * as React from 'react';
import Link, { LinkProps } from '@mui/material/Link';
import {
  Link as RouterLink,
  useMatches,
  useParams,
  useLoaderData,
  Outlet, useLocation
} from 'react-router-dom';
import { Box, Breadcrumbs, Stack, Typography } from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { storeString } from '../../services/storage.service';


export const Page = ({ id }: { id: string }) => {
  const pathname = '/' + useLocation().pathname.split('/').filter(v => v.length > 0).slice(0, 2).join('/');
  storeString(`${id}-react-router-path`, pathname);

  return (
    <Stack flexDirection={'column'} sx={{ height: '100%', width: '100%' }}>
      <RouterBreadcrumbs />
      <Box sx={{ flex: 1, display: 'flex', alignItems: 'stretch', height: '100%', overflow: 'hidden' }}>
        <Outlet />
      </Box>
    </Stack>
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
  const pathname = useLocation().pathname.replace(/\/$/, '');
  let matches = useMatches();
  console.log(`Navigating to: ${pathname}`);

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
        const samePath = to.replace(/\/$/, '') === pathname; // e.g. happens if last path adds nothing to link (second to last crumb also points to same page)
        return last || samePath ? (
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