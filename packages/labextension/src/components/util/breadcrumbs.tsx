import * as React from 'react';
import Link, { LinkProps } from '@mui/material/Link';
import {
  Link as RouterLink,
  useMatches,
  Outlet,
  useLocation
} from 'react-router-dom';
import { Box, Breadcrumbs, Stack, Typography } from '@mui/material';
import NavigateNextIcon from '@mui/icons-material/NavigateNext';
import { storeString } from '../../services/storage.service';

export const Page = ({ id }: { id: string }) => {
  const location = useLocation();
  const pathname =
    '/' +
    location.pathname
      .split('/')
      .filter(v => v.length > 0)
      .slice(0, 2)
      .join('/');
  storeString(`${id}-react-router-path`, pathname);

  return (
    <Stack flexDirection={'column'} sx={{ height: '100%', width: '100%' }}>
      <RouterBreadcrumbs />
      <Box
        sx={{
          flex: 1,
          display: 'flex',
          alignItems: 'stretch',
          height: '100%',
          overflow: 'hidden'
        }}
      >
        <Outlet key={id} />
      </Box>
    </Stack>
  );
};

interface ILinkRouterProps extends LinkProps {
  to: string;
  replace?: boolean;
}

export function LinkRouter(props: ILinkRouterProps) {
  return <Link {...props} component={RouterLink as any} />;
}

export const RouterBreadcrumbs = () => {
  const pathname = useLocation().pathname.replace(/\/$/, '');
  const matches = useMatches();

  const crumbs = matches
    // first get rid of any matches that don't have handle and crumb
    .filter((match: any) => Boolean(match.handle?.crumb))
    // now map them into an array of elements, passing the loader
    // data to each one
    .map((match: any) => match.handle.crumb(match.data));

  const links = matches
    .filter((match: any) => Boolean(match.handle?.link))
    .map((match: any) => match.handle.link(match.params));

  return (
    <Breadcrumbs
      sx={{ m: 1 }}
      aria-label="breadcrumb"
      separator={<NavigateNextIcon fontSize="small" />}
    >
      {links.map((value, index) => {
        const last = index === links.length - 1;
        const to = links.slice(0, index + 1).join('');
        const samePath = to.replace(/\/$/, '') === pathname; // e.g. happens if last path adds nothing to link (second to last crumb also points to same page)
        return last || samePath ? (
          <Typography color="text.primary" key={to}>
            {crumbs[index]}
          </Typography>
        ) : (
          <LinkRouter underline="hover" color="inherit" to={to} key={to}>
            {crumbs[index]}
          </LinkRouter>
        );
      })}
    </Breadcrumbs>
  );
};

export const extractIdsFromBreadcrumbs = () => {
  const matches = useMatches();
  const links = matches
    .filter((match: any) => Boolean(match.handle?.link))
    .map((match: any) => match.handle.link(match.params));

  let lectureId;
  let assignmentId;

  for (let i = 0; i < links.length; i++) {
    if (links[i].includes('lecture')) {
      const lecture = links[i].split('/');
      lectureId = parseInt(lecture[1], 10);
    } else if (links[i].includes('assignment')) {
      const assignment = links[i].split('/');
      assignmentId = parseInt(assignment[1], 10);
    }
  }

  return { lectureId, assignmentId };
};
