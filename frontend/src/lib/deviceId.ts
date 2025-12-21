/**
 * Device ID utility for multi-user claim system
 * Generates and persists a unique device ID in localStorage
 */

const DEVICE_ID_KEY = "lead_swiper_device_id";

/**
 * Get or create a persistent device ID
 * This ID is used to claim leads for swiping
 */
export function getDeviceId(): string {
  // Check if we're on the client side
  if (typeof window === "undefined") {
    return "server";
  }

  let deviceId = localStorage.getItem(DEVICE_ID_KEY);
  
  if (!deviceId) {
    deviceId = crypto.randomUUID();
    localStorage.setItem(DEVICE_ID_KEY, deviceId);
  }
  
  return deviceId;
}

/**
 * Clear the device ID (useful for testing)
 */
export function clearDeviceId(): void {
  if (typeof window !== "undefined") {
    localStorage.removeItem(DEVICE_ID_KEY);
  }
}

