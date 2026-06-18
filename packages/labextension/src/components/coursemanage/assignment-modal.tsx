// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import {
  Badge,
  Box,
  IconButton,
  Stack,
  Tab,
  Tabs,
  Tooltip
} from '@mui/material';
import DashboardIcon from '@mui/icons-material/Dashboard';
import FolderIcon from '@mui/icons-material/Folder';
import FormatListNumberedIcon from '@mui/icons-material/FormatListNumbered';
import QueryStatsIcon from '@mui/icons-material/QueryStats';
import SettingsIcon from '@mui/icons-material/Settings';
import KeyboardDoubleArrowLeftIcon from '@mui/icons-material/KeyboardDoubleArrowLeft';
import KeyboardDoubleArrowRightIcon from '@mui/icons-material/KeyboardDoubleArrowRight';
import { Link, Outlet, useMatch, useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { getAllSubmissions } from '../../services/submissions.service';
import { extractIdsFromBreadcrumbs } from '../util/breadcrumbs';
import { loadBoolean, storeBoolean } from '../../services/storage.service';

function a11yProps(index: any) {
  return {
    id: `vertical-tab-${index}`,
    'aria-controls': `vertical-tabpanel-${index}`
  };
}

export const AssignmentModalComponent = () => {
  const { lectureId, assignmentId } = extractIdsFromBreadcrumbs();

  const { data: latestSubmissionsNumber = 0 } = useQuery<number>({
    queryKey: ['latestSubmissionsNumber', lectureId, assignmentId],
    queryFn: async () => {
      const submissions = await getAllSubmissions(
        lectureId,
        assignmentId,
        'latest'
      );
      return submissions.length;
    },
    enabled: !!lectureId && !!assignmentId
  });

  const params = useParams();
  const match = useMatch(`/lecture/${params.lid}/assignment/${params.aid}/*`);
  const tab = match.params['*'];

  let value: number;
  if (tab === '') {
    value = 0;
  } else if (tab === 'files') {
    value = 1;
  } else if (tab.includes('submissions')) {
    value = 2;
  } else if (tab === 'stats') {
    value = 3;
  } else if (tab === 'settings') {
    value = 4;
  } else {
    console.warn(`Unknown tab ${tab}... navigating to overview page!`);
    value = 0;
  }

  const [isExpanded, setIsExpanded] = React.useState<boolean>(() => {
    return loadBoolean('isExpanded') ?? true;
  });

  React.useEffect(() => {
    storeBoolean('isExpanded', isExpanded);
  }, [isExpanded]);

  return (
    <Stack flexDirection={'column'} sx={{ flex: 1, overflowY: 'auto' }}>
      <Box
        sx={{
          flex: 1,
          bgcolor: 'background.paper',
          display: 'flex',
          overflow: 'hidden'
        }}
      >
        <Box
          sx={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: isExpanded ? 'flex-start' : 'center',
            borderRight: 1,
            borderColor: 'divider',
            transition: 'min-width 0.3s ease-in-out',
            marginTop: 5
          }}
        >
          <Tooltip title={isExpanded ? 'Collapse' : 'Expand'}>
            <IconButton
              onClick={() => setIsExpanded(!isExpanded)}
              sx={{
                alignSelf: isExpanded ? 'flex-end' : 'center'
              }}
            >
              {isExpanded ? (
                <KeyboardDoubleArrowLeftIcon />
              ) : (
                <KeyboardDoubleArrowRightIcon />
              )}
            </IconButton>
          </Tooltip>

          <Tabs
            orientation="vertical"
            value={value}
            sx={{
              flex: 1,
              overflow: 'hidden'
            }}
          >
            {[
              { label: 'Overview', icon: <DashboardIcon />, link: '' },
              { label: 'Files', icon: <FolderIcon />, link: 'files' },
              {
                label: 'Submissions',
                icon: (
                  <Badge
                    color="secondary"
                    badgeContent={latestSubmissionsNumber}
                    showZero={latestSubmissionsNumber !== 0}
                  >
                    <FormatListNumberedIcon />
                  </Badge>
                ),
                link: 'submissions'
              },
              { label: 'Stats', icon: <QueryStatsIcon />, link: 'stats' },
              { label: 'Settings', icon: <SettingsIcon />, link: 'settings' }
            ].map((tab, index) => (
              <Tab
                key={index}
                label={isExpanded ? tab.label : ''}
                icon={tab.icon}
                iconPosition="start"
                sx={{
                  justifyContent: isExpanded ? 'flex-start' : 'center',
                  padding: isExpanded ? '8px 16px' : '4px',
                  minWidth: isExpanded ? 160 : 48,
                  minHeight: 48,
                  mr: 1
                }}
                {...a11yProps(index)}
                component={Link as any}
                to={tab.link}
              />
            ))}
          </Tabs>
        </Box>
        <Box sx={{ display: 'flex', flexGrow: 1, overflow: 'hidden' }}>
          <Outlet />
        </Box>
      </Box>
    </Stack>
  );
};
