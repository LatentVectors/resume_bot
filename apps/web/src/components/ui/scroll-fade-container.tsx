"use client";

import { forwardRef, useCallback, useEffect, useRef, useState } from "react";
import { cn } from "@/lib/utils";

interface ScrollFadeContainerProps {
  children: React.ReactNode;
  /** Height of the top gradient in pixels (default: 40px) */
  topGradientHeight?: number;
  /** Height of the bottom gradient in pixels (default: 80px) */
  bottomGradientHeight?: number;
  /** Distance from edge in pixels at which gradient reaches full opacity (default: 100px for gradual fade) */
  fadeThreshold?: number;
  /** Additional class names for the container */
  className?: string;
  /** Additional class names for the scrollable content area */
  scrollClassName?: string;
}

/**
 * A scrollable container that displays gradient fade indicators at the top
 * and bottom when there is more content above or below the visible area.
 * The gradients use an ease-out curve to stay visible longer and fade out
 * more quickly as you approach the edges, creating a "sense of arrival".
 *
 * Features:
 * - Minimal scrollbar styling (thin, only visible on hover)
 * - Top/bottom gradient fade indicators with ease-out opacity curve
 * - Configurable gradient heights and fade thresholds
 */
export const ScrollFadeContainer = forwardRef<
  HTMLDivElement,
  ScrollFadeContainerProps
>(
  (
    {
      children,
      topGradientHeight = 40,
      bottomGradientHeight = 80,
      fadeThreshold = 100,
      className,
      scrollClassName,
    },
    ref
  ) => {
    const scrollRef = useRef<HTMLDivElement>(null);
    const [topOpacity, setTopOpacity] = useState(0);
    const [bottomOpacity, setBottomOpacity] = useState(0);

    const updateGradientOpacity = useCallback(() => {
      const container = scrollRef.current;
      if (!container) return;

      const { scrollTop, scrollHeight, clientHeight } = container;
      const maxScroll = scrollHeight - clientHeight;

      // Ease-out function: keeps gradient visible longer, fades quickly near edge
      // Creates a "sense of arrival" as you approach the top/bottom
      const easeOut = (t: number) => 1 - Math.pow(1 - t, 2.5);

      // Calculate top gradient opacity based on distance from top
      if (scrollTop <= 0) {
        setTopOpacity(0);
      } else if (scrollTop >= fadeThreshold) {
        setTopOpacity(1);
      } else {
        const t = scrollTop / fadeThreshold;
        setTopOpacity(easeOut(t));
      }

      // Calculate bottom gradient opacity based on distance from bottom
      const distanceFromBottom = maxScroll - scrollTop;
      if (distanceFromBottom <= 0) {
        setBottomOpacity(0);
      } else if (distanceFromBottom >= fadeThreshold) {
        setBottomOpacity(1);
      } else {
        const t = distanceFromBottom / fadeThreshold;
        setBottomOpacity(easeOut(t));
      }
    }, [fadeThreshold]);

    // Update on scroll
    const handleScroll = useCallback(() => {
      updateGradientOpacity();
    }, [updateGradientOpacity]);

    // Initial calculation and recalculate on resize/content changes
    useEffect(() => {
      updateGradientOpacity();

      const container = scrollRef.current;
      if (!container) return;

      // Use ResizeObserver to detect content size changes
      const resizeObserver = new ResizeObserver(() => {
        updateGradientOpacity();
      });

      resizeObserver.observe(container);

      // Also observe children for size changes
      const children = container.children;
      for (let i = 0; i < children.length; i++) {
        resizeObserver.observe(children[i]);
      }

      return () => {
        resizeObserver.disconnect();
      };
    }, [updateGradientOpacity]);

    // Recalculate when children change
    useEffect(() => {
      // Small delay to allow DOM to update
      const timeoutId = setTimeout(updateGradientOpacity, 10);
      return () => clearTimeout(timeoutId);
    }, [children, updateGradientOpacity]);

    return (
      <div ref={ref} className={cn("relative h-full min-h-0", className)}>
        {/* Scrollable content */}
        <div
          ref={scrollRef}
          onScroll={handleScroll}
          className={cn(
            "h-full min-h-0 overflow-y-auto scrollbar-minimal",
            scrollClassName
          )}
        >
          {children}
        </div>

        {/* Top gradient overlay */}
        <div
          className="pointer-events-none absolute left-0 right-0 top-0 z-10"
          style={{
            height: topGradientHeight,
            background:
              "linear-gradient(to bottom, var(--background), transparent)",
            opacity: topOpacity,
            transition: "opacity 150ms ease-out",
          }}
          aria-hidden="true"
        />

        {/* Bottom gradient overlay */}
        <div
          className="pointer-events-none absolute bottom-0 left-0 right-0 z-10"
          style={{
            height: bottomGradientHeight,
            background:
              "linear-gradient(to top, var(--background), transparent)",
            opacity: bottomOpacity,
            transition: "opacity 150ms ease-out",
          }}
          aria-hidden="true"
        />
      </div>
    );
  }
);

ScrollFadeContainer.displayName = "ScrollFadeContainer";

