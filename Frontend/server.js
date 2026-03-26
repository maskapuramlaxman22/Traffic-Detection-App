#!/usr/bin/env node
/**
 * Simple proxy server that:
 * 1. Serves React static files from build/
 * 2. Proxies /api/* requests to http://localhost:5000
 */

const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const path = require('path');

const app = express();
const PORT = 3000;
const API_BACKEND = 'http://localhost:5000';

// Proxy all /api/* requests to the backend
app.use('/api', createProxyMiddleware({
  target: API_BACKEND,
  changeOrigin: true,
  ws: true, // Enable WebSocket proxying
  onError: (err, req, res) => {
    console.error(`Proxy error for ${req.url}:`, err.message);
    res.status(503).json({ error: 'Backend service unavailable' });
  },
  onProxyRes: (proxyRes, req, res) => {
    proxyRes.headers['Access-Control-Allow-Origin'] = '*';
    proxyRes.headers['Cache-Control'] = 'no-cache';
  }
}));

// Serve React static files
app.use(express.static(path.join(__dirname, 'build')));

// SPA fallback: send index.html for all non-API routes
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'build', 'index.html'));
});

app.listen(PORT, () => {
  console.log(`🚀 Frontend server running on http://localhost:${PORT}`);
  console.log(`📡 API proxied to ${API_BACKEND}`);
});
