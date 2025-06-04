import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { vi } from 'vitest';
import { ToastProvider } from '../../contexts/ToastContext';
import DocumentUpload from '../../components/DocumentUpload';
import '@testing-library/jest-dom';

// Mock fetch
global.fetch = vi.fn();

const AllTheProviders = ({ children }: { children: React.ReactNode }) => {
  return (
    <ToastProvider>
      <BrowserRouter>
        {children}
      </BrowserRouter>
    </ToastProvider>
  );
};

const renderWithProviders = (component: React.ReactElement) => {
  return render(component, { wrapper: AllTheProviders });
};

describe('DocumentUpload', () => {
  const mockOnUpload = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
    (fetch as any).mockClear();
  });

  it('renders upload form', () => {
    renderWithProviders(<DocumentUpload onUpload={mockOnUpload} />);
    
    expect(screen.getByRole('heading', { name: /upload document/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /upload/i })).toBeInTheDocument();
    expect(screen.getByDisplayValue('')).toBeInTheDocument(); // file input
  });

  it('shows error for invalid file type', async () => {
    renderWithProviders(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('button', { name: /upload/i }).previousElementSibling as HTMLInputElement;
    const invalidFile = new File(['content'], 'test.xyz', { type: 'application/unknown' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [invalidFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    fireEvent.click(screen.getByRole('button', { name: /upload/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/format non supporté/i)).toBeInTheDocument();
    });
  });

  it('uploads valid file successfully', async () => {
    (fetch as any).mockResolvedValue({
      ok: true,
      json: () => Promise.resolve({ success: true }),
    });

    renderWithProviders(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('button', { name: /upload/i }).previousElementSibling as HTMLInputElement;
    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    fireEvent.click(screen.getByRole('button', { name: /upload/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/fichier uploadé avec succès/i)).toBeInTheDocument();
    });
    
    expect(mockOnUpload).toHaveBeenCalledWith('test.pdf');
  });

  it('shows loading state during upload', async () => {
    (fetch as any).mockImplementation(() => new Promise(resolve => setTimeout(resolve, 100)));

    renderWithProviders(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('button', { name: /upload/i }).previousElementSibling as HTMLInputElement;
    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    fireEvent.click(screen.getByRole('button', { name: /upload/i }));
    
    expect(screen.getByRole('button', { name: /uploading/i })).toBeInTheDocument();
  });

  it('handles upload error', async () => {
    (fetch as any).mockResolvedValue({
      ok: false,
      json: () => Promise.resolve({ detail: 'Server error' }),
    });

    renderWithProviders(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('button', { name: /upload/i }).previousElementSibling as HTMLInputElement;
    const validFile = new File(['content'], 'test.pdf', { type: 'application/pdf' });
    
    Object.defineProperty(fileInput, 'files', {
      value: [validFile],
      writable: false,
    });
    
    fireEvent.change(fileInput);
    fireEvent.click(screen.getByRole('button', { name: /upload/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/server error/i)).toBeInTheDocument();
    });
  });

  it('accepts valid file formats', () => {
    renderWithProviders(<DocumentUpload onUpload={mockOnUpload} />);
    
    const fileInput = screen.getByRole('button', { name: /upload/i }).previousElementSibling as HTMLInputElement;
    expect(fileInput).toHaveAttribute('accept', '.pdf,.docx,.txt,.md,.html');
  });
});
