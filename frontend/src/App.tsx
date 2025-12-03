import React, { useState, useEffect } from 'react';
import InferenceForm from './components/InferenceForm';
import Login from './components/Login';

function App() {
    const [token, setToken] = useState<string | null>(localStorage.getItem('auth_token'));

    useEffect(() => {
        // Check if token exists in local storage on mount
        const storedToken = localStorage.getItem('auth_token');
        if (storedToken) {
            setToken(storedToken);
        }
    }, []);

    const handleLogin = (newToken: string) => {
        setToken(newToken);
    };

    const handleLogout = () => {
        localStorage.removeItem('auth_token');
        setToken(null);
    };

    if (!token) {
        return <Login onLogin={handleLogin} />;
    }

    return <InferenceForm onLogout={handleLogout} />;
}

export default App;
