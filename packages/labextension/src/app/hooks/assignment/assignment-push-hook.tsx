import { useMutation, useQueryClient } from '@tanstack/react-query';
import { useMutationStatus } from '../../../widget';
import { HTTPError } from '../../../services/request.service';
import { pushAssignment } from '../../../services/git.service';
import { RepoType } from '../../components/utils/repo-type';
import { LectureDetailDto } from '../../../model/lectureDetailDto';

const successMessages: Record<RepoType, string> = {
  source:
    'Your changes have been saved successfully. The notebooks & files will now be pushed to the repository, and the updates will be visible to your students.',
  release: '',
  user: '',
  autograde: '',
  feedback: '',
  edit: ''
};

export function useAssignmentPush() {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();

  const pushAssignmentMutation = useMutation({
    mutationFn: async (variables: {
      assignmentId: number;
      lecture: LectureDetailDto;
      repoType: RepoType;
      commitMessage?: string;
      selectedFiles?: string[];
      selectedDir?: string;
      showSuccessMessage?: boolean;
    }) => {
      await pushAssignment(
        variables.lecture.id,
        variables.assignmentId,
        variables.repoType,
        variables.commitMessage,
        variables.selectedFiles
      );
    },
    onSuccess: async (data, variables) => {
      await Promise.all([
        queryClient.invalidateQueries({
          queryKey: [
            'files',
            variables.lecture.code,
            variables.assignmentId,
            variables.selectedDir
          ]
        }),
        queryClient.invalidateQueries({
          queryKey: [
            'remote-repo-status',
            variables.lecture.code,
            variables.assignmentId,
            variables.selectedDir
          ]
        })
      ]);
      if (variables.showSuccessMessage) {
        setStatus({
          status: 'success',
          message: successMessages[variables.repoType]
        });
      }
    },
    onError: (error: HTTPError) =>
      setStatus({
        status: 'error',
        message: error?.message || 'Error saving assignment.'
      })
  });

  const handlePushAssignment = (
    assignmentId: number,
    lecture: LectureDetailDto,
    repoType: RepoType,
    commitMessage?: string,
    selectedFiles?: string[],
    selectedDir?: string,
    showSuccessMessage?: boolean
  ) => {
    pushAssignmentMutation.mutate({
      lecture,
      assignmentId,
      repoType,
      commitMessage,
      selectedFiles,
      selectedDir,
      showSuccessMessage
    });
  };
  return { handlePushAssignment };
}
