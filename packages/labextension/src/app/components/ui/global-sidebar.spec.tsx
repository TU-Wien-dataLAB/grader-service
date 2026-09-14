import React from 'react';
import { render, screen } from '@testing-library/react';
import { GlobalSidebar } from './global-sidebar';
import { createAllProvidersWrapper } from '../../../test/utils';
import { getAllLectures } from '../../../services/lectures.service';
import { SidebarProvider } from '../../shadcn-components/ui/sidebar';

jest.mock('../../../services/lectures.service');

const mockedGetAllLectures = jest.mocked(getAllLectures);

test('global sidebar ', async () => {
  const Wrapper = createAllProvidersWrapper();
  mockedGetAllLectures.mockResolvedValue([
    { id: 1, code: 'CS101', name: 'Intro to CS', complete: false },
    { id: 2, code: 'CS202', name: 'Intro to ASE', complete: false }
  ]);

  render(
    <SidebarProvider>
      <GlobalSidebar />
    </SidebarProvider>,
    { wrapper: Wrapper }
  );
  expect(await screen.findByText('CS101')).toBeInTheDocument();
  expect(await screen.findByText('CS202')).toBeInTheDocument();
  expect(await screen.findByText('Intro to CS')).toBeInTheDocument();
  expect(await screen.findByText('Intro to ASE')).toBeInTheDocument();
});
