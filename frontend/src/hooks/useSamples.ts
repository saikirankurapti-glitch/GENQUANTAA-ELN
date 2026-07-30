import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sampleService } from '../services/sample.service';
import { SampleCreate, SampleUpdate } from '../types/sample';

export const useSamples = (
  page = 1, 
  pageSize = 20, 
  experimentId?: string,
  status?: string, 
  search?: string
) => {
  return useQuery({
    queryKey: ['samples', { page, pageSize, experimentId, status, search }],
    queryFn: () => sampleService.getSamples(page, pageSize, experimentId, status, search),
    placeholderData: (previousData) => previousData,
  });
};

export const useSample = (id: string) => {
  return useQuery({
    queryKey: ['sample', id],
    queryFn: () => sampleService.getSample(id),
    enabled: !!id,
  });
};

export const useCreateSample = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SampleCreate) => sampleService.createSample(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useUpdateSample = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SampleUpdate }) => sampleService.updateSample(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['sample', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useDeleteSample = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => sampleService.deleteSample(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['samples'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};
