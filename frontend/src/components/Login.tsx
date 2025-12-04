import React, { useState } from 'react';
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface LoginProps {
    onLogin: (token: string) => void;
}

export default function Login({ onLogin }: LoginProps) {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setLoading(true);

        try {
            const params = new URLSearchParams();
            params.append('username', username);
            params.append('password', password);

            const response = await axios.post(`${API_URL}/token`, params);

            const token = response.data.access_token;
            localStorage.setItem('auth_token', token);
            onLogin(token);
        } catch (err: any) {
            console.error('Login failed:', err);
            const errorMessage = err.response?.data?.detail || 'Invalid username or password';
            setError(errorMessage);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 w-full max-w-md">
                <h1 className="text-2xl font-bold text-gray-900 mb-2 text-center">
                    Parallel Inference
                </h1>
                <p className="text-gray-500 text-center mb-8 text-sm">
                    Sign in to access the system
                </p>

                <form onSubmit={handleSubmit} className="space-y-5">
                    <div>
                        <label className="block text-gray-700 text-sm font-medium mb-1.5">
                            Username
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all duration-200"
                            placeholder="Enter username"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-gray-700 text-sm font-medium mb-1.5">
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-2.5 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent transition-all duration-200"
                            placeholder="Enter password"
                            required
                        />
                    </div>

                    {error && (
                        <div className="text-red-600 text-sm bg-red-50 p-3 rounded-lg border border-red-100">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gray-900 hover:bg-black text-white font-medium py-2.5 px-6 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>

                    <div className="text-center text-gray-400 text-xs mt-6">
                        Use <code className="text-gray-600 bg-gray-100 px-1 py-0.5 rounded">testuser</code> / <code className="text-gray-600 bg-gray-100 px-1 py-0.5 rounded">password123</code>
                    </div>
                </form>
            </div>
        </div>
    );
}
