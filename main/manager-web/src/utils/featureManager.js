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
            // Retrieve configuration from pub-config API
            const config = await this.getConfigFromPubConfig();
            if (config) {
                this.currentFeatures = { ...config }; // Store in memory
                this.initialized = true;
                return;
            }
        } catch (error) {
            console.warn('Failed to retrieve configuration from pub-config API:', error);
        }

        // Use defaults when pub-config API fails
        this.currentFeatures = { ...this.defaultFeatures }; // Store default configuration in memory
        this.initialized = true;
    }

    /**
     * Update configuration cache
     */
    updateConfigCache(config) {
        store.commit('setPubConfig', config);
        localStorage.setItem('pubConfig', JSON.stringify(config));
    }

    /**
     * Retrieve configuration from pub-config API
     */
    async getConfigFromPubConfig() {
        return new Promise((resolve) => {
            // Request configuration directly from pub-config API
            Api.user.getPubConfig((result) => {
                // Check response structure
                if (result && result.status === 200) {
                    // Check for data field
                    if (result.data) {
                        const configCache = result.data.data || {};
                        // Check for code field and use it to evaluate response
                        if (result.data.code !== undefined) {
                            if (result.data.code === 0 && result.data.data && result.data.data.systemWebMenu) {
                                try {
                                    let config;
                                    if (typeof result.data.data.systemWebMenu === 'string') {
                                        // Parse JSON if response is a string
                                        config = JSON.parse(result.data.data.systemWebMenu);
                                    } else {
                                        // Use directly if already an object
                                        config = result.data.data.systemWebMenu;
                                    }

                                    // Check configuration for a features object
                                    if (config && config.features) {
                                        // Ensure knowledgeBase feature exists and is valid
                                        if (!config.features.knowledgeBase) {
                                            console.warn('knowledgeBase is missing; merge defaults');
                                            config.features = { ...this.defaultFeatures, ...config.features };
                                        }
                                        resolve(config.features);
                                    } else {
                                        console.warn('features object is missing; use defaults');
                                        resolve(this.defaultFeatures);
                                    }
                                    configCache.systemWebMenu = config;
                                } catch (error) {
                                    console.warn('Failed to process systemWebMenu configuration:', error);
                                    resolve(null);
                                }
                            } else {
                                console.warn('API code is nonzero or required data is missing; use defaults');
                                resolve(null);
                            }
                        } else {
                            // If no code field, inspect systemWebMenu directly
                            if (result.data && result.data.systemWebMenu) {
                                try {
                                    let config;
                                    if (typeof result.data.systemWebMenu === 'string') {
                                        // Parse JSON if response is a string
                                        config = JSON.parse(result.data.systemWebMenu);
                                    } else {
                                        // Use directly if already an object
                                        config = result.data.systemWebMenu;
                                    }

                                    // Check configuration for a features object
                                    if (config && config.features) {
                                        // Ensure knowledgeBase feature exists and is valid
                                        if (!config.features.knowledgeBase) {
                                            console.warn('knowledgeBase is missing; merge defaults');
                                            config.features = { ...this.defaultFeatures, ...config.features };
                                        }
                                        resolve(config.features);
                                    } else {
                                        console.warn('features object is missing; use defaults');
                                        resolve(this.defaultFeatures);
                                    }
                                    configCache.systemWebMenu = config;
                                } catch (error) {
                                    console.warn('Failed to process systemWebMenu configuration:', error);
                                    resolve(null);
                                }
                            } else {
                                console.warn('API response lacks systemWebMenu; use defaults');
                                resolve(null);
                            }
                        }
                        this.updateConfigCache(configCache)
                    } else {
                        console.warn('API response lacks data field; use defaults');
                        resolve(null);
                    }
                } else {
                    console.warn('pub-config request failed; use defaults');
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

            // Save asynchronously to backend API
            this.saveConfigToAPI(config).catch(error => {
                console.warn('Failed to save configuration via API:', error);
            }).finally(() => {
                this.init()
            });

            // Emit configuration change event
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
                        // Log update failure, possibly missing parameter; do not block localStorage save
                        console.warn('Failed to update parameter:', updateResult.msg);
                        resolve(); // Do not block saving to localStorage
                    }
                },
                (error) => {
                    console.warn('Failed to update parameter:', error);
                    resolve(); // Do not block saving to localStorage
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
     * Get state of selected feature
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
     * Reset all features to defaults
     */
    resetToDefault() {
        this.saveConfig(this.defaultFeatures);
    }

    /**
     * Bulk update feature states
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
     * Get enabled features
     */
    getEnabledFeatures() {
        const features = this.getAllFeatures();
        return Object.keys(features).filter(key => features[key].enabled);
    }

    /**
     * Check if feature is enabled
     */
    isFeatureEnabled(featureKey) {
        return this.getFeatureStatus(featureKey);
    }
}

// Create singleton instance
const featureManager = new FeatureManager();

export default featureManager;