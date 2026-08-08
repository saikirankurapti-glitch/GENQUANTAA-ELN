import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { experimentService } from '../services/experiment.service';
import type { QAComment, QACommentCreate } from '../types';

export const useQAComments = (experimentId?: string) => {
  return useQuery({
    queryKey: ['qa-comments', experimentId],
    queryFn: () => (experimentId ? experimentService.getQAComments(experimentId) : Promise.resolve([])),
    enabled: !!experimentId,
    refetchInterval: 6000, // Poll every 6 seconds for live collaborative review
  });
};

export const useAddQAComment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ experimentId, data }: { experimentId: string; data: QACommentCreate }) =>
      experimentService.addQAComment(experimentId, data),
    onSuccess: (_, { experimentId }) => {
      queryClient.invalidateQueries({ queryKey: ['qa-comments', experimentId] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });
};

export const useReplyQAComment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ experimentId, commentId, comment }: { experimentId: string; commentId: string; comment: string }) =>
      experimentService.replyQAComment(experimentId, commentId, comment),
    onSuccess: (_, { experimentId }) => {
      queryClient.invalidateQueries({ queryKey: ['qa-comments', experimentId] });
      queryClient.invalidateQueries({ queryKey: ['notifications'] });
      queryClient.invalidateQueries({ queryKey: ['unread-notifications-count'] });
    },
  });
};

export const useResolveQAComment = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      experimentId,
      commentId,
      status,
      resolutionNote,
    }: {
      experimentId: string;
      commentId: string;
      status: 'resolved' | 'open';
      resolutionNote?: string;
    }) => experimentService.resolveQAComment(experimentId, commentId, status, resolutionNote),
    onSuccess: (_, { experimentId }) => {
      queryClient.invalidateQueries({ queryKey: ['qa-comments', experimentId] });
    },
  });
};
