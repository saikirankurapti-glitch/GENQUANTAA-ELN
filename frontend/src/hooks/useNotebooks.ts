import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { notebookService } from '../services/notebook.service';
import { NotebookEntryCreate, NotebookEntryUpdate } from '../types/notebook';

export const useNotebookEntries = (
  page = 1, 
  pageSize = 20, 
  experimentId?: string,
  entryType?: string,
  search?: string
) => {
  return useQuery({
    queryKey: ['notebooks', { page, pageSize, experimentId, entryType, search }],
    queryFn: () => notebookService.getNotebookEntries(page, pageSize, experimentId, entryType, search),
    placeholderData: (previousData) => previousData,
  });
};

export const useNotebookEntry = (id: string) => {
  return useQuery({
    queryKey: ['notebook', id],
    queryFn: () => notebookService.getNotebookEntry(id),
    enabled: !!id,
  });
};

export const useCreateNotebookEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: NotebookEntryCreate) => notebookService.createNotebookEntry(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] });
    },
  });
};

export const useUpdateNotebookEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: NotebookEntryUpdate }) => notebookService.updateNotebookEntry(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['notebook', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['notebooks'] });
    },
  });
};

export const useDeleteNotebookEntry = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => notebookService.deleteNotebookEntry(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notebooks'] });
    },
  });
};
