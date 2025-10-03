# LAMB Frontend Migration Guidelines

## 1. Overview

This document outlines the strategy for migrating the LAMB frontend application from the legacy SvelteKit project (located in `_frontend/svelte-app`) to the new SvelteKit project (located in `frontend/svelte-app`). The primary motivation for this migration is to resolve persistent deployment issues encountered with the legacy application structure and to establish a cleaner, more maintainable foundation using updated dependencies and configurations.

## 2. Goals

-   Successfully replicate all features and functionalities of the legacy application within the new application structure.
-   Ensure the new application is correctly configured and buildable for deployment under the `/frontend` URL path.
-   Improve project maintainability and developer experience with the new setup.

## 3. Strategy: Module-by-Module Porting

The migration will follow a careful, incremental approach:

-   **Identify Modules/Features:** The legacy application will be broken down into logical modules or distinct features (e.g., Assistant List view, Assistant Creation form, Navigation, Authentication logic, specific UI components).
-   **Port One Module at a Time:** Each module or feature will be ported individually from the legacy codebase (`_frontend/svelte-app`) to the new codebase (`frontend/svelte-app`).
    -   This involves copying relevant Svelte components, JavaScript/TypeScript logic (services, stores, utils), and adapting them as necessary to fit the new structure and potentially newer Svelte 5/Tailwind v4 patterns.
    -   Code will be refactored during porting to adhere to the standards defined in `Documentation/frontend-guidelines.md`.
-   **Test Extensively:** After porting each module, it will be thoroughly tested within the new application's development environment (`npm run dev`). This includes:
    -   Unit tests (Vitest) for logic if applicable.
    -   Component interaction tests.
    -   End-to-end tests (Playwright) simulating user flows related to the migrated module.
    -   Manual verification of UI and functionality.
-   **Integrate and Verify:** Ensure the newly ported module integrates correctly with previously migrated parts and doesn't introduce regressions.

## 4. Key Considerations

-   **Deployment Path:** The new application is configured with `paths.base = '/frontend'` in `svelte.config.js`. All ported code, especially routing and asset links, must function correctly under this base path. 
-   **Build Output:** The static build output is configured in `frontend/svelte-app/svelte.config.js` using `adapter-static` with `pages: '../build'` and `assets: '../build'` to place the final files in the `/frontend/build/` directory, ready for deployment.
-   **Technology Differences:** Be mindful of potential differences between the legacy stack (likely Tailwind v3 with PostCSS config) and the new stack (Tailwind v4 with Vite plugin). CSS classes and configurations might need adjustments. Svelte 5 Runes might offer new ways to implement reactivity compared to the legacy app.
-   **Color Scheme:** The new application aims to match the legacy visual style. Action buttons use the following standard Tailwind colors corresponding to the legacy theme: Edit (indigo-600), Clone (gray-200), Delete (red-600), Download (blue-600), Unpublish (yellow-500), Publish (green-600).
-   **Runtime Configuration:** The new application relies on `static/config.js` loaded via `app.html`. Ensure any configuration access in ported code uses `window.LAMB_CONFIG` appropriately.
-   **Static Generation:** The new application uses `@sveltejs/adapter-static` configured with `fallback: 'index.html'` for SPA mode. Prerendering is not enabled globally, allowing for client-side rendering.

## 5. Process

1.  Choose the next module/feature from the legacy app to migrate.
2.  Copy relevant files (`*.svelte`, `*.js`, etc.) to the appropriate locations within `frontend/svelte-app/src/`.
3.  Refactor/update the code to align with Svelte 5, Tailwind v4, and the new project structure.
4.  Implement necessary tests (unit, component, e2e).
5.  Run `npm run dev` and manually test the migrated functionality.
6.  Run `npm run test` to execute automated tests.
7.  Run `npm run build` and potentially `npm run preview` to verify the build works and paths are correct.
8.  Commit the changes for the successfully migrated module.
9.  Repeat for the next module.

By following this structured approach, we aim for a smooth transition with minimal disruption and a well-tested, robust final application.

## 6. Migration Status

This section tracks the progress of migrating modules from the legacy application (`_frontend/svelte-app`) to the new application (`frontend/svelte-app`).

| Module                   | Status        | Notes                                                      |
| :----------------------- | :------------ | :------------------------------------------------------- |
| Core UI/Layout         | Done          | Basic structure, Nav, global styles migrated.            |
| Authentication           | Done          | Store, Service, Login/Signup components migrated. Review done. |
| Assistants List          | Done          | Store, Service, List component migrated (display only). Review done. |
| Assistant Creation       | In Progress   | Basic form ported (no KB/description gen). Needs review. |
| Internationalization     | Not Started   | Language selection, translation loading                 |
| Help System              | Not Started   | Help modal component                                   |
| **(Add other modules)**  | Not Started   |                                                          | 