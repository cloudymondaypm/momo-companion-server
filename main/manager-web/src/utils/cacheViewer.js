/**
 * Cache inspector for checking whether CDN assets are cached by the Service Worker
 */

/**
 * Get names of all Service Worker caches
 * @returns {Promise<string[]>} List of cache names
 */
export const getCacheNames = async () => {
  if (!('caches' in window)) {
    return [];
  }
  
  try {
    return await caches.keys();
  } catch (error) {
    console.error('Failed to get cache names:', error);
    return [];
  }
};

/**
 * Get all URLs in the specified cache
 * @param {string} cacheName Cache name
 * @returns {Promise<string[]>} List of cached URLs
 */
export const getCacheUrls = async (cacheName) => {
  if (!('caches' in window)) {
    return [];
  }
  
  try {
    const cache = await caches.open(cacheName);
    const requests = await cache.keys();
    return requests.map(request => request.url);
  } catch (error) {
    console.error(`Failed to get URLs from cache ${cacheName}:`, error);
    return [];
  }
};

/**
 * Check whether a specific URL is cached
 * @param {string} url URL to check
 * @returns {Promise<boolean>} Whether it is cached
 */
export const isUrlCached = async (url) => {
  if (!('caches' in window)) {
    return false;
  }
  
  try {
    const cacheNames = await getCacheNames();
    for (const cacheName of cacheNames) {
      const cache = await caches.open(cacheName);
      const match = await cache.match(url);
      if (match) {
        return true;
      }
    }
    return false;
  } catch (error) {
    console.error(`Failed to check cache for URL ${url}:`, error);
    return false;
  }
};

/**
 * Get CDN asset cache status for the current page
 * @returns {Promise<Object>} Cache status object
 */
export const checkCdnCacheStatus = async () => {
  // Find assets in CDN caches
  const cdnCaches = ['cdn-stylesheets', 'cdn-scripts'];
  const results = {
    css: [],
    js: [],
    totalCached: 0,
    totalNotCached: 0
  };
  
  for (const cacheName of cdnCaches) {
    try {
      const urls = await getCacheUrls(cacheName);
      
      // Distinguish CSS and JS assets
      for (const url of urls) {
        if (url.endsWith('.css')) {
          results.css.push({ url, cached: true });
        } else if (url.endsWith('.js')) {
          results.js.push({ url, cached: true });
        }
        results.totalCached++;
      }
    } catch (error) {
      console.error(`Failed to get cache details for ${cacheName}:`, error);
    }
  }
  
  return results;
};

/**
 * Clear all Service Worker caches
 * @returns {Promise<boolean>} Whether clearing succeeded
 */
export const clearAllCaches = async () => {
  if (!('caches' in window)) {
    return false;
  }
  
  try {
    const cacheNames = await getCacheNames();
    for (const cacheName of cacheNames) {
      await caches.delete(cacheName);
    }
    return true;
  } catch (error) {
    console.error('Failed to clear caches:', error);
    return false;
  }
};

/**
 * Print cache status to console
 */
export const logCacheStatus = async () => {
  console.group('Service Worker cache status');
  
  const cacheNames = await getCacheNames();
  console.log('Caches found:', cacheNames);
  
  for (const cacheName of cacheNames) {
    const urls = await getCacheUrls(cacheName);
    console.group(`Cache: ${cacheName} (${urls.length} entries)`);
    urls.forEach(url => console.log(url));
    console.groupEnd();
  }
  
  console.groupEnd();
  return cacheNames.length > 0;
}; 