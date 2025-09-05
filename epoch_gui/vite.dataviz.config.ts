import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import { resolve } from 'path';
import { viteSingleFile } from 'vite-plugin-singlefile';

export default defineConfig(({ command }) => ({
  plugins: [
    react(),
    // we only include viteSingleFile for build, not for dev
    command === 'build' ? viteSingleFile() : undefined,
  ].filter(Boolean),
  base: './',
  // we treat this as a 'mpa' so we can open any html files
  // and then tell vite to open dataviz.html
  appType: 'mpa',
  publicDir: 'public/dataviz',
  server: {
    port: 8759,
    open: '/dataviz.html',
  },
  build: {
    outDir: 'dist/dataviz',
    assetsDir: '.',
    rollupOptions: {
      input: resolve(__dirname, 'dataviz.html'),
      output: {
        inlineDynamicImports: true,
      }
    }
  }
}));
