import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { experimentService } from '../services/experiment.service';
import { ExperimentCreate, ExperimentUpdate } from '../types/experiment';

export const useExperiments = (
  page = 1, 
  pageSize = 20, 
  projectId?: string,
  search?: string, 
  status?: string, 
  priority?: string
) => {
  return useQuery({
    queryKey: ['experiments', { page, pageSize, projectId, search, status, priority }],
    queryFn: () => experimentService.getExperiments(page, pageSize, projectId, search, status, priority),
    placeholderData: (previousData) => previousData,
  });
};

export const useExperiment = (id: string) => {
  return useQuery({
    queryKey: ['experiment', id],
    queryFn: () => experimentService.getExperiment(id),
    enabled: !!id,
  });
};

export const useCreateExperiment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ExperimentCreate) => experimentService.createExperiment(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useUpdateExperiment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ExperimentUpdate }) => experimentService.updateExperiment(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['experiment', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};

export const useDeleteExperiment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => experimentService.deleteExperiment(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['experiments'] });
      queryClient.invalidateQueries({ queryKey: ['dashboard'] });
    },
  });
};
