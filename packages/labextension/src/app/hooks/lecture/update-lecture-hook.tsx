import { useMutation, useQueryClient } from '@tanstack/react-query';
import { Lecture } from '../../../model/lecture';
import { updateLecture } from '../../../services/lectures.service';
import { useMutationStatus } from '../../../widget';

export const useUpdateLecture = () => {
  const queryClient = useQueryClient();
  const { setStatus } = useMutationStatus();

  const mutateLecture = useMutation({
    mutationFn: async (variables: {
      name: string;
      complete: boolean;
      lecture: Lecture;
    }) => {
      const updatedLecture: Lecture = {
        ...variables.lecture,
        name: variables.name,
        complete: variables.complete
      };
      return updateLecture(updatedLecture);
    },
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ['activeLectures'] }),
        queryClient.invalidateQueries({ queryKey: ['completedLectures'] })
      ]);
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
