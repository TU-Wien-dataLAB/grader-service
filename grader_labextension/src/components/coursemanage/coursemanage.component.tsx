// Copyright (c) 2022, TU Wien
// All rights reserved.
//
// This source code is licensed under the BSD-style license found in the
// LICENSE file in the root directory of this source tree.

import * as React from 'react';
import { Lecture } from '../../model/lecture';
import { Scope, UserPermissions } from '../../services/permission.service';
import { useRouteLoaderData, Link as RouterLink } from 'react-router-dom';
import {Box, ListItem, ListItemProps, ListItemText, Paper, Tab, Tabs, Typography} from '@mui/material';

export interface ICourseManageProps {
  // lectures: Array<Lecture>;
  root: HTMLElement;
}

interface ListItemLinkProps extends ListItemProps {
  to: string;
  lecture: Lecture;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const CustomTabPanel = (props: TabPanelProps) => {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`simple-tabpanel-${index}`}
      aria-labelledby={`simple-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ p: 3 }}>
          <Typography>{children}</Typography>
        </Box>
      )}
    </div>
  );
}

function a11yProps(index: number) {
  return {
    id: `simple-tab-${index}`,
    'aria-controls': `simple-tabpanel-${index}`,
  };
}
const ListItemLink = (props: ListItemLinkProps) => {
  const { to, ...other } = props;
  return (
      <ListItem component={RouterLink as any} to={to} {...other} >
          <Paper sx={{width: '100%'}}>
              <ListItemText primary={props.lecture.name} sx={{ m: 2 }}/>
          </Paper>

      </ListItem>
  );
}


export const CourseManageComponent = (props: ICourseManageProps) => {
  const allLectures = useRouteLoaderData("root") as {lectures: Lecture[], completedLectures: Lecture[]};
  const [tab, setTab] = React.useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setTab(newValue);
  };
  return (
    <Box sx={{ width: '100%' }}>
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={tab} onChange={handleChange} aria-label="basic tabs example">
        <Tab label="Active Lectures" {...a11yProps(0)} />
        <Tab label="Archive" {...a11yProps(1)} />
      </Tabs>
      </Box>
        <CustomTabPanel index={0} value={tab}>
            {allLectures.lectures
                .filter(el => UserPermissions.getScope(el) > Scope.student)
                .map((el, index) => (
                  <ListItemLink to={`/lecture/${el.id}`} lecture={el} />
        ))}
        </CustomTabPanel>
        <CustomTabPanel index={1} value={tab}>
            {allLectures.completedLectures
                .filter(el => UserPermissions.getScope(el) > Scope.student)
                .map((el, index) => (
                  <ListItemLink to={`/lecture/${el.id}`} lecture={el} />
                ))}
        </CustomTabPanel>
    </Box>
  );
};
