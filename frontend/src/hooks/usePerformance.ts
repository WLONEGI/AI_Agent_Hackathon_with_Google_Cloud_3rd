'use client';

import { useEffect, useCallback } from 'react';

interface WebVitalsMetric {
  name: string;
  value: number;
  delta: number;
  id: string;
  navigationType: string;
}

// Performance monitoring hook for Core Web Vitals
export const usePerformance = () => {
  const reportMetric = useCallback((metric: WebVitalsMetric) => {
    // Log to console in development
    if (process.env.NODE_ENV === 'development') {
      console.log('Web Vitals:', metric);
    }
    
    // Could be extended to send to analytics service
    // analytics.track('web_vitals', metric);
  }, []);

  useEffect(() => {
    // Dynamic import for web-vitals library when available
    if (typeof window !== 'undefined') {
      import('web-vitals').then(({ onCLS, onINP, onFCP, onLCP, onTTFB }) => {
        onCLS(reportMetric);
        onINP(reportMetric);
        onFCP(reportMetric);
        onLCP(reportMetric);
        onTTFB(reportMetric);
      }).catch(() => {
        // Graceful fallback if web-vitals is not available
        console.log('Web Vitals library not available');
      });
    }
  }, [reportMetric]);

  // Performance optimization utilities
  const optimizeImages = useCallback(() => {
    if (typeof window !== 'undefined') {
      // Preload critical images
      const criticalImages = document.querySelectorAll('img[loading="eager"]');
      criticalImages.forEach((img) => {
        if (img instanceof HTMLImageElement && !img.complete) {
          const link = document.createElement('link');
          link.rel = 'preload';
          link.as = 'image';
          link.href = img.src;
          document.head.appendChild(link);
        }
      });
    }
  }, []);

  // Lazy load non-critical resources
  const lazyLoadResources = useCallback(() => {
    if (typeof window !== 'undefined' && 'IntersectionObserver' in window) {
      const lazyImages = document.querySelectorAll('img[loading="lazy"]');
      const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const img = entry.target as HTMLImageElement;
            if (img.dataset.src) {
              img.src = img.dataset.src;
              img.removeAttribute('data-src');
              imageObserver.unobserve(img);
            }
          }
        });
      }, {
        rootMargin: '50px',
      });

      lazyImages.forEach((img) => imageObserver.observe(img));
    }
  }, []);

  return {
    optimizeImages,
    lazyLoadResources,
  };
};