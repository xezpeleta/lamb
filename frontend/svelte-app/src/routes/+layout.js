import { browser } from '$app/environment';
// Import the setup functions from our i18n module
import { setupI18n, setLocale, supportedLocales, fallbackLocale } from '$lib/i18n';

// We want this to run only once on the client
let initialized = false;

/** @type {import('./$types').LayoutLoad} */
export const load = async () => {
  
  if (browser && !initialized) {
    console.log('Running i18n setup in +layout.js load...');
    // 1. Initialize svelte-i18n (registers locales, sets fallback)
    setupI18n(); 
    
    let storedLocale = localStorage.getItem('lang');
    let localeToSet = fallbackLocale; // Default to fallback
    
    if (storedLocale && supportedLocales.includes(storedLocale)) {
      localeToSet = storedLocale; // Use stored locale if valid
    }
    
    // localeToSet is now guaranteed to be a valid, non-null string
    setLocale(localeToSet); 

    initialized = true;
  }
  
  // The load function needs to return an object, even if empty
  return {};
};

// Remove ssr = false; it's handled by adapter-static fallback
// export const ssr = false; 