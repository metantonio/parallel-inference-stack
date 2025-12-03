/// <reference types="vite/client" />
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient, type Query } from '@tanstack/react-query';
import axios, { type InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// API client
const api = axios.create({
    baseURL: API_URL,
    timeout: 30000,
    headers: {
        'Content-Type': 'application/json',
    },
});

// Add auth token to requests
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('auth_token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

interface InferenceRequest {
    data: Record<string, any>;
    priority?: 'high' | 'normal' | 'low';
    model_version?: string;
    timeout?: number;
}

interface InferenceResponse {
    task_id: string;
    status: string;
    estimated_wait_time?: number;
    queue_position?: number;
}

interface TaskResult {
    task_id: string;
    status: string;
    result?: Record<string, any>;
    error?: string;
    created_at: string;
    started_at?: string;
    completed_at?: string;
    processing_time?: number;
}

interface InferenceFormProps {
    onLogout: () => void;
}

export default function InferenceForm({ onLogout }: InferenceFormProps) {
    const [inputData, setInputData] = useState('{"text": "Hello, world!"}');
    const [priority, setPriority] = useState<'high' | 'normal' | 'low'>('normal');
    const [taskId, setTaskId] = useState<string | null>(null);
    const queryClient = useQueryClient();

    // Submit inference mutation
    const submitMutation = useMutation({
        mutationFn: async (request: InferenceRequest) => {
            const response = await api.post<InferenceResponse>('/inference', request);
            return response.data;
        },
        onSuccess: (data: InferenceResponse) => {
            setTaskId(data.task_id);
            queryClient.invalidateQueries({ queryKey: ['tasks'] });
        },
    });

    // Poll for result
    const { data: result } = useQuery({
        queryKey: ['task', taskId],
        queryFn: async () => {
            if (!taskId) return null;
            const response = await api.get<TaskResult>(`/inference/${taskId}`);
            return response.data;
        },
        enabled: !!taskId,
        refetchInterval: (query: Query<any, any, any, any>) => {
            // Stop polling if completed or failed
            const data = query.state.data as TaskResult | null;
            if (data?.status === 'completed' || data?.status === 'failed') {
                return false;
            }
            return 2000; // Poll every 2 seconds
        },
    });

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        try {
            const data = JSON.parse(inputData);
            await submitMutation.mutateAsync({
                data,
                priority,
                timeout: 60,
            });
        } catch (error) {
            console.error('Invalid JSON:', error);
            alert('Invalid JSON input');
        }
    };

    const handleReset = () => {
        setTaskId(null);
        setInputData('{"text": "Hello, world!"}');
        queryClient.invalidateQueries({ queryKey: ['tasks'] });
    };

    return (
        <div className="min-h-screen bg-gradient-to-br from-gray-900 via-blue-900 to-purple-900 p-8">
            <div className="max-w-4xl mx-auto">
                <div className="bg-white/10 backdrop-blur-lg rounded-2xl shadow-2xl p-8 border border-white/20">
                    <h1 className="text-4xl font-bold text-white mb-2">
                        AI Inference System
                    </h1>
                    <p className="text-blue-200 mb-8">
                        Parallel GPU-based inference with automatic load balancing
                    </p>

                    <div className="absolute top-8 right-8">
                        <button
                            onClick={onLogout}
                            className="px-4 py-2 bg-white/10 hover:bg-white/20 text-white text-sm font-semibold rounded-lg transition-all duration-200 border border-white/30"
                        >
                            Sign Out
                        </button>
                    </div>

                    {/* Input Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-white font-semibold mb-2">
                                Input Data (JSON)
                            </label>
                            <textarea
                                value={inputData}
                                onChange={(e) => setInputData(e.target.value)}
                                className="w-full h-32 px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                                placeholder='{"text": "Your input here"}'
                            />
                        </div>

                        <div>
                            <label className="block text-white font-semibold mb-2">
                                Priority
                            </label>
                            <select
                                value={priority}
                                onChange={(e) => setPriority(e.target.value as 'high' | 'normal' | 'low')}
                                className="w-full px-4 py-3 bg-white/10 border border-white/30 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                            >
                                <option value="low" className="bg-gray-800">Low</option>
                                <option value="normal" className="bg-gray-800">Normal</option>
                                <option value="high" className="bg-gray-800">High</option>
                            </select>
                        </div>

                        <div className="flex gap-4">
                            <button
                                type="submit"
                                disabled={submitMutation.isPending}
                                className="flex-1 bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-bold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none shadow-lg"
                            >
                                {submitMutation.isPending ? (
                                    <span className="flex items-center justify-center">
                                        <svg className="animate-spin h-5 w-5 mr-2" viewBox="0 0 24 24">
                                            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                        </svg>
                                        Submitting...
                                    </span>
                                ) : (
                                    'Submit Inference'
                                )}
                            </button>

                            {taskId && (
                                <button
                                    type="button"
                                    onClick={handleReset}
                                    className="px-6 py-3 bg-white/10 hover:bg-white/20 text-white font-semibold rounded-lg transition-all duration-200 border border-white/30"
                                >
                                    Reset
                                </button>
                            )}
                        </div>
                    </form>

                    {/* Results */}
                    {taskId && (
                        <div className="mt-8 space-y-4">
                            <div className="bg-white/5 border border-white/20 rounded-lg p-6">
                                <h2 className="text-2xl font-bold text-white mb-4">
                                    Task Status
                                </h2>

                                <div className="space-y-3">
                                    <div className="flex justify-between items-center">
                                        <span className="text-gray-300">Task ID:</span>
                                        <code className="text-blue-300 font-mono text-sm bg-black/30 px-3 py-1 rounded">
                                            {taskId}
                                        </code>
                                    </div>

                                    {result && (
                                        <>
                                            <div className="flex justify-between items-center">
                                                <span className="text-gray-300">Status:</span>
                                                <span className={`px-3 py-1 rounded-full text-sm font-semibold ${result.status === 'completed' ? 'bg-green-500/20 text-green-300' :
                                                    result.status === 'failed' ? 'bg-red-500/20 text-red-300' :
                                                        result.status === 'processing' ? 'bg-yellow-500/20 text-yellow-300' :
                                                            'bg-blue-500/20 text-blue-300'
                                                    }`}>
                                                    {result.status.toUpperCase()}
                                                </span>
                                            </div>

                                            {result.processing_time && (
                                                <div className="flex justify-between items-center">
                                                    <span className="text-gray-300">Processing Time:</span>
                                                    <span className="text-white font-semibold">
                                                        {result.processing_time.toFixed(2)}s
                                                    </span>
                                                </div>
                                            )}

                                            {result.status === 'processing' && (
                                                <div className="flex items-center gap-3 text-yellow-300">
                                                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                    </svg>
                                                    <span>Processing on GPU...</span>
                                                </div>
                                            )}
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* Result Display */}
                            {result?.result && (
                                <div className="bg-white/5 border border-white/20 rounded-lg p-6">
                                    <h3 className="text-xl font-bold text-white mb-4">Result</h3>
                                    <pre className="bg-black/40 text-green-300 p-4 rounded-lg overflow-x-auto font-mono text-sm border border-green-500/30">
                                        {JSON.stringify(result.result, null, 2)}
                                    </pre>
                                </div>
                            )}

                            {/* Error Display */}
                            {result?.error && (
                                <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-6">
                                    <h3 className="text-xl font-bold text-red-300 mb-2">Error</h3>
                                    <p className="text-red-200">{result.error}</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Error Display */}
                    {submitMutation.isError && (
                        <div className="mt-4 bg-red-500/10 border border-red-500/30 rounded-lg p-4">
                            <p className="text-red-300">
                                Error: {(submitMutation.error as any)?.response?.data?.detail || 'Failed to submit request'}
                            </p>
                        </div>
                    )}
                </div>

                {/* Info Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
                    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                        <div className="text-blue-300 text-sm font-semibold mb-1">LATENCY</div>
                        <div className="text-white text-2xl font-bold">~50ms</div>
                        <div className="text-gray-400 text-sm mt-1">Average response time</div>
                    </div>

                    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                        <div className="text-green-300 text-sm font-semibold mb-1">THROUGHPUT</div>
                        <div className="text-white text-2xl font-bold">1000+</div>
                        <div className="text-gray-400 text-sm mt-1">Requests per second</div>
                    </div>

                    <div className="bg-white/10 backdrop-blur-lg rounded-xl p-6 border border-white/20">
                        <div className="text-purple-300 text-sm font-semibold mb-1">GPU POOL</div>
                        <div className="text-white text-2xl font-bold">3 GPUs</div>
                        <div className="text-gray-400 text-sm mt-1">Active workers</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
