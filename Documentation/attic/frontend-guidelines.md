# LAMB Frontend Guidelines (New Application)

## Introduction

This document provides guidelines and summarizes the setup for the **new** frontend application for LAMB (Learning Assistants Manager and Builder), located in the `frontend/svelte-app` directory. This application was initialized as a fresh SvelteKit project to address deployment issues with the previous version.

## Technology Stack

The frontend is built with the following technologies:

- **Node.js**: v20.18.3
- **npm**: v10.8.2
- **Framework**: Svelte 5 (using Runes) with SvelteKit v2+
- **Build Tool**: Vite v6+
- **CSS Framework**: Tailwind CSS v4+
    - Plugins: `@tailwindcss/forms`, `@tailwindcss/typography`
    - Integration: Via `@tailwindcss/vite` plugin
- **HTTP Client**: Axios v1.8.1
- **Internationalization**: svelte-i18n v4.0.1
- **Type Checking**: JSDoc
- **Linting/Formatting**: ESLint, Prettier
- **Testing**: Vitest, Playwright
- **SvelteKit Adapter**: `@sveltejs/adapter-static`

## Project Setup & Configuration

- **Location**: The project root is `/frontend/svelte-app`.
- **Initialization**: Started from the SvelteKit 'skeleton' template with options for JSDoc types, ESLint, Prettier, Playwright, and Vitest.
- **Build Process**:
    - Command: `npm run build` (executed within `/frontend/svelte-app`)
    - Adapter: Uses `@sveltejs/adapter-static` for generating a static site.
    - Output Directory: Configured in `svelte.config.js` (`adapter.pages` and `adapter.assets`) to output files to `../build` (relative to the project root), resulting in the final build residing in `/frontend/build`.
- **Deployment Base Path**:
    - Configured to be served from the root `/` by the backend (`backend/main.py`).
    - The `kit.paths.base` in `svelte.config.js` has been removed.
    - All generated assets and internal links are automatically generated relative to the root.
    - Backend serving uses specific mounts for SvelteKit build assets (e.g., `/app`, `/img`) and a final catch-all route (`/{full_path:path}`) to serve `index.html` for SPA routing.
- **Rendering Mode**:
    - Configured for Single-Page Application (SPA) mode via `adapter-static`'s `fallback: 'index.html'` option in `svelte.config.js`.
    - Client-side rendering is used; `export const ssr = false` is set in the root `+layout.js`.
- **Tailwind CSS**:
    - Configuration: `tailwind.config.js`
    - Integration: Uses the `@tailwindcss/vite` plugin, configured in `vite.config.js`.
    - Global Styles: Base directives (`@import 'tailwindcss'`, `@plugin`) are included in `src/app.css`, which is imported by the root layout (`src/routes/+layout.svelte`).
- **Runtime Configuration**:
    - A configuration file `static/config.js` is expected.
    - This file is loaded via a `<script>` tag in `src/app.html` using `%sveltekit.assets%/config.js`.
    - It defines a global `window.LAMB_CONFIG` object.
    - Type definition for `window.LAMB_CONFIG` is added in `src/app.d.ts`.
    - The `$lib/config.js` file provides helpers (`getConfig`, `getApiUrl`) to access this configuration safely.

## 6. Routing Strategy

This SvelteKit application is configured as a Single Page Application (SPA) using `@sveltejs/adapter-static` with `fallback: 'index.html'` and served from the root (`/`). The backend (`backend/main.py`) handles serving: it mounts specific asset directories (like `/app`) and uses a catch-all route to serve the `index.html` for any non-API, non-asset path, enabling SPA routing (e.g., refreshing `/assistants`). The primary navigation within the main assistant management section utilizes the `/assistants` path combined with **query parameters** for specific views (e.g., create, detail).

- **Base Path**: The application is served under the root path (`/`). The main assistants section is located at `/assistants`.
- **Navigation**: Instead of only using paths like `/assistants/create` or `/assistants/123`, navigation is handled like:
    - List View: `/assistants`
    - Create View: `/assistants?view=create`
    - Detail View: `/assistants?view=detail&id=123`
- **Implementation**: 
    - The main component for the assistants section (likely `src/routes/assistants/+page.svelte` or similar) listens to the `$page` store's `url.searchParams` to determine the current view (`list`, `create`, `detail`) and the relevant ID.
    - `goto` calls and `<a>` tag `href` attributes should construct URLs using the base path `/assistants` combined with the appropriate query parameters. SvelteKit handles root-relative links correctly without needing `$app/paths.base` when the base is `/`.

This approach aims to simplify server configuration while still providing distinct URLs for different states within the assistants section.

### 5.1. API Endpoint Construction

When making calls to the backend API, be aware of two patterns:

1.  **Standard API Calls (under `/creator`):** Most backend endpoints related to creating/managing assistants, KBs, etc., are expected to be under the `/creator` base path (or whatever is configured in `window.LAMB_CONFIG.api.baseUrl`). Use the `$lib/config.js` helper function for these:
    ```javascript
    import { getApiUrl } from '$lib/config';

    const loginUrl = getApiUrl('/auth/login'); // -> /creator/auth/login (typically)
    ```

2.  **Direct Endpoint Calls:** Certain specific backend endpoints or static assets are accessed directly, *not* under the `/creator` base. You need to construct these URLs manually:
    *   **Core LAMB API (e.g., completions):** Use the `lambServer` base URL defined in `window.LAMB_CONFIG`.
        ```javascript
        import { getConfig } from '$lib/config';

        const config = getConfig();
        const lambServerBase = config?.lambServer;
        if (!lambServerBase) throw new Error('Config missing lambServer');
        const capabilitiesUrl = `${lambServerBase.replace(/\/$/, '')}/lamb/v1/completions/list`;
        ```
    *   **Static Configuration Files (e.g., defaults.json):** Use the `lambServer` base URL to access static configuration files served by the backend.
        ```javascript
        import { getConfig } from '$lib/config';

        const config = getConfig();
        const lambServerBase = config?.api?.lambServer;
        if (!lambServerBase) throw new Error('Config missing lambServer');
        const defaultsUrl = `${lambServerBase.replace(/\/$/, '')}/static/json/defaults.json`;

        // This works in both development and production because:
        // - Backend serves /static from backend/static/ directory
        // - Frontend uses the LAMB server URL to access these files
        // - Files like defaults.json are not copied to frontend build directory
        ```
    Always verify the correct base path required for each specific endpoint.

## Directory Structure (Initial)

```
frontend/
├── build/                   # Build output (generated by `npm run build`)
├── svelte-app/
│   ├── .svelte-kit/         # SvelteKit intermediate files
│   ├── node_modules/        # Project dependencies
│   ├── src/                 # Application source code
│   │   ├── lib/             # Reusable components, utilities, etc. (currently empty)
│   │   ├── routes/          # Application pages and layouts
│   │   │   ├── +layout.js   # Root layout logic (prerender config)
│   │   │   ├── +layout.svelte # Root layout component (imports app.css)
│   │   │   └── +page.svelte # Homepage component (displays debug config)
│   │   ├── app.css          # Global CSS (Tailwind directives)
│   │   ├── app.d.ts         # Global type definitions (incl. window.LAMB_CONFIG)
│   │   └── app.html         # HTML template (loads config.js)
│   ├── static/              # Static assets (copied directly to build)
│   │   └── config.js        # Runtime configuration
│   ├── eslint.config.js     # ESLint configuration
│   ├── package.json         # Project manifest and dependencies
│   ├── svelte.config.js     # SvelteKit configuration (adapter, paths)
│   ├── tailwind.config.js   # Tailwind CSS configuration
│   ├── vite.config.js       # Vite configuration (Tailwind plugin)
│   └── ...                  # Other config files (prettier, jsconfig, etc.)
```

## Getting Started

1.  Navigate to the application directory: `cd frontend/svelte-app`
2.  Install dependencies: `npm install`
3.  Run the development server: `npm run dev`
4.  Build the application for production: `npm run build` (Output will be in `frontend/build`)
5.  Preview the build locally: `npm run preview` (Note: This preview might not perfectly reflect the production serving setup if the preview server doesn't handle root SPA fallbacks).

## 7. CSS and Styling Considerations

### 7.1. Handling Brand Colors and Tailwind Classes

During frontend development, we encountered several important styling considerations:

- **Brand Color Reliability**: The `bg-brand` class defined in `tailwind.config.js` may experience compilation or runtime issues that prevent it from being properly applied. When critical UI elements need to use brand colors:
  - Continue using semantic class names (`bg-brand`, `text-brand`, etc.) for maintainability
  - Add inline styles with the exact hex value as a fallback: `style="background-color: #2271b3;"`
  - The brand color is defined as `#2271b3` in the Tailwind config

- **Text Contrast and Visibility**: 
  - Use `text-gray-800` rather than `text-gray-500` for non-highlighted text to ensure adequate contrast and readability
  - For emphasized UI elements, use `text-brand` (with inline fallback if needed)
  - Apply the brand color consistently across related elements (e.g., table headers, tab controls, navigation)

- **Active/Selected UI States**:
  - For active tabs: Use `bg-brand text-white border-brand` to make the selected state visually distinct
  - Consider adding `style={isActive ? 'background-color: #2271b3; color: white; border-color: #2271b3;' : ''}` as a fallback

- **Hover States**:
  - For hover effects on brand color elements: Use `hover:bg-brand-hover` (the darker variant)
  - For hover on text that should emphasize: `hover:text-brand`

### 7.2. Responsive Design Patterns

- **Responsive Tables**:
  - Use `hidden md:table-cell` to hide less critical columns on smaller screens
  - Apply `whitespace-normal break-words` to allow text wrapping in cells with variable content
  - Use `overflow-x-auto` on table containers to handle horizontal scrolling on small screens

- **Flexible Layout Containers**:
  - Use `flex flex-col sm:flex-row` for containers that should stack vertically on mobile but display horizontally on larger screens
  - Apply `space-y-2 sm:space-y-0` to manage spacing in responsive layouts

These patterns ensure consistent visual design across the application and help prevent styling issues caused by build process variations or browser inconsistencies.
