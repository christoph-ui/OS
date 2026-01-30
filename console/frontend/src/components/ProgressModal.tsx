const colors = {
  dark: '#1e293b',
  light: '#faf9f5',
  midGray: '#94a3b8',
  lightGray: '#e8e6dc',
  orange: '#d97757',
  green: '#788c5d',
  blue: '#6a9bcc',
};

interface ProgressPhase {
  progress: number;
  message: string;
  explanation?: string;
  files_processed?: number;
  files_total?: number;
  phase?: string;
  current_file?: string;
}

interface ProgressModalProps {
  upload: ProgressPhase | null;
  ingestion: ProgressPhase | null;
  deployment: ProgressPhase | null;
  overallProgress: number;
  onClose?: () => void;
}

export default function ProgressModal({
  upload,
  ingestion,
  deployment,
  overallProgress,
  onClose,
}: ProgressModalProps) {
  const renderPhase = (name: string, phase: ProgressPhase | null, icon: string) => {
    if (!phase) {
      return (
        <div style={{
          padding: 20,
          backgroundColor: colors.lightGray,
          borderRadius: 12,
          opacity: 0.5,
        }}>
          <div style={{ fontSize: 24, marginBottom: 8 }}>{icon}</div>
          <div style={{ fontSize: 14, color: colors.midGray }}>{name}</div>
          <div style={{ fontSize: 12, color: colors.midGray, marginTop: 4 }}>Warten...</div>
        </div>
      );
    }

    return (
      <div style={{
        padding: 20,
        backgroundColor: '#fff',
        borderRadius: 12,
        border: `2px solid ${phase.progress === 100 ? colors.green : colors.orange}`,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12, marginBottom: 12 }}>
          <div style={{ fontSize: 24 }}>{icon}</div>
          <div style={{ flex: 1 }}>
            <div style={{ fontSize: 14, fontWeight: 600, color: colors.dark }}>{name}</div>
            <div style={{ fontSize: 12, color: colors.midGray }}>{phase.message}</div>
            {phase.files_total && phase.files_total > 0 && (
              <div style={{ fontSize: 11, color: colors.midGray, marginTop: 4 }}>
                📊 {phase.files_processed || 0} von {phase.files_total} Dateien
              </div>
            )}
            {phase.current_file && (
              <div style={{ fontSize: 11, color: colors.midGray, marginTop: 4, fontStyle: 'italic' }}>
                Aktuelle Datei: {phase.current_file}
              </div>
            )}
          </div>
          <div style={{ fontSize: 18, fontWeight: 600, color: colors.orange }}>
            {phase.progress}%
          </div>
        </div>

        {/* Progress Bar */}
        <div style={{
          height: 8,
          backgroundColor: colors.lightGray,
          borderRadius: 4,
          overflow: 'hidden',
          marginBottom: 8,
        }}>
          <div style={{
            width: `${phase.progress}%`,
            height: '100%',
            backgroundColor: phase.progress === 100 ? colors.green : colors.orange,
            transition: 'width 0.3s',
          }} />
        </div>

        {/* AI Explanation */}
        {phase.explanation && (
          <div style={{
            fontSize: 13,
            color: colors.midGray,
            lineHeight: 1.5,
            fontStyle: 'italic',
          }}>
            💡 {phase.explanation}
          </div>
        )}
      </div>
    );
  };

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      backgroundColor: 'rgba(20, 20, 19, 0.95)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 9999,
      padding: 20,
    }}>
      <div style={{
        backgroundColor: colors.light,
        borderRadius: 16,
        maxWidth: 800,
        width: '100%',
        padding: 40,
        boxShadow: '0 20px 60px rgba(0,0,0,0.5)',
      }}>
        <h2 style={{
          fontFamily: "'Poppins', Arial, sans-serif",
          fontSize: 24,
          fontWeight: 600,
          margin: '0 0 8px',
          color: colors.dark,
          textAlign: 'center',
        }}>
          🚀 Onboarding läuft
        </h2>

        <p style={{
          fontSize: 15,
          color: colors.midGray,
          margin: '0 0 32px',
          textAlign: 'center',
        }}>
          Ihre Daten werden verarbeitet - das dauert 2-5 Minuten
        </p>

        {/* Overall Progress */}
        <div style={{ marginBottom: 32 }}>
          <div style={{
            height: 12,
            backgroundColor: colors.lightGray,
            borderRadius: 6,
            overflow: 'hidden',
          }}>
            <div style={{
              width: `${overallProgress}%`,
              height: '100%',
              backgroundColor: colors.orange,
              transition: 'width 0.5s',
            }} />
          </div>
          <div style={{
            textAlign: 'center',
            fontSize: 13,
            color: colors.midGray,
            marginTop: 8,
          }}>
            Gesamt: {overallProgress}%
          </div>
        </div>

        {/* Phases */}
        <div style={{ display: 'grid', gap: 16 }}>
          {renderPhase('Upload', upload, '📤')}
          {renderPhase('Analyse & Verarbeitung', ingestion, '🔍')}
          {renderPhase('Deployment', deployment, '🚀')}
        </div>

        {overallProgress === 100 && onClose && (
          <button
            onClick={onClose}
            style={{
              width: '100%',
              marginTop: 24,
              padding: 14,
              backgroundColor: colors.green,
              color: '#fff',
              border: 'none',
              borderRadius: 10,
              fontSize: 16,
              fontWeight: 600,
              cursor: 'pointer',
            }}
          >
            ✓ Fertig - Weiter
          </button>
        )}
      </div>
    </div>
  );
}
