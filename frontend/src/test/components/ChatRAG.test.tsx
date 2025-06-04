import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { vi } from 'vitest';
import { ToastProvider } from '../../contexts/ToastContext';
import ChatRAG from '../../components/ChatRAG';
import '@testing-library/jest-dom';

// Mock fetch
const mockFetch = vi.fn();
global.fetch = mockFetch;

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

describe('ChatRAG Component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders chat interface', () => {
    renderWithProviders(<ChatRAG sessionId="test-session" />);
    
    expect(screen.getByText('AskRAG Chat')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('Ask a question...')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('sends message and displays response', async () => {
    const mockResponse = {
      answer: 'Test response',
      sources: ['doc1.pdf', 'doc2.pdf']
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve(mockResponse),
    });

    renderWithProviders(<ChatRAG sessionId="test-session" />);
    
    const input = screen.getByPlaceholderText('Ask a question...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);
    
    // Check that user message is displayed
    expect(screen.getByText('Test question')).toBeInTheDocument();
    
    // Wait for assistant response
    await waitFor(() => {
      expect(screen.getByText('Test response')).toBeInTheDocument();
    });
    
    // Check that sources are displayed
    expect(screen.getByText('Sources: doc1.pdf, doc2.pdf')).toBeInTheDocument();
  });

  it('handles send error and shows toast', async () => {
    mockFetch.mockRejectedValueOnce(new Error('Network error'));

    renderWithProviders(<ChatRAG sessionId="test-session" />);
    
    const input = screen.getByPlaceholderText('Ask a question...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);
    
    // Check that user message is displayed
    expect(screen.getByText('Test question')).toBeInTheDocument();
    
    // Wait for error handling
    await waitFor(() => {
      expect(screen.getByText('Network error')).toBeInTheDocument();
    });
  });

  it('disables input and button while loading', async () => {
    // Mock a slow response
    mockFetch.mockImplementationOnce(() => 
      new Promise(resolve => setTimeout(() => resolve({
        ok: true,
        json: () => Promise.resolve({ answer: 'Response', sources: [] })
      }), 100))
    );

    renderWithProviders(<ChatRAG sessionId="test-session" />);
    
    const input = screen.getByPlaceholderText('Ask a question...');
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);
    
    // Check loading state
    expect(input).toBeDisabled();
    expect(screen.getByText('...')).toBeInTheDocument();
  });

  it('prevents sending empty messages', () => {
    renderWithProviders(<ChatRAG sessionId="test-session" />);
    
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.click(sendButton);
    
    // Should not make any fetch calls
    expect(mockFetch).not.toHaveBeenCalled();
  });

  it('clears input after successful send', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: () => Promise.resolve({ answer: 'Response', sources: [] }),
    });

    renderWithProviders(<ChatRAG sessionId="test-session" />);
    
    const input = screen.getByPlaceholderText('Ask a question...') as HTMLInputElement;
    const sendButton = screen.getByRole('button', { name: /send/i });
    
    fireEvent.change(input, { target: { value: 'Test question' } });
    fireEvent.click(sendButton);
    
    await waitFor(() => {
      expect(input.value).toBe('');
    });
  });
});
