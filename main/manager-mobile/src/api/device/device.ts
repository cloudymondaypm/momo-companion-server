import type { Device, FirmwareType } from './types'
import { http } from '@/http/request/alova'

/**
 * Get device type list
 */
export function getFirmwareTypes() {
  return http.Get<FirmwareType[]>('/admin/dict/data/type/FIRMWARE_TYPE')
}

/**
 * Get bound device list
 * @param agentId Agent ID
 */
export function getBindDevices(agentId: string) {
  return http.Get<Device[]>(`/device/bind/${agentId}`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

/**
 * Add device
 * @param agentId Agent ID
 * @param code Verification code
 */
export function bindDevice(agentId: string, code: string) {
  return http.Post(`/device/bind/${agentId}/${code}`, null)
}

/**
 * Add device manually
 * @param agentId Agent ID
 * @param board Device type
 * @param appVersion Firmware version
 * @param macAddress MAC address
 */
export function bindDeviceManual(data: {
  agentId: string
  board: string
  appVersion: string
  macAddress: string
}) {
  return http.Post('/device/manual-add', data)
}

/**
 * Set device OTA update toggle
 * @param deviceId Device ID (MAC address)
 * @param autoUpdate Auto-update setting 0|1
 */
export function updateDeviceAutoUpdate(deviceId: string, autoUpdate: number) {
  return http.Put(`/device/update/${deviceId}`, {
    autoUpdate,
  })
}

/**
 * Unbind device
 * @param deviceId Device ID (MAC address)
 */
export function unbindDevice(deviceId: string) {
  return http.Post('/device/unbind', {
    deviceId,
  })
}
