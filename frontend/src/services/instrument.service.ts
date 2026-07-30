import { apiClient } from './apiClient';
import { 
  InstrumentListResponse, InstrumentDetail, InstrumentCreate, InstrumentUpdate, InstrumentRead
} from '../types/instrument';

export const instrumentService = {
  getInstruments: async (
    page = 1, 
    pageSize = 20, 
    instrumentTypeId?: string,
    operationalStatus?: string,
    availabilityStatus?: string,
    isCalibrationOverdue?: boolean,
    search?: string
  ): Promise<InstrumentListResponse> => {
    const params = new URLSearchParams({
      page: page.toString(),
      page_size: pageSize.toString(),
    });
    
    if (instrumentTypeId) params.append('instrument_type_id', instrumentTypeId);
    if (operationalStatus) params.append('operational_status', operationalStatus);
    if (availabilityStatus) params.append('availability_status', availabilityStatus);
    if (isCalibrationOverdue !== undefined) params.append('is_calibration_overdue', isCalibrationOverdue.toString());
    if (search) params.append('search', search);

    const response = await apiClient.get<InstrumentListResponse>(`/instruments?${params.toString()}`);
    return response.data;
  },

  getInstrument: async (id: string): Promise<InstrumentDetail> => {
    const response = await apiClient.get<InstrumentDetail>(`/instruments/${id}`);
    return response.data;
  },

  createInstrument: async (data: InstrumentCreate): Promise<InstrumentRead> => {
    const response = await apiClient.post<InstrumentRead>('/instruments', data);
    return response.data;
  },

  updateInstrument: async (id: string, data: InstrumentUpdate): Promise<InstrumentRead> => {
    const response = await apiClient.put<InstrumentRead>(`/instruments/${id}`, data);
    return response.data;
  },

  deleteInstrument: async (id: string): Promise<void> => {
    await apiClient.delete(`/instruments/${id}`);
  }
};
