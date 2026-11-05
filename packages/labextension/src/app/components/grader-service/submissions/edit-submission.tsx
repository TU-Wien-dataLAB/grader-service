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
import { useMutation, useQuery } from '@tanstack/react-query';
import { getSubmissionById } from '../../../../services/queries/submissions.query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import { useFiles } from '../../../hooks/submissions/get-uploaded-files-hook';
import {
  createOrOverrideEditRepository,
  pullSubmissionFiles,
  pushSubmissionFiles
} from '../../../../services/git.service';
import { queryClient, useMutationStatus } from '../../../../widget';
import { SuccessBanner } from '../../ui/success-banner';
import { ErrorBanner } from '../../ui/error-banner';
import { assignmentQuery } from '../../../../services/queries/assignments.queries';

const EditSubmission = () => {
  const params = useParams();
  const lectureId = Number(params.lid);
  const assignmentId = Number(params.aid);
  const submissionId = Number(params.sid);
  const navigate = useNavigate();
  const { status, setStatus } = useMutationStatus();
  const { data: assignment } = useQuery(
    assignmentQuery(lectureId, assignmentId)
  );

  const { data: submission, refetch: refetchSubmission } = useQuery(
    getSubmissionById(lectureId, assignmentId, submissionId)
  );
  const { data: lecture } = useQuery(lectureQuery(lectureId));

  const path = useMemo(
    () =>
      `${lectureBasePath}${lecture?.code}/edit/${assignmentId}/${submissionId}`,
    [lecture, assignmentId]
  );

  const { data: files = [], refetch: refetchFiles } = useFiles(path);

  const goToSubmissionsView = () => {
    navigate(`/lectures/${lectureId}/assignments/${assignmentId}`, {
      state: { activeTab: 'submissions' }
    });
  };

  const pushSubmissionFilesMutation = useMutation({
    mutationFn: async () => {
      await pushSubmissionFiles(lectureId, assignmentId, submission);
    },
    onSuccess: () => {
      setStatus({
        message: 'You successfully push submission files.',
        status: 'success'
      });
      queryClient.invalidateQueries({ queryKey: ['submissions'] });
    },
    onError: () => {
      setStatus({
        message: 'Failed to push submission files. Please, try again!',
        status: 'error'
      });
    }
  });

  const pullSubmissionFilesMutation = useMutation({
    mutationFn: async () => {
      await pullSubmissionFiles(lectureId, assignmentId, submissionId);
    },
    onSuccess: () => {
      refetchFiles();
    },
    onError: () => {
      setStatus({
        message: 'Failed to pull submission files. Please, try again!',
        status: 'error'
      });
    }
  });

  const createOrOverrideEditRepositoryMutation = useMutation({
    mutationFn: async () => {
      await createOrOverrideEditRepository(
        lectureId,
        assignmentId,
        submissionId
      );
    }
  });

  const restoreLatestSubmission = async () => {
    await refetchSubmission();
    refetchFiles();
  };

  useEffect(() => {
    openInFileBrowser(path);
  }, [path]);

  useEffect(() => {
    createOrOverrideEditRepositoryMutation.mutate();
    pullSubmissionFilesMutation.mutate();
  }, []);

  return (
    <div
      className={
        'flex flex-col items-start gap-4 self-stretch p-6 w-full overflow-auto'
      }
    >
      {status.status === 'success' && (
        <SuccessBanner message={status.message} />
      )}
      {status.status === 'error' && <ErrorBanner message={status.message} />}
      <div className="flex gap-4 items-center w-full">
        <ArrowLeft
          onClick={goToSubmissionsView}
          className={'size-4 cursor-pointer text-primary'}
        />
        <h2 className={'text-2xl font-bold leading-[32px]'}>Edit submission</h2>
      </div>

      {submission && (
        <div className="w-full">
          <SubmissionDetailInfo
            submission={submission}
            assignment={assignment}
            isEditMode
          />
        </div>
      )}

      <div className="py-6 w-full">
        <div className="flex justify-between mb-2 w-full">
          <h3 className="text-xl font-bold mb-2">Submission</h3>
          {files && (
            <Button onClick={restoreLatestSubmission} variant="outline">
              Restore latest submission
            </Button>
          )}
        </div>
        {submission?.edited ? (
          <div>
            <SubmissionFiles files={files} />
            <div className="flex flex-start gap-4 mt-4">
              <Button
                onClick={() => pushSubmissionFilesMutation.mutate()}
                variant="default"
              >
                Replace submission
              </Button>
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
            <Button
              onClick={() => createOrOverrideEditRepositoryMutation.mutate()}
              className="w-fit"
              variant="default"
            >
              Start editing
            </Button>
          </div>
        )}
      </div>
    </div>
  );
};

export default EditSubmission;
