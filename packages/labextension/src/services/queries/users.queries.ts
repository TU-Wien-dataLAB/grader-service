import { queryOptions } from '@tanstack/react-query';
import { getCurrentUser } from '../user.service';

export const getCurrentUserQuery = () =>
  queryOptions({
    queryKey: ['currentUser'],
    queryFn: () => {
      return getCurrentUser();
    }
  });
