import React, { useEffect, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Link, useLocation, useParams } from 'react-router';
import { lectureQuery } from '../../../services/queries/lectures.queries';
import { ArrowLeft } from 'lucide-react';
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger
} from '../../shadcn-components/ui/tabs';
import {
  assignmentStatus,
  gradingType
} from '../../components/utils/assignment-metadata';
import { assignmentQuery } from '../../../services/queries/assignments.queries';
import {
  buildFileBasePath,
  lectureBasePath,
  openInFileBrowser
} from '../../../services/local-file.service';
import { selectedDirQuery } from '../../../services/queries/file.queries';
import NewSubmission from '../../components/grader-service/submissions/new-submission';
import { SubmissionsView } from '../../components/grader-service/submissions/submissions-view';

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
  const [showNewSubmissionForm, setShowNewSubmissionForm] =
    useState<boolean>(false);

  useEffect(() => {
    openInFileBrowser(
      `${lectureBasePath}${lecture?.id}/${selectedDir}/${assignmentId}`
    );
  }, [assignmentId, lecture?.code, selectedDir]);

  const currentPath = buildFileBasePath(lecture.code, 'source', assignmentId);

  console.log('ggg: ', currentPath);

  return (
    <div className={'flex p-6 flex-col items-start gap-6 w-full bg-background'}>
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
        className={'flex-col w-full gap-6'}
      >
        <TabsList variant="line" className={'border-b-border border-b w-full'}>
          <TabsTrigger value="notebooks-and-files">
            Notebooks & files
          </TabsTrigger>
          <TabsTrigger value="submissions">Submissions</TabsTrigger>
          <TabsTrigger value="statistics">Statistics</TabsTrigger>
        </TabsList>
        <TabsContent value="notebooks-and-files">
          Notebooks and files
        </TabsContent>
        <TabsContent value="submissions">
          {showNewSubmissionForm ? (
            <NewSubmission
              currentPath={currentPath}
              setShowNewSubmissionForm={setShowNewSubmissionForm}
            />
          ) : (
            <SubmissionsView
              setShowNewSubmissionForm={setShowNewSubmissionForm}
            />
          )}
        </TabsContent>
        <TabsContent value="statistics">Statistics</TabsContent>
      </Tabs>
    </div>
  );
};
