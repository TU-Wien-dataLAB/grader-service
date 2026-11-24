import React, { useEffect, useMemo, useRef, useState } from 'react';
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
import {
  getPulledSubmissionFiles,
  getSubmissionById,
  restoreLatestSubmission
} from '../../../../services/queries/submissions.query';
import { lectureQuery } from '../../../../services/queries/lectures.queries';
import { useFiles } from '../../../hooks/submissions/get-uploaded-files-hook';
import {
  createOrOverrideEditRepository,
  pushSubmissionFiles
} from '../../../../services/git.service';
import { queryClient, useMutationStatus } from '../../../../widget';
import { SuccessBanner } from '../../ui/success-banner';
import { ErrorBanner } from '../../ui/error-banner';
import { assignmentQuery } from '../../../../services/queries/assignments.queries';
import { RestoreSubmissionDialog } from './restore-submission';
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger
} from '../../../shadcn-components/ui/tooltip';
import { collectPaths } from './utils';
import { useFilesChanged } from './use-files-status-hook';

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

  const [openRestoreConfirmationDialog, setOpenRestoreConfirmationDialog] =
    useState<boolean>(false);

  const { data: submission } = useQuery(
    getSubmissionById(lectureId, assignmentId, submissionId)
  );
  const { data: lecture } = useQuery(lectureQuery(lectureId));

  const path = useMemo(
    () =>
      `${lectureBasePath}${lecture?.code}/edit/${assignmentId}/${submissionId}`,
    [lecture, assignmentId]
  );

  const { data: files = [], refetch: refetchFiles } = useFiles(path);
  const filePaths = useMemo(() => collectPaths(files), [files]);
  const { resetBaselines, anyChanged, clearBaselines } =
    useFilesChanged(filePaths);

  const clearBaselinesRef = useRef(clearBaselines);

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
      queryClient.invalidateQueries({
        queryKey: ['submissionsById', submissionId]
      });

      resetBaselines();
      queryClient.invalidateQueries({
        queryKey: ['submissionFiles', submissionId]
      });
    },
    onError: () => {
      setStatus({
        message: 'Failed to push submission files. Please, try again!',
        status: 'error'
      });
    }
  });

  const { refetch: refetchPullFiles } = useQuery(
    getPulledSubmissionFiles(lectureId, assignmentId, submissionId)
  );

  const createOrOverrideEditRepositoryMutation = useMutation({
    mutationFn: async () => {
      await createOrOverrideEditRepository(
        lectureId,
        assignmentId,
        submissionId
      );
    },
    onSuccess() {
      queryClient.invalidateQueries({
        queryKey: ['submissionById', submissionId]
      });
      refetchPullFiles().then(() => refetchFiles());
    }
  });

  const { refetch: refetchRestoreSubmission } = useQuery(
    restoreLatestSubmission(lectureId, assignmentId, submission?.commit_hash)
  );

  useEffect(() => {
    openInFileBrowser(path);
  }, [path]);

  useEffect(() => {
    clearBaselinesRef.current = clearBaselines;
  }, [clearBaselines]);

  useEffect(() => {
    return () => clearBaselinesRef.current();
  }, []);

  return (
    <>
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
          <h2 className={'text-2xl font-bold leading-[32px]'}>
            Edit submission
          </h2>
        </div>

        {status.status === 'success' && (
          <SuccessBanner message={status.message} />
        )}
        {status.status === 'error' && <ErrorBanner message={status.message} />}

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
              <Button
                onClick={() => setOpenRestoreConfirmationDialog(true)}
                variant="outline"
              >
                Restore latest submission
              </Button>
            )}
          </div>
          {submission?.edited ? (
            <div>
              <SubmissionFiles files={files} isEditMode />
              <div className="flex flex-start gap-4 mt-4">
                <Tooltip>
                  <TooltipTrigger disabled={anyChanged}>
                    <Button
                      onClick={() => pushSubmissionFilesMutation.mutate()}
                      variant="default"
                      disabled={!anyChanged}
                    >
                      Replace submission
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    No changes have been made to the submission yet.
                  </TooltipContent>
                </Tooltip>

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

      {openRestoreConfirmationDialog && (
        <RestoreSubmissionDialog
          openDialog={openRestoreConfirmationDialog}
          setOpenDialog={setOpenRestoreConfirmationDialog}
          handleRestoreSubmission={refetchRestoreSubmission}
        />
      )}
    </>
  );
};

export default EditSubmission;
