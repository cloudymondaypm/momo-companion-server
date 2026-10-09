//Feature configuration utility
import Api from "@/apis/api";
import store from "@/store";

class FeatureManager {
    constructor() {
        this.defaultFeatures = {
            voiceprintRecognition: {
                name: 'feature.voiceprintRecognition.name',
                enabled: false,
                description: 'feature.voiceprintRecognition.description'
            },
            voiceClone: {
                name: 'feature.voiceClone.name',
                enabled: false,
                description: 'feature.voiceClone.description'
            },
            knowledgeBase: {
                name: 'feature.knowledgeBase.name',
                enabled: false,
                description: 'feature.knowledgeBase.description'
            },
            mcpAccessPoint: {
                name: 'feature.mcpAccessPoint.name',
                enabled: false,
                description: 'feature.mcpAccessPoint.description'
            },
            vad: {
                name: 'feature.vad.name',
                enabled: false,
                description: 'feature.vad.description'
            },
            asr: {
                name: 'feature.asr.name',
                enabled: false,
                description: 'feature.asr.description'
            },
            addressBook: {
                name: 'feature.addressBook.name',
                enabled: false,
                description: 'feature.addressBook.description'
            }
        };
        this.currentFeatures = { ...this.defaultFeatures }; // Current in-memory configuration
        this.initialized = false;
        this.initPromise = null;
    }

    /**
     * Wait for initialization
     */
    async waitForInitialization() {
        if (!this.initPromise) {
            this.initPromise = this.init();
        }
        await this.initPromise;
        return this.initialized;
    }

    /**
     * Initialize feature configuration
     */
    async init() {
        try {
            // Get configuration from pub-config API
            const config = await this.getConfigFromPubConfig();
            if (config) {
                this.currentFeatures = { ...config }; // Save in memory
                this.initialized = true;
                return;
            }
        } catch (error) {
            console.warn('Failed to load configuration from pub-config:', error);
        }

        // Use defaults if pub-config API fails
        this.currentFeatures = { ...this.defaultFeatures }; // Save defaults in memory
        this.initialized = true;
    }

    /**
     * Update config cache
     */
    updateConfigCache(config) {
        store.commit('setPubConfig', config);
        localStorage.setItem('pubConfig', JSON.stringify(config));
    }

    /**
     * Get configuration from pub-config API
     */
    async getConfigFromPubConfig() {
        return new Promise((resolve) => {
            // Call pub-config API directly
            Api.user.getPubConfig((result) => {
                // Check response structure
                if (result && result.status === 200) {
                    // Check for a data field
                    if (result.data) {
                        const configCache = result.data.data || {};
                        // If code field exists, validate its value
                        if (result.data.code !== undefined) {
                            if (result.data.code === 0 && result.data.data && result.data.data.systemWebMenu) {
                                try {
                                    let config;
                                    if (typeof result.data.data.systemWebMenu === 'string') {
                                        // Parse JSON if value is a string
                                        config = JSON.parse(result.data.data.systemWebMenu);
                                    } else {
                                        // Use object values directly
                                        config = result.data.data.systemWebMenu;
                                    }

                                    // Check if config contains features object
                                    if (config && config.features) {
                                        // Ensure knowledgeBase feature exists and is valid
                                        if (!config.features.knowledgeBase) {
                                            console.warn('knowledgeBase is missing; merging defaults');
                                            config.features = { ...this.defaultFeatures, ...config.features };
                                        }
                                        resolve(config.features);
                                    } else {
                                        console.warn('features object is missing; using defaults');
                                        resolve(this.defaultFeatures);
                                    }
                                    configCache.systemWebMenu = config;
                                } catch (error) {
                                    console.warn('Failed to process systemWebMenu configuration:', error);
                                    resolve(null);
                                }
                            } else {
                                console.warn('API returned a nonzero code or missing data; using defaults');
                                resolve(null);
                            }
                        } else {
                            // If no code field exists, check systemWebMenu directly
                            if (result.data && result.data.systemWebMenu) {
                                try {
                                    let config;
                                    if (typeof result.data.systemWebMenu === 'string') {
                                        // Parse JSON if value is a string
                                        config = JSON.parse(result.data.systemWebMenu);
                                    } else {
                                        // Use object values directly
                                        config = result.data.systemWebMenu;
                                    }

                                    // Check if config contains features object
                                    if (config && config.features) {
                                        // Ensure knowledgeBase feature exists and is valid
                                        if (!config.features.knowledgeBase) {
                                            console.warn('knowledgeBase is missing; merging defaults');
                                            config.features = { ...this.defaultFeatures, ...config.features };
                                        }
                                        resolve(config.features);
                                    } else {
                                        console.warn('features object is missing; using defaults');
                                        resolve(this.defaultFeatures);
                                    }
                                    configCache.systemWebMenu = config;
                                } catch (error) {
                                    console.warn('Failed to process systemWebMenu configuration:', error);
                                    resolve(null);
                                }
                            } else {
                                console.warn('API response missing systemWebMenu; using defaults');
                                resolve(null);
                            }
                        }
                        this.updateConfigCache(configCache)
                    } else {
                        console.warn('API response missing data field; using defaults');
                        resolve(null);
                    }
                } else {
                    console.warn('pub-config request failed; using defaults');
                    resolve(null);
                }
            });
        });
    }

    /**
     * Get current configuration
     */
    getCurrentConfig() {
        // Return current in-memory configuration
        return this.currentFeatures;
    }

    /**
     * Save configuration to backend API
     */
    async saveConfig(config) {
        try {
            // Update in-memory configuration
            this.currentFeatures = { ...config };

            // Save to backend API asynchronously
            this.saveConfigToAPI(config).catch(error => {
                console.warn('Failed to save config to API:', error);
            }).finally(() => {
                this.init()
            });

            // Emit configuration-changed event
            window.dispatchEvent(new CustomEvent('featureConfigChanged', {
                detail: config
            }));
        } catch (error) {
            console.error('Failed to save feature configuration:', error);
        }
    }

    /**
     * Save configuration to backend API
     */
    async saveConfigToAPI(config) {
        return new Promise((resolve) => {
            // Update parameter using known ID (600)
            Api.admin.updateParam(
                {
                    id: 600,
                    paramCode: 'system-web.menu',
                    paramValue: JSON.stringify({
                        features: config,
                        groups: {
                            featureManagement: ["voiceprintRecognition", "voiceClone", "knowledgeBase", "mcpAccessPoint", "addressBook"],
                            voiceManagement: ["vad", "asr"]
                        }
                    }),
                    valueType: 'json',
                    remark: 'System feature menu configuration'
                },
                (updateResult) => {
                    if (updateResult.code === 0) {
                        resolve();
                    } else {
                        // If update fails, log but do not block localStorage persistence
                        console.warn('Failed to update parameter:', updateResult.msg);
                        resolve(); // Do not block localStorage persistence
                    }
                },
                (error) => {
                    console.warn('Failed to update parameter:', error);
                    resolve(); // Do not block localStorage persistence
                }
            );
        });
    }



    /**
     * Get all feature configurations
     */
    getAllFeatures() {
        return this.getCurrentConfig();
    }

    /**
     * Get simplified configuration for home component
     */
    getConfig() {
        const features = this.getAllFeatures();
        return {
            voiceprintRecognition: features.voiceprintRecognition?.enabled || false,
            voiceClone: features.voiceClone?.enabled || false,
            knowledgeBase: features.knowledgeBase?.enabled || false,
            mcpAccessPoint: features.mcpAccessPoint?.enabled || false,
            vad: features.vad?.enabled || false,
            asr: features.asr?.enabled || false,
            addressBook: features.addressBook?.enabled || false
        };
    }

    /**
     * Get status of a particular feature
     */
    getFeatureStatus(featureKey) {
        const features = this.getAllFeatures();
        return features[featureKey]?.enabled || false;
    }

    /**
     * Set feature state
     */
    setFeatureStatus(featureKey, enabled) {
        const features = this.getAllFeatures();
        if (features[featureKey]) {
            features[featureKey].enabled = enabled;
            this.saveConfig(features);
            return true;
        }
        return false;
    }

    /**
     * Enable feature
     */
    enableFeature(featureKey) {
        return this.setFeatureStatus(featureKey, true);
    }

    /**
     * Disable feature
     */
    disableFeature(featureKey) {
        return this.setFeatureStatus(featureKey, false);
    }

    /**
     * Toggle feature state
     */
    toggleFeature(featureKey) {
        const currentStatus = this.getFeatureStatus(featureKey);
        return this.setFeatureStatus(featureKey, !currentStatus);
    }

    /**
     * Reset all features to default state
     */
    resetToDefault() {
        this.saveConfig(this.defaultFeatures);
    }

    /**
     * Bulk update feature state
     */
    updateFeatures(featureUpdates) {
        const features = this.getAllFeatures();
        Object.keys(featureUpdates).forEach(featureKey => {
            if (features[featureKey]) {
                features[featureKey].enabled = featureUpdates[featureKey];
            } else if (this.defaultFeatures[featureKey]) {
                features[featureKey] = { ...this.defaultFeatures[featureKey] };
                features[featureKey].enabled = featureUpdates[featureKey];
            }
        });
        this.saveConfig(features);
    }

    /**
     * Get list of enabled features
     */
    getEnabledFeatures() {
        const features = this.getAllFeatures();
        return Object.keys(features).filter(key => features[key].enabled);
    }

    /**
     * Check if a feature is enabled
     */
    isFeatureEnabled(featureKey) {
        return this.getFeatureStatus(featureKey);
    }
}

// Create singleton instance
const featureManager = new FeatureManager();

export default featureManager;