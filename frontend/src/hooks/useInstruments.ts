import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { instrumentService } from '../services/instrument.service';
import { InstrumentCreate, InstrumentUpdate } from '../types/instrument';

export const useInstruments = (
  page = 1, 
  pageSize = 20, 
  instrumentTypeId?: string,
  operationalStatus?: string,
  availabilityStatus?: string,
  isCalibrationOverdue?: boolean,
  search?: string
) => {
  return useQuery({
    queryKey: ['instruments', { page, pageSize, instrumentTypeId, operationalStatus, availabilityStatus, isCalibrationOverdue, search }],
    queryFn: () => instrumentService.getInstruments(page, pageSize, instrumentTypeId, operationalStatus, availabilityStatus, isCalibrationOverdue, search),
    placeholderData: (previousData) => previousData,
  });
};

export const useInstrument = (id: string) => {
  return useQuery({
    queryKey: ['instrument', id],
    queryFn: () => instrumentService.getInstrument(id),
    enabled: !!id,
  });
};

export const useCreateInstrument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InstrumentCreate) => instrumentService.createInstrument(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
    },
  });
};

export const useUpdateInstrument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InstrumentUpdate }) => instrumentService.updateInstrument(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['instrument', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
    },
  });
};

export const useDeleteInstrument = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => instrumentService.deleteInstrument(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['instruments'] });
    },
  });
};
