import React, { useEffect, useMemo } from 'react';
import SubmissionFiles from './submission-files';
import { ArrowLeft } from 'lucide-react';
import SubmissionDetailInfo from './submission-detail-info';
import { EmptyState } from '../../utils/empty-state';
import { EmptyIcon } from '../../../../assets/empty-icon';
import { Button } from '../../../shadcn-components/ui/button';
import { useNavigate, useParams } from 'react-router';
import {
  lectureBasePath,
  openInFileBrowser
} from '../../../../services/local-file.service';
import { useQuery } from '@tanstack/react-query';
import { getSubmissionById } from '../../../../services/queries/submissions.query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import { useFiles } from '../../../hooks/submissions/get-uploaded-files-hook';

const EditSubmission = () => {
  const params = useParams();
  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const submissionId = Number(params.sid);
  const navigate = useNavigate();

  const { data: submission } = useQuery(
    getSubmissionById(lectureId, assignmentId, submissionId)
  );
  const { data: lecture } = useQuery(lectureQuery(lectureId));

  const path = useMemo(
    () =>
      `${lectureBasePath}${lecture.code}/edit/${assignmentId}/${submissionId}`,
    [lecture, assignmentId]
  );

  const { data: files = [] } = useFiles(path);

  const goToSubmissionsView = () => {
    navigate(`/lectures/${lectureId}/assignments/${assignmentId}`, {
      state: { activeTab: 'submissions' }
    });
  };

  useEffect(() => {
    openInFileBrowser(path);
  }, [path]);

  return (
    <div
      className={
        'flex flex-col items-start gap-4 self-stretch p-6 w-full overflow-auto'
      }
    >
      <div className="flex gap-4 items-center w-full">
        <ArrowLeft
          onClick={goToSubmissionsView}
          className={'size-4 cursor-pointer text-primary'}
        />
        <h2 className={'text-2xl font-bold leading-[32px]'}>Edit submission</h2>
      </div>

      {submission && (
        <div className="w-full">
          <SubmissionDetailInfo submission={submission} isEditMode />
        </div>
      )}

      <div className="py-6 w-full">
        <div className="flex justify-between mb-2 w-full">
          <h3 className="text-xl font-bold mb-2">Submission</h3>
          {files && (
            <Button variant="outline">Restore latest submission</Button>
          )}
        </div>
        {files ? (
          <div>
            <SubmissionFiles files={files} />
            <div className="flex flex-start gap-4 mt-4">
              <Button variant="default">Replace submission</Button>
              <Button variant="outline" onClick={goToSubmissionsView}>
                Cancel
              </Button>
            </div>
          </div>
        ) : (
          <div className="mt-10 flex flex-col items-center">
            <EmptyState
              title={'No entries found'}
              icon={<EmptyIcon />}
              description={
                'Start editing to load the submission and make changes.'
              }
            />
            <Button className="w-fit" variant="default">
              Start editing
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EditSubmission;
