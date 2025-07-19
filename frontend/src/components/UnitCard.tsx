import React from 'react';
import type { Unit } from '../types';
import { formatPrice, formatArea, formatBedrooms, formatBathrooms } from '../utils/language';
import { MapPin, Home, Bath, Maximize, ExternalLink, Heart } from 'lucide-react';

interface UnitCardProps {
  unit: Unit;
  language?: 'ar' | 'en';
}

export const UnitCard: React.FC<UnitCardProps> = ({ unit, language = 'en' }) => {
  const isRTL = language === 'ar';

  const renderPhotos = () => {
    if (!unit.photos_urls || unit.photos_urls.length === 0) {
      return null;
    }

    return (
      <div className="flex flex-wrap gap-2 mt-3">
        {unit.photos_urls.slice(0, 2).map((url, index) => (
          <div key={index} className="relative">
            <img
              src={url}
              alt={`Unit ${unit.unit_number} - Photo ${index + 1}`}
              className="w-16 h-16 object-cover rounded-lg cursor-pointer hover:opacity-80 transition-opacity"
              onClick={() => window.open(url, '_blank')}
              onError={(e) => {
                const target = e.target as HTMLImageElement;
                target.style.display = 'none';
              }}
            />
            {unit.photos_urls.length > 2 && index === 1 && (
              <div className="absolute inset-0 bg-black bg-opacity-50 rounded-lg flex items-center justify-center">
                <span className="text-white text-xs font-semibold">
                  +{unit.photos_urls.length - 2}
                </span>
              </div>
            )}
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className={`unit-card ${isRTL ? 'text-right' : 'text-left'}`} dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Header */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-gray-900 text-lg">
            {language === 'ar' ? 'الوحدة' : 'Unit'} {unit.unit_number || 'N/A'}
          </h3>
          <div className="flex items-center text-gray-600 mt-1">
            <MapPin className="w-4 h-4 mr-1" />
            <span className="text-sm">{unit.address}</span>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold text-green-600">
            {formatPrice(unit.price_jod, language)}
          </div>
        </div>
      </div>

      {/* Details */}
      <div className="grid grid-cols-3 gap-4 mb-3">
        <div className="flex items-center text-gray-600">
          <Home className="w-4 h-4 mr-2" />
          <span className="text-sm">{formatBedrooms(unit.bedrooms, language)}</span>
        </div>
        <div className="flex items-center text-gray-600">
          <Bath className="w-4 h-4 mr-2" />
          <span className="text-sm">{formatBathrooms(unit.bathrooms, language)}</span>
        </div>
        <div className="flex items-center text-gray-600">
          <Maximize className="w-4 h-4 mr-2" />
          <span className="text-sm">{formatArea(unit.size_sqm, language)}</span>
        </div>
      </div>

      {/* Description */}
      {unit.description_ar && (
        <div className="mb-3">
          <p className="text-gray-700 text-sm leading-relaxed arabic-text" dir="rtl">
            {unit.description_ar.length > 200 
              ? `${unit.description_ar.substring(0, 200)}...`
              : unit.description_ar
            }
          </p>
        </div>
      )}

      {/* Photos */}
      {renderPhotos()}

      {/* Additional Info */}
      <div className="mt-3 pt-3 border-t border-gray-100">
        <div className="flex justify-between items-center text-xs text-gray-500">
          <span>
            {language === 'ar' ? 'الطابق' : 'Floor'}: {unit.floor_number || 'N/A'}
          </span>
          {unit.floor_type && (
            <span>
              {language === 'ar' ? 'نوع الطابق' : 'Floor Type'}: {unit.floor_type}
            </span>
          )}
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-4 flex gap-2">
        <button
          onClick={() => window.open(`https://wa.me/962790342041?text=I'm interested in Unit ${unit.unit_number} at ${unit.address}`, '_blank')}
          className="flex-1 bg-green-500 hover:bg-green-600 text-white text-sm py-2 px-3 rounded-lg transition-colors duration-200 flex items-center justify-center"
        >
          <ExternalLink className="w-4 h-4 mr-1" />
          {language === 'ar' ? 'تواصل معنا' : 'Contact Us'}
        </button>
        <button
          onClick={() => {
            // Add to favorites functionality
            console.log('Added to favorites:', unit.unit_id);
          }}
          className="bg-gray-100 hover:bg-gray-200 text-gray-700 text-sm py-2 px-3 rounded-lg transition-colors duration-200"
          title={language === 'ar' ? 'أضف للمفضلة' : 'Add to favorites'}
        >
          <Heart className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
};