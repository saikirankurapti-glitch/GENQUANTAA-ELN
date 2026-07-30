import React, { createContext, useContext, useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { authService } from '../services/auth.service';
import { User, LoginRequest, RegisterRequest } from '../types/auth';

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  login: (credentials: LoginRequest) => Promise<void>;
  register: (data: RegisterRequest) => Promise<void>;
  logout: () => void;
  refetchUser: () => Promise<any>;
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = useQueryClient();
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    !!localStorage.getItem('eln_access_token')
  );

  const { data: user, isLoading, refetch } = useQuery({
    queryKey: ['currentUser'],
    queryFn: authService.getCurrentUser,
    enabled: isAuthenticated,
  });

  const loginMutation = useMutation({
    mutationFn: authService.login,
    onSuccess: (data) => {
      localStorage.setItem('eln_access_token', data.access_token);
      localStorage.setItem('eln_refresh_token', data.refresh_token);
      setIsAuthenticated(true);
      refetch();
    },
  });

  const registerMutation = useMutation({
    mutationFn: authService.register,
  });

  useEffect(() => {
    const handleUnauthorized = () => {
      localStorage.removeItem('eln_access_token');
      localStorage.removeItem('eln_refresh_token');
      setIsAuthenticated(false);
      queryClient.clear();
    };

    window.addEventListener('auth:unauthorized', handleUnauthorized);
    return () => {
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [queryClient]);

  const logout = () => {
    try {
      authService.logout().catch(() => {});
    } catch (e) {
      // Ignore network errors on logout
    }
    localStorage.removeItem('eln_access_token');
    localStorage.removeItem('eln_refresh_token');
    setIsAuthenticated(false);
    queryClient.clear();
  };

  const login = async (credentials: LoginRequest) => {
    await loginMutation.mutateAsync(credentials);
  };

  const register = async (data: RegisterRequest) => {
    await registerMutation.mutateAsync(data);
  };

  return (
    <AuthContext.Provider value={{ 
      user: user || null, 
      isLoading: isLoading || loginMutation.isPending || registerMutation.isPending, 
      login, 
      register,
      logout,
      refetchUser: refetch,
      isAuthenticated 
    }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
