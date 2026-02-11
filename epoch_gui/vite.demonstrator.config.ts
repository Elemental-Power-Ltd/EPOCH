import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';


export default defineConfig({
    plugins: [react()],
    server: {
        host: true,
        port: 80,
        open: '/demonstrator.html',
        proxy: {
            '/api': {
                target: 'http://localhost:8763',
                changeOrigin: true,
                rewrite: (path) => path.replace(/^\/api/, '')
            }
        }
    },
});