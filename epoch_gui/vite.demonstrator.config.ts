import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import {resolve} from "node:path";


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
    base: "/",
    build: {
        outDir: "dist-demonstrator",
        emptyOutDir: true,
        rollupOptions: {
            input: {
                demonstrator: resolve(__dirname, "demonstrator.html")
            },
        },
    }
});