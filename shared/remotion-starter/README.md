# Bundled Remotion starter

This starter is intentionally neutral. It renders one video with optional canonical m-edit caption segments and exposes all visual choices through props. It does not install dependencies automatically.

After scaffolding and explicit authorization for package installation:

```bash
npm install
npm run studio
```

Copy or link trusted media into `public/m-edit-assets/` and use a project-relative path in input props. Include the complete `src/`, props JSON, caption JSON, source asset, and lockfile in the preview render recipe.

Copy `props.example.json`, set source metadata and caption data, and pass it to Remotion with `--props`. Width, height, FPS, fit, caption position, typography, colors, and background are all props rather than fixed creator defaults.
