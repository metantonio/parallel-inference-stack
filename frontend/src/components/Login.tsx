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
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 flex items-center justify-center p-4">
            <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20 w-full max-w-md">
                <h1 className="text-3xl font-bold text-white mb-6 text-center">
                    Parallel Inference
                </h1>

                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-white font-semibold mb-2">
                            Username
                        </label>
                        <input
                            type="text"
                            value={username}
                            onChange={(e) => setUsername(e.target.value)}
                            className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter username"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-white font-semibold mb-2">
                            Password
                        </label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            placeholder="Enter password"
                            required
                        />
                    </div>

                    {error && (
                        <div className="text-red-300 text-sm bg-red-500/20 p-3 rounded-lg border border-red-500/30">
                            {error}
                        </div>
                    )}

                    <button
                        type="submit"
                        disabled={loading}
                        className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                    >
                        {loading ? 'Signing in...' : 'Sign In'}
                    </button>

                    <div className="text-center text-gray-400 text-sm">
                        Use <code className="text-blue-300">testuser</code> / <code className="text-blue-300">password123</code>
                    </div>
                </form>
            </div>
        </div>
    );
}
