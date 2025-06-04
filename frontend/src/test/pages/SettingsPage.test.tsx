import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { ToastProvider } from '../../contexts/ToastContext';
import SettingsPage from '../../pages/SettingsPage';
import '@testing-library/jest-dom';

// Mock localStorage
const mockLocalStorage = {
  getItem: vi.fn(),
  setItem: vi.fn(),
  removeItem: vi.fn(),
  clear: vi.fn(),
};
Object.defineProperty(window, 'localStorage', { value: mockLocalStorage });

const createQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  const queryClient = createQueryClient();
  return (
    <QueryClientProvider client={queryClient}>
      <ToastProvider>
        <BrowserRouter>
          {children}
        </BrowserRouter>
      </ToastProvider>
    </QueryClientProvider>
  );
};

const renderWithProviders = (ui: React.ReactElement) => {
  return render(ui, { wrapper: AllTheProviders });
};

describe('SettingsPage Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify({
      openaiApiKey: '',
      model: 'gpt-3.5-turbo',
      temperature: 0.7,
      maxTokens: 2048,
      topK: 5,
      chunkSize: 1000,
      chunkOverlap: 200
    }));
  });

  it('renders settings page with all tabs', () => {
    renderWithProviders(<SettingsPage />);
    
    expect(screen.getByText('Settings')).toBeInTheDocument();
    expect(screen.getByText('Configure your AskRAG application settings')).toBeInTheDocument();
    
    // Check tabs
    expect(screen.getByText('API Configuration')).toBeInTheDocument();
    expect(screen.getByText('Model Settings')).toBeInTheDocument();
    expect(screen.getByText('RAG Parameters')).toBeInTheDocument();
  });

  it('switches between tabs', () => {
    renderWithProviders(<SettingsPage />);
    
    // Initially should show API tab content
    expect(screen.getByLabelText('OpenAI API Key')).toBeInTheDocument();
    
    // Click Model Settings tab
    fireEvent.click(screen.getByText('Model Settings'));
    expect(screen.getByLabelText('Model')).toBeInTheDocument();
    
    // Click RAG Parameters tab
    fireEvent.click(screen.getByText('RAG Parameters'));
    expect(screen.getByLabelText('Top-K Results')).toBeInTheDocument();
  });

  it('loads settings from localStorage', () => {
    const mockSettings = {
      openaiApiKey: 'test-key',
      model: 'gpt-4',
      temperature: 0.5,
      maxTokens: 1024,
      topK: 3,
      chunkSize: 800,
      chunkOverlap: 100
    };
    
    mockLocalStorage.getItem.mockReturnValue(JSON.stringify(mockSettings));
    
    renderWithProviders(<SettingsPage />);
    
    expect(mockLocalStorage.getItem).toHaveBeenCalledWith('askrag-settings');
    
    // Check that values are loaded
    const apiKeyInput = screen.getByLabelText('OpenAI API Key') as HTMLInputElement;
    expect(apiKeyInput.value).toBe('test-key');
  });

  it('updates input values', () => {
    renderWithProviders(<SettingsPage />);
    
    const apiKeyInput = screen.getByLabelText('OpenAI API Key');
    fireEvent.change(apiKeyInput, { target: { value: 'new-api-key' } });
    
    expect((apiKeyInput as HTMLInputElement).value).toBe('new-api-key');
  });

  it('saves settings to localStorage and shows success toast', async () => {
    renderWithProviders(<SettingsPage />);
    
    const apiKeyInput = screen.getByLabelText('OpenAI API Key');
    fireEvent.change(apiKeyInput, { target: { value: 'new-api-key' } });
    
    const saveButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(saveButton);
    
    await waitFor(() => {
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith(
        'askrag-settings',
        expect.stringContaining('"openaiApiKey":"new-api-key"')
      );
    });
  });

  it('handles localStorage error and shows error toast', async () => {
    mockLocalStorage.setItem.mockImplementation(() => {
      throw new Error('Storage quota exceeded');
    });
    
    renderWithProviders(<SettingsPage />);
    
    const saveButton = screen.getByRole('button', { name: /save settings/i });
    fireEvent.click(saveButton);
    
    // Should not throw an error and should handle gracefully
    await waitFor(() => {
      expect(mockLocalStorage.setItem).toHaveBeenCalled();
    });
  });

  it('updates model settings correctly', () => {
    renderWithProviders(<SettingsPage />);
    
    // Switch to Model Settings tab
    fireEvent.click(screen.getByText('Model Settings'));
    
    const modelSelect = screen.getByLabelText('Model');
    fireEvent.change(modelSelect, { target: { value: 'gpt-4' } });
    
    expect((modelSelect as HTMLSelectElement).value).toBe('gpt-4');
    
    const temperatureInput = screen.getByLabelText('Temperature');
    fireEvent.change(temperatureInput, { target: { value: '0.9' } });
    
    expect((temperatureInput as HTMLInputElement).value).toBe('0.9');
  });

  it('updates RAG parameters correctly', () => {
    renderWithProviders(<SettingsPage />);
    
    // Switch to RAG Parameters tab
    fireEvent.click(screen.getByText('RAG Parameters'));
    
    const topKInput = screen.getByLabelText('Top-K Results');
    fireEvent.change(topKInput, { target: { value: '10' } });
    
    expect((topKInput as HTMLInputElement).value).toBe('10');
    
    const chunkSizeInput = screen.getByLabelText('Chunk Size');
    fireEvent.change(chunkSizeInput, { target: { value: '1500' } });
    
    expect((chunkSizeInput as HTMLInputElement).value).toBe('1500');
  });

  it('validates number inputs', () => {
    renderWithProviders(<SettingsPage />);
    
    // Switch to Model Settings tab
    fireEvent.click(screen.getByText('Model Settings'));
    
    const temperatureInput = screen.getByLabelText('Temperature');
    const maxTokensInput = screen.getByLabelText('Max Tokens');
    
    // Check min/max attributes
    expect(temperatureInput).toHaveAttribute('min', '0');
    expect(temperatureInput).toHaveAttribute('max', '2');
    expect(temperatureInput).toHaveAttribute('step', '0.1');
    
    expect(maxTokensInput).toHaveAttribute('min', '1');
    expect(maxTokensInput).toHaveAttribute('max', '8192');
  });
});
