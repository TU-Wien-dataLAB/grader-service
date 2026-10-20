import React from 'react';
import SubmissionFiles from './submission-files';
import { ArrowLeft } from 'lucide-react';
import SubmissionDetailInfo from './submission-detail-info';
import { Submission } from '../../../../model/submission';
import { SubmissionFile } from './submission-details-dialog';
import { EmptyState } from '../../utils/empty-state';
import { EmptyIcon } from '../../../../assets/empty-icon';
import { Button } from '../../../shadcn-components/ui/button';
import { useNavigate, useParams } from 'react-router';
import { mockSubmission } from './table-mock-data';

const EditSubmission = () => {
  const files: SubmissionFile[] = [];
  const submission: Submission[] = [];

  const params = useParams();

  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const navigate = useNavigate();

  const goToViewSubmissions = () => {
    navigate(`/lectures/${lectureId}/assignments/${assignmentId}`, {
      state: { activeTab: 'submissions' }
    });
  };

  return (
    <div
      className={
        'flex flex-col items-start gap-4 self-stretch p-6 w-full overflow-auto'
      }
    >
      <div className="flex gap-4 items-center w-full">
        <ArrowLeft
          onClick={goToViewSubmissions}
          className={'size-4 cursor-pointer text-primary'}
        />
        <h2 className={'text-2xl font-bold leading-[32px]'}>Edit submission</h2>
      </div>

      {submission && submission.length >= 0 && (
        <div className="w-full">
          <SubmissionDetailInfo submission={mockSubmission} isEditMode />
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
            <SubmissionFiles files={mockSubmission} />
            <div className="flex flex-start gap-4 mt-4">
              <Button variant="default">Replace submission</Button>
              <Button variant="outline" onClick={goToViewSubmissions}>
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
