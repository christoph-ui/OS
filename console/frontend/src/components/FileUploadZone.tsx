'use client';

import { useState } from 'react';

const colors = {
  dark: '#1e293b',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  midGray: '#94a3b8',
};

interface FileUploadZoneProps {
  onFilesSelected: (files: File[]) => void;
  uploading?: boolean;
}

export default function FileUploadZone({ onFilesSelected, uploading = false }: FileUploadZoneProps) {
  const [dragging, setDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);

    const files = Array.from(e.dataTransfer.files);
    onFilesSelected(files);
  };

  const handleFileInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      const files = Array.from(e.target.files);
      onFilesSelected(files);
    }
  };

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      style={{
        border: `2px dashed ${dragging ? colors.orange : colors.lightGray}`,
        borderRadius: 16,
        padding: 60,
        textAlign: 'center',
        backgroundColor: dragging ? `${colors.orange}08` : '#fff',
        transition: 'all 0.2s',
        cursor: uploading ? 'not-allowed' : 'pointer',
        opacity: uploading ? 0.6 : 1,
      }}
    >
      <div style={{
        fontSize: 48,
        marginBottom: 16,
      }}>
        📁
      </div>

      <h3 style={{
        fontFamily: "'Poppins', Arial, sans-serif",
        fontSize: 18,
        fontWeight: 600,
        margin: '0 0 8px',
        color: colors.dark,
      }}>
        {uploading ? 'Upload läuft...' : 'Dateien hochladen'}
      </h3>

      <p style={{
        fontSize: 14,
        color: colors.midGray,
        margin: '0 0 24px',
      }}>
        Drag & Drop oder klicken zum Auswählen
      </p>

      <input
        type="file"
        multiple
        onChange={handleFileInput}
        disabled={uploading}
        style={{ display: 'none' }}
        id="file-input"
      />

      <label
        htmlFor="file-input"
        style={{
          display: 'inline-block',
          padding: '12px 24px',
          backgroundColor: uploading ? colors.midGray : colors.orange,
          color: '#fff',
          borderRadius: 10,
          fontSize: 15,
          fontWeight: 600,
          cursor: uploading ? 'not-allowed' : 'pointer',
          fontFamily: "'Poppins', Arial, sans-serif",
        }}
      >
        {uploading ? 'Wird hochgeladen...' : 'Dateien auswählen'}
      </label>
    </div>
  );
}
