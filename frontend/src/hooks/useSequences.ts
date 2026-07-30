import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { sequenceService } from '../services/sequence.service';
import { SequenceCreate, SequenceUpdate } from '../types/sequence';

export const useSequences = (
  page = 1, 
  pageSize = 20, 
  sequenceType?: string,
  status?: string,
  experimentId?: string,
  sampleId?: string,
  search?: string
) => {
  return useQuery({
    queryKey: ['sequences', { page, pageSize, sequenceType, status, experimentId, sampleId, search }],
    queryFn: () => sequenceService.getSequences(page, pageSize, sequenceType, status, experimentId, sampleId, search),
    placeholderData: (previousData) => previousData,
  });
};

export const useSequence = (id: string) => {
  return useQuery({
    queryKey: ['sequence', id],
    queryFn: () => sequenceService.getSequence(id),
    enabled: !!id,
  });
};

export const useCreateSequence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: SequenceCreate) => sequenceService.createSequence(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sequences'] });
    },
  });
};

export const useUpdateSequence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SequenceUpdate }) => sequenceService.updateSequence(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['sequence', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['sequences'] });
    },
  });
};

export const useDeleteSequence = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => sequenceService.deleteSequence(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sequences'] });
    },
  });
};
