import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { 
  healthCheck, 
  getDocuments, 
  uploadDocument, 
  deleteDocument,
  sendChatMessage,
  getChatHistory 
} from '../services/api';

// Health check hook
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health'],
    queryFn: healthCheck,
    refetchInterval: 30000, // Check every 30 seconds
  });
};

// Document hooks
export const useDocuments = () => {
  return useQuery({
    queryKey: ['documents'],
    queryFn: getDocuments,
  });
};

export const useUploadDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: uploadDocument,
    onSuccess: () => {
      // Invalidate documents query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

export const useDeleteDocument = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: deleteDocument,
    onSuccess: () => {
      // Invalidate documents query to refetch the list
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });
};

// Chat hooks
export const useChatHistory = () => {
  return useQuery({
    queryKey: ['chat-history'],
    queryFn: getChatHistory,
  });
};

export const useSendMessage = () => {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ message, documentIds }: { message: string; documentIds?: string[] }) =>
      sendChatMessage(message, documentIds),
    onSuccess: () => {
      // Invalidate chat history to include the new message
      queryClient.invalidateQueries({ queryKey: ['chat-history'] });
    },
  });
};
