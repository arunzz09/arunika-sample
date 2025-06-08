import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 3000,
    proxy: {
      '/add_location': 'http://localhost:5001',
      '/get_locations': 'http://localhost:5001'
    }
  },
  build: {
    outDir: '../dist'
  }
});