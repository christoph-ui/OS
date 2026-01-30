'use client';

import React from 'react';
import { colors, fonts } from './mcps/theme';

interface ProductCardProps {
  product: {
    product_code?: string;
    code?: string;
    name: string;
    description?: string;
    specifications?: any;
    specs?: any;
    documents?: any[];
  };
}

export default function ProductCard({ product }: ProductCardProps) {
  const specs = product.specs || product.specifications || product;
  const productCode = product.product_code || product.code || specs.sku || 'Unknown';
  const description = product.description || specs.short_description || product.name || '';
  const longDesc = specs.long_description || '';

  // Gruppiere Lightnet-Felder
  const basicInfo = {
    'SKU': specs.sku,
    'Produktname': specs.product_name,
    'Familie': specs.product_family,
    'Preis': specs.price_eur ? `€${specs.price_eur}` : null,
  };

  const opticalSpecs = {
    'Lichtverteilung': specs.light_distribution,
    'Lichtquelle': specs.light_source,
    'Optik': specs.optical_system,
    'Oberfläche': specs.surface,
    'Farbtemperatur': specs.color_temperature,
    'Farbwiedergabe': specs.color_rendering_index,
    'Lichtstrom': specs.luminous_flux,
    'Leistung': specs.power_consumption,
  };

  const technicalSpecs = {
    'Montage': specs.installation_type,
    'Form': specs.form,
    'Länge': specs.length_mm,
    'Breite': specs.width_mm,
    'Höhe': specs.height_mm,
    'Gewicht': specs.weight_kg,
    'Steuerung': specs.control,
    'Leistungsmodus': specs.power_mode,
  };

  const electricalSpecs = {
    'Schutzart IP': specs.protection_class_ip,
    'Schutzklasse': specs.protection_class,
    'Spannung': specs.voltage,
    'Frequenz': specs.frequency,
    'IK-Wert': specs.ik_value,
  };

  return (
    <div className="border rounded-lg p-6 mb-6" style={{ backgroundColor: colors.light, borderColor: colors.lightGray }}>
      {/* Header */}
      <div className="mb-6">
        <h2 className="text-2xl font-bold mb-2" style={{ color: colors.dark, fontFamily: fonts.heading }}>
          {productCode}
        </h2>
        <p className="text-sm mb-1" style={{ color: colors.midGray, fontFamily: fonts.body }}>{description}</p>
        {longDesc && <p className="text-xs mt-2" style={{ color: colors.darkGray, fontFamily: fonts.body }}>{longDesc.slice(0, 200)}...</p>}
      </div>

      {/* Basis-Informationen */}
      <SpecSection title="Basis-Informationen" specs={basicInfo} />

      {/* Optische Spezifikationen */}
      <SpecSection title="Optik & Licht" specs={opticalSpecs} />

      {/* Technische Daten */}
      <SpecSection title="Maße & Mechanik" specs={technicalSpecs} />

      {/* Elektrik */}
      <SpecSection title="Elektrik & Sicherheit" specs={electricalSpecs} />
    </div>
  );
}

function SpecSection({ title, specs }: { title: string; specs: Record<string, any> }) {
  const validSpecs = Object.entries(specs).filter(([_, value]) => value && value !== '' && value !== 'null');

  if (validSpecs.length === 0) return null;

  return (
    <div className="mb-6">
      <h3 className="text-sm font-semibold mb-3" style={{ color: colors.dark, fontFamily: fonts.heading }}>{title}</h3>
      <div className="grid grid-cols-2 gap-3">
        {validSpecs.map(([key, value]) => (
          <div key={key} className="border-l-2 pl-3" style={{ borderColor: colors.orange }}>
            <div className="text-xs" style={{ color: colors.midGray, fontFamily: fonts.body }}>{key}</div>
            <div className="text-sm font-medium" style={{ color: colors.dark, fontFamily: fonts.heading }}>{value}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function SpecBadge({ label, value }: { label: string; value: string }) {
  return (
    <div className="border rounded-lg p-3" style={{ backgroundColor: colors.dark + '05', borderColor: colors.lightGray }}>
      <div className="text-xs mb-1" style={{ color: colors.midGray, fontFamily: fonts.heading }}>{label}</div>
      <div className="text-lg font-semibold" style={{ color: colors.dark, fontFamily: fonts.heading }}>{value}</div>
    </div>
  );
}
