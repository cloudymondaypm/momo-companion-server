import { getServiceUrl } from '../api';
import RequestService from '../httpRequest';

export default {
    // List voice resources with pagination
    getVoiceResourceList(params, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource`)
            .method('GET')
            .data(params)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get voice resource list failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getVoiceResourceList(params, callback);
                });
            }).send();
    },
    // Get one voice resource
    getVoiceResourceInfo(id, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/${id}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get voice resource information failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getVoiceResourceInfo(id, callback);
                });
            }).send();
    },
    // Save voice resource
    saveVoiceResource(entity, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource`)
            .method('POST')
            .data(entity)
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Save voice resource failed:', err);
                RequestService.reAjaxFun(() => {
                    this.saveVoiceResource(entity, callback);
                });
            }).send();
    },
    // Delete voice resource
    deleteVoiceResource(ids, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/${ids}`)
            .method('DELETE')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Delete voice resource failed:', err);
                RequestService.reAjaxFun(() => {
                    this.deleteVoiceResource(ids, callback);
                });
            }).send();
    },
    // Get voice resources by user ID
    getVoiceResourceByUserId(userId, callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/user/${userId}`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get user voice resource list failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getVoiceResourceByUserId(userId, callback);
                });
            }).send();
    },
    // Get TTS platform list
    getTtsPlatformList(callback) {
        RequestService.sendRequest()
            .url(`${getServiceUrl()}/voiceResource/ttsPlatforms`)
            .method('GET')
            .success((res) => {
                RequestService.clearRequestTime();
                callback(res);
            })
            .networkFail((err) => {
                console.error('Get TTS platform list failed:', err);
                RequestService.reAjaxFun(() => {
                    this.getTtsPlatformList(callback);
                });
            }).send();
    }
}
