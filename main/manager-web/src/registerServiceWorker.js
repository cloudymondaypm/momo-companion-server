/* eslint-disable no-console */

export const register = () => {
  if (process.env.NODE_ENV === 'production' && 'serviceWorker' in navigator) {
    window.addEventListener('load', () => {
      const swUrl = `${process.env.BASE_URL}service-worker.js`;
      
      console.info(`[Momo Companion] Attempting to register Service Worker, URL: ${swUrl}`);
      
      // Check whether Service Worker is already registered
      navigator.serviceWorker.getRegistrations().then(registrations => {
        if (registrations.length > 0) {
          console.info('[Momo Companion] Existing Service Worker found; checking for updates');
        }
        
        // Continue Service Worker registration
        navigator.serviceWorker
          .register(swUrl)
          .then(registration => {
            console.info('[Momo Companion] Service Worker registration succeeded');
            
            // Update handling
            registration.onupdatefound = () => {
              const installingWorker = registration.installing;
              if (installingWorker == null) {
                return;
              }
              installingWorker.onstatechange = () => {
                if (installingWorker.state === 'installed') {
                  if (navigator.serviceWorker.controller) {
                    // Updated content cached; prompt user to refresh
                    console.log('[Momo Companion] New content available. Refresh the page.');
                    // Show update notification here
                    const updateNotification = document.createElement('div');
                    updateNotification.style.cssText = `
                      position: fixed;
                      bottom: 20px;
                      right: 20px;
                      background: #409EFF;
                      color: white;
                      padding: 12px 20px;
                      border-radius: 4px;
                      box-shadow: 0 2px 12px 0 rgba(0,0,0,.1);
                      z-index: 9999;
                    `;
                    updateNotification.innerHTML = `
                      <div style="display: flex; align-items: center;">
                        <span style="margin-right: 10px;">New version available. Click to refresh.</span>
                        <button style="background: white; color: #409EFF; border: none; padding: 5px 10px; border-radius: 3px; cursor: pointer;">Refresh</button>
                      </div>
                    `;
                    document.body.appendChild(updateNotification);
                    updateNotification.querySelector('button').addEventListener('click', () => {
                      window.location.reload();
                    });
                  } else {
                    // Service Worker installed successfully
                    console.log('[Momo Companion] Content cached for offline use');
                    
                    // Initialize cache here
                    setTimeout(() => {
                      // Prewarm CDN cache
                      const cdnUrls = [
                        'https://unpkg.com/element-ui@2.15.14/lib/theme-chalk/index.css',
                        'https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css',
                        'https://unpkg.com/vue@2.6.14/dist/vue.min.js',
                        'https://unpkg.com/vue-router@3.6.5/dist/vue-router.min.js',
                        'https://unpkg.com/vuex@3.6.2/dist/vuex.min.js',
                        'https://unpkg.com/element-ui@2.15.14/lib/index.js',
                        'https://unpkg.com/axios@0.27.2/dist/axios.min.js',
                        'https://unpkg.com/opus-decoder@0.7.7/dist/opus-decoder.min.js'
                      ];
                      
                      // Prewarm cache
                      cdnUrls.forEach(url => {
                        fetch(url, { mode: 'no-cors' }).catch(err => {
                          console.log(`Prewarm cache ${url} failed`, err);
                        });
                      });
                    }, 2000);
                  }
                }
              };
            };
          })
          .catch(error => {
            console.error('Service Worker registration failed:', error);
            
            if (error.name === 'TypeError' && error.message.includes('Failed to register a ServiceWorker')) {
              console.warn('[Momo Companion] Network error during Service Worker registration; CDN assets may not be cached');
              if (process.env.NODE_ENV === 'production') {
                console.info(
                  'Possible reasons: 1. Incorrect MIME type; 2. Server SSL certificate issue; 3. Missing service-worker.js response'
                );
              }
            }
          });
      });
    });
  }
};

export const unregister = () => {
  if ('serviceWorker' in navigator) {
    navigator.serviceWorker.ready
      .then(registration => {
        registration.unregister();
      })
      .catch(error => {
        console.error(error.message);
      });
  }
}; 