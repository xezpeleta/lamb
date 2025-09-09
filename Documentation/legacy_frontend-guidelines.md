# LAMB Frontend Guidelines

## Table of Contents
- [Introduction](#introduction)
- [Technology Stack](#technology-stack)
- [Assistant Creation Guidelines](#assistant-creation-guidelines)
  - [APIs and Endpoints](#apis-and-endpoints)
  - [Data Structure](#data-structure)
  - [Additional Endpoints](#additional-endpoints)
  - [Configuration](#configuration)
- [Design Principles](#design-principles)
- [Best Practices](#best-practices)
- [Styling Guidelines](#styling-guidelines)
  - [Color Palette](#color-palette)
  - [Typography](#typography)
- [Component Structure](#component-structure)
- [Internationalization](#internationalization)
- [Best Practices](#best-practices-1)
  - [Performance](#performance)
  - [Accessibility](#accessibility)
  - [Code Quality](#code-quality)
  - [State Management](#state-management)
  - [Tailwind CSS Troubleshooting](#tailwind-css-troubleshooting)

## Introduction

This document provides comprehensive guidelines for the frontend development of the LAMB (Learning Assistants Manager and Builder) application. It serves as a reference for maintaining consistency in design, code structure, and user experience across the application.

## Technology Stack

LAMB's frontend is built with the following technologies:

- **Framework**: [Svelte](https://svelte.dev/) (v5.0.0) with [SvelteKit](https://kit.svelte.dev/) (v2.18.0)
- **CSS Framework**: [Tailwind CSS](https://tailwindcss.com/) (v3.3.3)
- **HTTP Client**: [Axios](https://axios-http.com/) (v1.8.1)
- **Internationalization**: [svelte-i18n](https://github.com/kaisermann/svelte-i18n) (v4.0.1)
- **Build Tool**: [Vite](https://vitejs.dev/) (v6.0.0)
- **Testing**: [Vitest](https://vitest.dev/) (v3.0.0) with [Testing Library](https://testing-library.com/)
- We are using CommonJS syntax With JSDoc for type validation 


## Assistant Creation Guidelines

### APIs and Endpoints
- **createAssistant API**: Used to create a new assistant with specified parameters.
  - **Endpoint**: `/creator/assistant/create_assistant`
  - **Method**: POST
  - **Headers**: Requires `Authorization` header with a Bearer token.

### Data Structure
- **Form Data Object**: Contains all necessary fields for assistant creation.
  - **name**: The name of the assistant.
  - **description**: A brief description of the assistant.
  - **system_prompt**: The initial prompt for the assistant.
  - **prompt_template**: Template for generating responses.
  - **rag_processor**: Specifies RAG processing method, e.g., `single_file_rag`.
  - **file_path**: Path to the file used for RAG.
  - **RAG_Top_k**: Number of top results to consider in RAG.
  - **api_callback**: JSON string containing configuration for prompt processor, connector, LLM, etc.


### Configuration
- **Server URLs**: Configuration for server URLs can be found in the `config.js` file located in the `src/config` directory.
- **Environment Variables**: Ensure environment variables are set for API keys and server endpoints.

## Design Principles

The LAMB application follows these core design principles:

1. **Simplicity**: Interfaces should be clean and intuitive, focusing on essential functionality without unnecessary complexity.
2. **Consistency**: UI elements, patterns, and interactions should be consistent throughout the application.
3. **Accessibility**: The application should be usable by people with diverse abilities and needs.
4. **Responsiveness**: The UI should adapt seamlessly to different screen sizes and devices.
5. **Feedback**: Users should receive clear feedback for their actions through visual cues and notifications.

## Best Practices

- Ensure `rag_processor` and `file_path` are correctly set based on user input.
- `api_callback` should be a JSON string with relevant configuration details.
- Validate form data before submission to ensure all required fields are populated.

## Styling Guidelines

### Color Palette

The LAMB application uses a consistent color palette based on the original CSS from the backend, with Tailwind CSS utility classes for implementation:

#### Primary Colors
- **Primary Blue** (`#2271b3` / `--primary-color`): Used for primary actions, active states, and important UI elements
- **Primary Blue Hover** (`#195a91` / `--primary-hover`): Darker version of the primary blue for hover states
- **Dark Gray** (`#1f2937`): Used for top navigation bar background and headings
- **Light Gray** (`#f4f6f8`): Used for page backgrounds

#### Secondary Colors
- **Secondary Gray** (`#e9ecef` / `--secondary-color`): Used for secondary UI elements and hover states
- **Text Color** (`#333` / `--text-color`): Primary text color
- **Light Text** (`#6c757d` / `--text-light`): Secondary text color for less important information
- **Border Color** (`#dee2e6` / `--border-color`): Used for borders and dividers
- **Background Color** (`#f8f9fa` / `--bg-color`): Used for component backgrounds

#### Semantic Colors
- **Success**: Background `#d4edda` with text `#155724` for success states
- **Warning**: Background `#fff3cd` with text `#856404` for warning states
- **Danger/Error**: Background `#f8d7da` with text `#721c24` for error states
- **Info**: Background `#d1ecf1` with text `#0c5460` for informational states

#### Button Colors
- **Primary Button**: `#2271b3` (Primary Blue) with hover state `#195a91`
- **Destructive Button**: `#dc3545` (Red) with hover state `#c82333`

#### Usage Guidelines
- Use the primary blue color for main actions, navigation highlights, and interactive elements
- Use red sparingly and primarily for destructive actions like delete buttons
- Use gray scales for most UI elements, backgrounds, and text
- Maintain sufficient contrast between text and background colors for readability
- Follow the semantic color system for feedback and status indicators

### Typography

The application uses Roboto as its primary font, imported from Google Fonts:

#### Font Family
- **Primary Font**: 'Roboto', sans-serif
- **Monospace**: 'Courier New', monospace (for code blocks and technical content)

#### Font Sizes
- **Extra Small** (`text-xs`): 0.75rem - Used for metadata, badges, and helper text
- **Small** (`text-sm`): 0.875rem - Used for secondary text and compact UI elements
- **Base** (`text-base`): 1rem - Default text size for body content
- **Large** (`text-lg`): 1.125rem - Used for section headings and emphasized content
- **Extra Large** (`text-xl` and above): 1.25rem+ - Used for major headings and titles

#### Font Weights
- **Normal** (`font-normal`): 400 - Default text weight
- **Medium** (`font-medium`): 500 - Used for semi-emphasized text

## Component Structure

The LAMB frontend follows a modular component structure:

### Directory Structure
```
src/
├── app.css                  # Global CSS imports
├── app.html                 # HTML template
├── routes/                  # SvelteKit routes
└── lib/
    ├── components/          # Reusable UI components
    ├── services/            # API and business logic services
    ├── stores/              # Svelte stores for state management
    ├── utils/               # Utility functions
    └── i18n/                # Internationalization resources
```

### Component Patterns

1. **Page Components**: Located in the `routes` directory, these components represent full pages in the application.

2. **UI Components**: Located in `lib/components`, these are reusable interface elements used across multiple pages:
   - `AssistantsList.svelte`: Displays a table of assistants with details and actions
   - `Nav.svelte`: Navigation bar component
   - `LanguageSelector.svelte`: Language selection dropdown
   - `HelpModal.svelte`: Help system modal

3. **Service Modules**: Located in `lib/services`, these handle API communication and data processing:
   - `assistantService.js`: Handles assistant-related API calls
   - `authService.js`: Manages authentication

4. **Store Modules**: Located in `lib/stores`, these manage application state:
   - `userStore.js`: Manages user authentication state

## Internationalization

The LAMB application uses `svelte-i18n` for internationalization:

### Implementation
- Translation files are stored in JSON format
- The `$_()` function is used to retrieve translated strings
- The `locale` store manages the current language
- A `LanguageSelector` component allows users to change the language

### Best Practices
- Use translation keys that reflect the content's purpose
- Group related translations under namespaces (e.g., `assistants.title`)
- Provide fallback text for when translations aren't loaded yet
- Use the `localeLoaded` state to handle loading states

## Best Practices

### Performance
- Minimize bundle size by importing only what's needed
- Use Svelte's reactive declarations for derived values
- Implement pagination for large data sets
- Optimize images and assets

### Accessibility
- Use semantic HTML elements
- Provide alternative text for images
- Ensure sufficient color contrast
- Support keyboard navigation
- Test with screen readers

### Code Quality
- Follow consistent naming conventions
- Document complex components and functions
- Use TypeScript or JSDoc for type safety
- Write unit tests for critical functionality
- Use ESLint and Prettier for code formatting

### State Management
- Use Svelte stores for application-wide state
- Keep component state local when possible
- Use reactive declarations for derived state
- Handle loading, success, and error states consistently

### Tailwind CSS Troubleshooting

- **Configuration File Format**: Always use CommonJS format (`.cjs` extension) for Tailwind and PostCSS config files when working with ES modules in the project
- **Version Compatibility**: Maintain compatibility between Tailwind CSS and its plugins:
  - Tailwind CSS v3.3.x works best with:
    - `@tailwindcss/forms` v0.5.x
    - `@tailwindcss/typography` v0.5.x
    - `autoprefixer` v10.4.x
    - `postcss` v8.4.x
- **PostCSS Configuration**: Keep the PostCSS configuration simple with just `tailwindcss` and `autoprefixer` plugins
- **Common Issues**:
  - If you encounter errors about using `tailwindcss` directly as a PostCSS plugin, ensure you're using the correct version of Tailwind CSS (v3.x) and not v4.x
  - For module format errors, ensure config files use the `.cjs` extension
  - When updating dependencies, perform a clean install by removing `node_modules` and `package-lock.json` if you encounter persistent issues

---

This document is a living guide and should be updated as the LAMB application evolves. All developers working on the LAMB frontend should follow these guidelines to maintain consistency and quality across the application.
