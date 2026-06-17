# Static assets

Add PWA icons here before prod build:

- `icon-192.png` (192×192)
- `icon-512.png` (512×512)

Referenced by `vite.config.ts` manifest. Without them the PWA install prompt is degraded
but the app still builds and runs.
