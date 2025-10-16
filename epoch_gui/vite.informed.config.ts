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
  // and then tell vite to open informed.html
  appType: 'mpa',
  server: {
    port: 8759,
    open: '/informed.html',
  },
  build: {
    outDir: 'dist/informed',
    assetsDir: '.',
    rollupOptions: {
      input: resolve(__dirname, 'informed.html'),
      output: {
        inlineDynamicImports: true,
      }
    }
  }
}));
