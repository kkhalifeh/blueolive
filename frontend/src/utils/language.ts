/**
 * Detect if text contains Arabic characters
 */
export const containsArabic = (text: string): boolean => {
  const arabicPattern = /[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]/;
  return arabicPattern.test(text);
};

/**
 * Detect language of text
 */
export const detectLanguage = (text: string): 'ar' | 'en' => {
  return containsArabic(text) ? 'ar' : 'en';
};

/**
 * Get text direction based on language
 */
export const getTextDirection = (language: 'ar' | 'en'): 'rtl' | 'ltr' => {
  return language === 'ar' ? 'rtl' : 'ltr';
};

/**
 * Get text alignment based on language
 */
export const getTextAlignment = (language: 'ar' | 'en'): 'right' | 'left' => {
  return language === 'ar' ? 'right' : 'left';
};

/**
 * Format text with appropriate CSS classes
 */
export const getLanguageClasses = (language: 'ar' | 'en'): string => {
  return language === 'ar' ? 'arabic-text' : 'english-text';
};

/**
 * Extract unit information from bot response
 */
export const parseUnitInfo = (text: string): {
  hasUnits: boolean;
  unitCount?: number;
  hasMoreUnits: boolean;
} => {
  // Check if response contains unit information
  const unitPattern = /Unit\s+\d+|الوحدة\s+\d+/;
  const hasUnits = unitPattern.test(text);
  
  // Extract unit count
  const countPattern = /Showing\s+(\d+)\s+of\s+(\d+)|عرض\s+(\d+)\s+من\s+(\d+)/;
  const countMatch = text.match(countPattern);
  
  // Check for pagination indicators
  const morePattern = /more\s+apartments?\s+available|would\s+you\s+like\s+to\s+see\s+more|المزيد\s+من\s+الوحدات/i;
  const hasMoreUnits = morePattern.test(text);
  
  return {
    hasUnits,
    unitCount: countMatch ? parseInt(countMatch[1] || countMatch[3]) : undefined,
    hasMoreUnits,
  };
};

/**
 * Format price for display
 */
export const formatPrice = (price: number, language: 'ar' | 'en' = 'en'): string => {
  const formatter = new Intl.NumberFormat(language === 'ar' ? 'ar-JO' : 'en-US', {
    style: 'currency',
    currency: 'JOD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  });
  
  return formatter.format(price);
};

/**
 * Format area for display
 */
export const formatArea = (area: number, language: 'ar' | 'en' = 'en'): string => {
  const suffix = language === 'ar' ? 'م²' : 'sqm';
  return `${area} ${suffix}`;
};

/**
 * Format bedroom count
 */
export const formatBedrooms = (count: number, language: 'ar' | 'en' = 'en'): string => {
  if (language === 'ar') {
    return count === 1 ? 'غرفة نوم واحدة' : `${count} غرف نوم`;
  }
  return count === 1 ? '1 bedroom' : `${count} bedrooms`;
};

/**
 * Format bathroom count
 */
export const formatBathrooms = (count: number, language: 'ar' | 'en' = 'en'): string => {
  if (language === 'ar') {
    return count === 1 ? 'حمام واحد' : `${count} حمامات`;
  }
  return count === 1 ? '1 bathroom' : `${count} bathrooms`;
};