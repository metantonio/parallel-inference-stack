import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen } from '@testing-library/react';
import App from '../App';

// Mock child components
vi.mock('../components/Login', () => ({
    default: ({ onLogin }: { onLogin: (token: string) => void }) => (
        <div data-testid="login-component">
            <button onClick={() => onLogin('mock-token')}>Mock Login</button>
        </div>
    ),
}));

vi.mock('../components/InferenceForm', () => ({
    default: ({ onLogout }: { onLogout: () => void }) => (
        <div data-testid="inference-form-component">
            <button onClick={onLogout}>Mock Logout</button>
        </div>
    ),
}));

describe('App Component', () => {
    beforeEach(() => {
        // Clear localStorage before each test
        localStorage.clear();
    });

    it('renders Login component when no token exists', () => {
        render(<App />);
        expect(screen.getByTestId('login-component')).toBeInTheDocument();
    });

    it('renders InferenceForm when token exists in localStorage', () => {
        localStorage.setItem('auth_token', 'mock-token');
        render(<App />);
        expect(screen.getByTestId('inference-form-component')).toBeInTheDocument();
    });

    it('switches to InferenceForm after login', () => {
        const { rerender } = render(<App />);

        // Initially shows login
        expect(screen.getByTestId('login-component')).toBeInTheDocument();

        // Simulate login
        const loginButton = screen.getByText('Mock Login');
        loginButton.click();

        // Re-render to see updated state
        rerender(<App />);

        // Should now show inference form
        expect(screen.queryByTestId('login-component')).not.toBeInTheDocument();
    });

    it('clears token on logout', () => {
        localStorage.setItem('auth_token', 'mock-token');
        const { rerender } = render(<App />);

        // Should show inference form
        expect(screen.getByTestId('inference-form-component')).toBeInTheDocument();

        // Simulate logout
        const logoutButton = screen.getByText('Mock Logout');
        logoutButton.click();

        // Token should be cleared
        expect(localStorage.getItem('auth_token')).toBeNull();

        // Re-render
        rerender(<App />);

        // Should show login again
        expect(screen.getByTestId('login-component')).toBeInTheDocument();
    });
});
