import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import Login from '../components/Login';

describe('Login Component', () => {
    it('renders login form', () => {
        const mockOnLogin = vi.fn();
        render(<Login onLogin={mockOnLogin} />);

        expect(screen.getByText(/Parallel Inference/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Enter username/i)).toBeInTheDocument();
        expect(screen.getByPlaceholderText(/Enter password/i)).toBeInTheDocument();
        expect(screen.getByRole('button', { name: /Sign In/i })).toBeInTheDocument();
    });

    it('displays test credentials hint', () => {
        const mockOnLogin = vi.fn();
        render(<Login onLogin={mockOnLogin} />);

        expect(screen.getByText(/testuser/i)).toBeInTheDocument();
        expect(screen.getByText(/password123/i)).toBeInTheDocument();
    });

    it('updates input fields on change', () => {
        const mockOnLogin = vi.fn();
        render(<Login onLogin={mockOnLogin} />);

        const usernameInput = screen.getByPlaceholderText(/Enter username/i) as HTMLInputElement;
        const passwordInput = screen.getByPlaceholderText(/Enter password/i) as HTMLInputElement;

        fireEvent.change(usernameInput, { target: { value: 'testuser' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });

        expect(usernameInput.value).toBe('testuser');
        expect(passwordInput.value).toBe('password123');
    });

    it('shows loading state when submitting', async () => {
        const mockOnLogin = vi.fn();
        render(<Login onLogin={mockOnLogin} />);

        const usernameInput = screen.getByPlaceholderText(/Enter username/i);
        const passwordInput = screen.getByPlaceholderText(/Enter password/i);
        const submitButton = screen.getByRole('button', { name: /Sign In/i });

        fireEvent.change(usernameInput, { target: { value: 'testuser' } });
        fireEvent.change(passwordInput, { target: { value: 'password123' } });

        // Mock axios to prevent actual API call
        vi.mock('axios');

        fireEvent.click(submitButton);

        // Button should show loading state
        await waitFor(() => {
            expect(screen.getByText(/Signing in.../i)).toBeInTheDocument();
        });
    });

    it('requires both username and password', () => {
        const mockOnLogin = vi.fn();
        render(<Login onLogin={mockOnLogin} />);

        const usernameInput = screen.getByPlaceholderText(/Enter username/i);
        const passwordInput = screen.getByPlaceholderText(/Enter password/i);

        expect(usernameInput).toHaveAttribute('required');
        expect(passwordInput).toHaveAttribute('required');
    });
});
