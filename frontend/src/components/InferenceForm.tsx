/// <reference types="vite/client" />
import React, { useState } from 'react';
import { useQuery, useMutation, useQueryClient, type Query } from '@tanstack/react-query';
import axios, { type InternalAxiosRequestConfig } from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';

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
        <div className="min-h-screen bg-gray-50 p-8">
            <div className="max-w-5xl mx-auto">
                <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-8 mb-8">
                    <div className="flex justify-between items-start mb-8">
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 mb-2">
                                AI Inference System
                            </h1>
                            <p className="text-gray-500">
                                Parallel GPU-based inference with automatic load balancing
                            </p>
                        </div>
                        <button
                            onClick={onLogout}
                            className="px-4 py-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 font-medium rounded-lg transition-colors duration-200"
                        >
                            Sign Out
                        </button>
                    </div>

                    {/* Input Form */}
                    <form onSubmit={handleSubmit} className="space-y-6">
                        <div>
                            <label className="block text-gray-700 font-medium mb-2">
                                Input Data (JSON)
                            </label>
                            <textarea
                                value={inputData}
                                onChange={(e) => setInputData(e.target.value)}
                                className="w-full h-32 px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent font-mono text-sm transition-all duration-200"
                                placeholder='{"text": "Your input here"}'
                            />
                        </div>

                        <div>
                            <label className="block text-gray-700 font-medium mb-2">
                                Priority
                            </label>
                            <div className="relative">
                                <select
                                    value={priority}
                                    onChange={(e) => setPriority(e.target.value as 'high' | 'normal' | 'low')}
                                    className="w-full px-4 py-3 bg-white border border-gray-300 rounded-lg text-gray-900 focus:outline-none focus:ring-2 focus:ring-gray-900 focus:border-transparent appearance-none transition-all duration-200"
                                >
                                    <option value="low">Low</option>
                                    <option value="normal">Normal</option>
                                    <option value="high">High</option>
                                </select>
                                <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-4 text-gray-500">
                                    <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
                                        <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
                                    </svg>
                                </div>
                            </div>
                        </div>

                        <div className="flex gap-4 pt-2">
                            <button
                                type="submit"
                                disabled={submitMutation.isPending}
                                className="flex-1 bg-gray-900 hover:bg-black text-white font-medium py-3 px-6 rounded-lg transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed shadow-sm"
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
                                    className="px-6 py-3 bg-white border border-gray-300 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors duration-200"
                                >
                                    Reset
                                </button>
                            )}
                        </div>
                    </form>

                    {/* Results */}
                    {taskId && (
                        <div className="mt-10 pt-10 border-t border-gray-100 space-y-6">
                            <div className="flex items-center justify-between">
                                <h2 className="text-xl font-bold text-gray-900">
                                    Task Status
                                </h2>
                                <div className="flex items-center gap-4">
                                    <span className="text-gray-500 text-sm">Task ID:</span>
                                    <code className="text-gray-700 bg-gray-100 px-2 py-1 rounded text-sm font-mono border border-gray-200">
                                        {taskId}
                                    </code>
                                </div>
                            </div>

                            <div className="bg-gray-50 rounded-lg border border-gray-200 p-6">
                                {result ? (
                                    <div className="space-y-4">
                                        <div className="flex justify-between items-center">
                                            <span className="text-gray-600 font-medium">Current Status</span>
                                            <span className={`px-3 py-1 rounded-full text-sm font-medium border ${result.status === 'completed' ? 'bg-green-50 text-green-700 border-green-200' :
                                                    result.status === 'failed' ? 'bg-red-50 text-red-700 border-red-200' :
                                                        result.status === 'processing' ? 'bg-yellow-50 text-yellow-700 border-yellow-200' :
                                                            'bg-blue-50 text-blue-700 border-blue-200'
                                                }`}>
                                                {result.status.toUpperCase()}
                                            </span>
                                        </div>

                                        {result.processing_time && (
                                            <div className="flex justify-between items-center border-t border-gray-200 pt-4">
                                                <span className="text-gray-600">Processing Time</span>
                                                <span className="text-gray-900 font-mono">
                                                    {result.processing_time.toFixed(2)}s
                                                </span>
                                            </div>
                                        )}

                                        {result.status === 'processing' && (
                                            <div className="flex items-center gap-3 text-yellow-700 bg-yellow-50 p-3 rounded border border-yellow-100">
                                                <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                                                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                                                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                                                </svg>
                                                <span className="text-sm font-medium">Processing on GPU...</span>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="text-center text-gray-500 py-4">
                                        Loading status...
                                    </div>
                                )}
                            </div>

                            {/* Result Display */}
                            {result?.result && (
                                <div>
                                    <h3 className="text-lg font-bold text-gray-900 mb-3">Result Output</h3>
                                    <div className="bg-gray-900 rounded-lg p-4 overflow-x-auto shadow-inner">
                                        <pre className="text-green-400 font-mono text-sm">
                                            {JSON.stringify(result.result, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            )}

                            {/* Error Display */}
                            {result?.error && (
                                <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                                    <h3 className="text-lg font-bold text-red-800 mb-2">Error</h3>
                                    <p className="text-red-700">{result.error}</p>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Submit Error */}
                    {submitMutation.isError && (
                        <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-4">
                            <p className="text-red-700 text-sm">
                                <span className="font-bold">Error:</span> {(submitMutation.error as any)?.response?.data?.detail || 'Failed to submit request'}
                            </p>
                        </div>
                    )}
                </div>

                {/* Info Cards */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="text-gray-500 text-xs font-bold tracking-wider uppercase mb-2">Latency</div>
                        <div className="text-gray-900 text-3xl font-bold">~50ms</div>
                        <div className="text-gray-400 text-sm mt-1">Average response time</div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="text-gray-500 text-xs font-bold tracking-wider uppercase mb-2">Throughput</div>
                        <div className="text-gray-900 text-3xl font-bold">1000+</div>
                        <div className="text-gray-400 text-sm mt-1">Requests per second</div>
                    </div>

                    <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
                        <div className="text-gray-500 text-xs font-bold tracking-wider uppercase mb-2">GPU Pool</div>
                        <div className="text-gray-900 text-3xl font-bold">3 GPUs</div>
                        <div className="text-gray-400 text-sm mt-1">Active workers</div>
                    </div>
                </div>
            </div>
        </div>
    );
}
