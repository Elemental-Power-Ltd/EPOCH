import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 8760,
    proxy: {
      // rewrite requests to /api/optimisation/* to localhost:8761/*
      '/api/optimisation': {
        target: 'http://localhost:8761',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/optimisation/, '')
      },
      // rewrite requests to /api/data/* to localhost:8762/*
      '/api/data': {
        target: 'http://localhost:8762',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/data/, '')
      }
    }
  }
});
