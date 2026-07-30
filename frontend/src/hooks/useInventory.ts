import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { inventoryService } from '../services/inventory.service';
import { InventoryItemCreate, InventoryItemUpdate, InventoryReceiveRequest, InventoryIssueRequest } from '../types/inventory';

export const useInventory = (
  page = 1, 
  pageSize = 20, 
  categoryId?: string,
  supplierId?: string,
  storageLocationId?: string,
  status?: string,
  isLowStock?: boolean,
  search?: string
) => {
  return useQuery({
    queryKey: ['inventory', { page, pageSize, categoryId, supplierId, storageLocationId, status, isLowStock, search }],
    queryFn: () => inventoryService.getInventory(page, pageSize, categoryId, supplierId, storageLocationId, status, isLowStock, search),
    placeholderData: (previousData) => previousData,
  });
};

export const useInventoryItem = (id: string) => {
  return useQuery({
    queryKey: ['inventoryItem', id],
    queryFn: () => inventoryService.getInventoryItem(id),
    enabled: !!id,
  });
};

export const useCreateInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (data: InventoryItemCreate) => inventoryService.createInventoryItem(data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

export const useUpdateInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InventoryItemUpdate }) => inventoryService.updateInventoryItem(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inventoryItem', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

export const useDeleteInventoryItem = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => inventoryService.deleteInventoryItem(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

export const useReceiveInventory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InventoryReceiveRequest }) => inventoryService.receiveInventory(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inventoryItem', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};

export const useIssueInventory = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: InventoryIssueRequest }) => inventoryService.issueInventory(id, data),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['inventoryItem', variables.id] });
      queryClient.invalidateQueries({ queryKey: ['inventory'] });
    },
  });
};
