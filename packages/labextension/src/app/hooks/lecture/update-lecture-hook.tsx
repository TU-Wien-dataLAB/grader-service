import { useMutation, useQueryClient } from '@tanstack/react-query';
import { updateLecture } from '../../../services/lectures.service';
import { useMutationStatus } from '../../../widget';
import { LectureUpdateDto } from '../../../model/lectureUpdateDto';

export const useUpdateLecture = () => {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();

  const mutateLecture = useMutation({
    mutationFn: async (variables: {
      name: string;
      complete: boolean;
      lectureId: number;
    }) => {
      const updatedLecture: LectureUpdateDto = {
        name: variables.name,
        complete: variables.complete
      };
      return updateLecture(updatedLecture, variables.lectureId);
    },
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ['lectures'] });
      setStatus({
        status: 'success',
        message: 'Your changes have been saved successfully!'
      });
    },
    onError: (error: any) =>
      setStatus({
        status: 'error',
        message: error.message || error.error.message
      })
  });
  return { mutateLecture };
};
