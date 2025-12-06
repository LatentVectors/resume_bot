/**
 * Centralized UI configuration constants
 * This file contains all shared UI behavior settings to ensure consistency across the application
 */

/**
 * Tooltip configuration
 * Defines consistent behavior for all tooltips across the application
 */
export const TOOLTIP_CONFIG = {
  /**
   * Delay before tooltip appears on hover (in milliseconds)
   * Set to 700ms to reduce visual clutter as users move their mouse
   */
  delayDuration: 700,
  /**
   * Duration to skip the delay when moving between tooltips (in milliseconds)
   * Default is 300ms - users won't see delay when quickly moving between tooltips
   */
  skipDelayDuration: 300,
} as const;

