import React, { useEffect, useState } from 'react';
import { selectedDirQuery } from '../../../services/queries/files.queries';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useNavigation, useParams } from 'react-router';
import { assignmentQuery } from '../../../services/queries/assignments.queries';
import {
  lectureBasePath,
  openInFileBrowser
} from '../../../services/local-file.service';
import { lectureQuery } from '../../../services/queries/lectures.queries';
import { ArrowLeft } from 'lucide-react';
import {
  assignmentStatus,
  gradingType
} from '../../components/utils/assignment-metadata';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '../../shadcn-components/ui/tabs';
import { FilesOverview } from '../../components/grader-service/notebooks-and-files/files-overview';

export const Assignment = () => {
  const params = useParams();

  const lectureId = Number(params.id);
  const assignmentId = Number(params.aid);

  const { data: selectedDir } = useQuery(selectedDirQuery());
  const { data: lecture } = useQuery(lectureQuery(lectureId));
  const { data: assignment } = useQuery(
    assignmentQuery(lectureId, assignmentId)
  );

  const location = useLocation();
  const { activeTab } = (location.state as { activeTab?: string }) ?? {};

  const [currentTab, setCurrentTab] = useState(
    activeTab ?? 'notebooks-and-files'
  );

  useEffect(() => {
    openInFileBrowser(
      `${lectureBasePath}${lecture?.code}/${selectedDir}/${assignmentId}`
    );
  }, [assignmentId, lecture?.code]);
  const navigation = useNavigation();

  console.log('navigation state:', navigation.state, navigation.location);

  return (
    <div className={'flex p-6 flex-col items-start gap-6 w-full'}>
      <div className={'flex items-center gap-6 self-stretch'}>
        <div className={'flex items-center gap-4'}>
          <Link to={`/lectures/${lectureId}`}>
            <ArrowLeft className={'size-4 cursor-pointer text-primary'} />
          </Link>
          <div className={'flex flex-col justify-center items-start gap-1'}>
            <h1 className={'text-2xl font-bold'}>{assignment?.name}</h1>
            <div className={'flex items-center gap-4'}>
              {assignmentStatus(assignment?.status)}
              {gradingType(
                assignment?.settings.autograde_type,
                assignment?.status === 'complete'
              )}
            </div>
          </div>
        </div>
      </div>
      <Tabs
        value={currentTab}
        onValueChange={setCurrentTab}
        className={'flex-col w-full'}
      >
        <TabsList variant="line" className={'border-b-border border-b'}>
          <TabsTrigger value="notebooks-and-files">
            Notebooks & files
          </TabsTrigger>
          <TabsTrigger value="submissions">Submissions</TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
        </TabsList>
        <TabsContent value="notebooks-and-files">
          <FilesOverview />
        </TabsContent>

        <TabsContent value="submissions">
          <div>Submissions</div>
        </TabsContent>
        <TabsContent value="statistics">Statistics</TabsContent>
      </Tabs>
    </div>
  );
};
