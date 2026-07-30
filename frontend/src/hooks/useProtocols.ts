import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { protocolService } from '../services/protocol.service';
import { ProtocolCreate, ProtocolUpdate, ProtocolApprovalCreate } from '../types/protocol';

export const useProtocols = (
  page = 1, 
  pageSize = 20, 
  category?: string,
  status?: string,
  ownerId?: string,
  search?: string
) => {
  return useQuery({
    queryKey: ['protocols', { page, pageSize, category, status, ownerId, search }],
    queryFn: () => protocolService.getProtocols(page, pageSize, category, status, ownerId, search),
    placeholderData: (previousData) => previousData,
  });
};

export const useProtocol = (id: string) => {
  return useQuery({
    queryKey: ['protocol', id],
    queryFn: () => protocolService.getProtocol(id),
    enabled: !!id,
  });
};

export const useCreateProtocol = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: ProtocolCreate) => protocolService.createProtocol(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['protocols'] });
    },
  });
};

export const useUpdateProtocol = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProtocolUpdate }) => protocolService.updateProtocol(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['protocol', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['protocols'] });
    },
  });
};

export const useDeleteProtocol = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => protocolService.deleteProtocol(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['protocols'] });
    },
  });
};

export const useApproveProtocol = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: ProtocolApprovalCreate }) => protocolService.approveProtocol(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['protocol', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['protocols'] });
    },
  });
};
