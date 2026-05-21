// config.js - API Configuration

const ENV = {
    development: 'http://localhost:8000',
    production: 'https://twoxbet-j42a.onrender.com'
};

// Detect environment based on hostname
const CURRENT_ENV = window.location.hostname === 'localhost' ? 'development' : 'production';
const API_BASE_URL = ENV[CURRENT_ENV];

console.log('[config] Environment:', CURRENT_ENV);
console.log('[config] API URL:', API_BASE_URL);
