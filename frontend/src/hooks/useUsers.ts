import { useQuery } from '@tanstack/react-query';
import { userService } from '../services/user.service';

export const useUsers = (
  page = 1, 
  pageSize = 20, 
  search?: string
) => {
  return useQuery({
    queryKey: ['users', { page, pageSize, search }],
    queryFn: () => userService.getUsers(page, pageSize, search),
    placeholderData: (previousData) => previousData,
  });
};
