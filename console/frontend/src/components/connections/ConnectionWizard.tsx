"use client";

import { useState } from "react";
import { Loader2, CheckCircle2, AlertCircle, X } from "lucide-react";

interface MCP {
  id: string;
  name: string;
  display_name: string;
  description: string;
  category: string;
  icon: string;
  icon_color: string;
  logo_url?: string;
  connection_type: "oauth2" | "api_key" | "database" | "service_account";
  oauth_config?: {
    provider: string;
    scopes: string[];
  };
  api_docs_url: string;
  setup_instructions: string;
}

interface ConnectionWizardProps {
  mcp: MCP;
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (connectionId: string) => void;
}

type ConnectionStep = "configure" | "testing" | "success" | "error";

export default function ConnectionWizard({
  mcp,
  isOpen,
  onClose,
  onSuccess,
}: ConnectionWizardProps) {
  const [step, setStep] = useState<ConnectionStep>("configure");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [connectionId, setConnectionId] = useState<string | null>(null);

  // OAuth state
  const [oauthPopup, setOauthPopup] = useState<Window | null>(null);

  // API Key state
  const [apiKey, setApiKey] = useState("");
  const [apiSecret, setApiSecret] = useState("");
  const [connectionName, setConnectionName] = useState("");

  // Database state
  const [dbHost, setDbHost] = useState("");
  const [dbPort, setDbPort] = useState("5432");
  const [dbUsername, setDbUsername] = useState("");
  const [dbPassword, setDbPassword] = useState("");
  const [dbDatabase, setDbDatabase] = useState("");
  const [dbSslMode, setDbSslMode] = useState("prefer");

  if (!isOpen) return null;

  const handleOAuthConnect = async () => {
    setLoading(true);
    setError(null);

    try {
      const token = localStorage.getItem("0711_token");
      // Use Control Plane API (port 4080) for connections
      const apiUrl = "http://localhost:4080";
      const response = await fetch(`${apiUrl}/api/connections/oauth/start`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          mcp_id: mcp.id,
          provider_name: mcp.oauth_config?.provider,
        }),
      });

      if (!response.ok) throw new Error("Failed to initiate OAuth flow");

      const data = await response.json();

      // Open OAuth popup
      const popup = window.open(
        data.authorization_url,
        "oauth_popup",
        "width=600,height=700,left=100,top=100"
      );

      setOauthPopup(popup);

      // Poll for popup close
      const pollTimer = setInterval(() => {
        if (popup?.closed) {
          clearInterval(pollTimer);
          checkOAuthCallback(data.connection_id);
        }
      }, 500);

      setStep("testing");
    } catch (err: any) {
      setError(err.message);
      setStep("error");
    } finally {
      setLoading(false);
    }
  };

  const checkOAuthCallback = async (connId: string) => {
    setLoading(true);

    try {
      const token = localStorage.getItem("0711_token");
      const apiUrl = "http://localhost:4080";
      const response = await fetch(`${apiUrl}/api/connections/${connId}`, {
        headers: {
          ...(token && { Authorization: `Bearer ${token}` }),
        },
      });

      if (response.ok) {
        const connection = await response.json();
        if (connection.status === "active") {
          setConnectionId(connId);
          setStep("success");
          onSuccess?.(connId);
        } else {
          throw new Error("Connection failed");
        }
      } else {
        throw new Error("Failed to verify connection");
      }
    } catch (err: any) {
      setError(err.message);
      setStep("error");
    } finally {
      setLoading(false);
    }
  };

  const handleApiKeyConnect = async () => {
    setLoading(true);
    setError(null);
    setStep("testing");

    try {
      const token = localStorage.getItem("0711_token");
      const apiUrl = "http://localhost:4080";
      const response = await fetch(`${apiUrl}/api/connections/api-key`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          mcp_id: mcp.id,
          api_key: apiKey,
          api_secret: apiSecret || undefined,
          connection_name: connectionName || undefined,
          test_connection: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create connection");
      }

      const connection = await response.json();
      setConnectionId(connection.id);
      setStep("success");
      onSuccess?.(connection.id);
    } catch (err: any) {
      setError(err.message);
      setStep("error");
    } finally {
      setLoading(false);
    }
  };

  const handleDatabaseConnect = async () => {
    setLoading(true);
    setError(null);
    setStep("testing");

    try {
      const token = localStorage.getItem("0711_token");
      const apiUrl = "http://localhost:4080";
      const response = await fetch(`${apiUrl}/api/connections/database`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token && { Authorization: `Bearer ${token}` }),
        },
        body: JSON.stringify({
          mcp_id: mcp.id,
          host: dbHost,
          port: parseInt(dbPort),
          username: dbUsername,
          password: dbPassword,
          database: dbDatabase,
          ssl_mode: dbSslMode,
          connection_name: connectionName || undefined,
          test_connection: true,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to create connection");
      }

      const connection = await response.json();
      setConnectionId(connection.id);
      setStep("success");
      onSuccess?.(connection.id);
    } catch (err: any) {
      setError(err.message);
      setStep("error");
    } finally {
      setLoading(false);
    }
  };

  const renderConfigureStep = () => {
    // Handle MCPs without connection_type (legacy/core MCPs)
    if (!mcp.connection_type) {
      return (
        <div className="space-y-4">
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
            <p className="text-sm text-yellow-800">
              This MCP does not support external connections yet. It's a core platform MCP that works with your uploaded data.
            </p>
          </div>
          <button
            onClick={onClose}
            className="w-full bg-gray-600 hover:bg-gray-700 text-white font-medium py-3 px-4 rounded-lg transition-colors"
          >
            Close
          </button>
        </div>
      );
    }

    switch (mcp.connection_type) {
      case "oauth2":
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                You'll be redirected to {mcp.display_name} to authorize access.
                This connection is secure and you can revoke access at any time.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Connection Name (Optional)
              </label>
              <input
                type="text"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={`${mcp.display_name} Connection`}
                value={connectionName}
                onChange={(e) => setConnectionName(e.target.value)}
              />
            </div>

            <div className="bg-gray-50 p-4 rounded-lg text-sm">
              <h4 className="font-semibold mb-2">OAuth Scopes:</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-600">
                {mcp.oauth_config?.scopes.map((scope, i) => (
                  <li key={i}>{scope}</li>
                ))}
              </ul>
            </div>

            <button
              onClick={handleOAuthConnect}
              disabled={loading}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Connect with {mcp.display_name}
            </button>
          </div>
        );

      case "api_key":
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                Enter your {mcp.display_name} API key. This will be encrypted
                and stored securely.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Connection Name (Optional)
              </label>
              <input
                type="text"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={`${mcp.display_name} Connection`}
                value={connectionName}
                onChange={(e) => setConnectionName(e.target.value)}
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                API Key *
              </label>
              <input
                type="password"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="Enter API key"
                value={apiKey}
                onChange={(e) => setApiKey(e.target.value)}
                required
              />
            </div>

            {mcp.name === "stripe" && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  API Secret (Optional)
                </label>
                <input
                  type="password"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Enter API secret"
                  value={apiSecret}
                  onChange={(e) => setApiSecret(e.target.value)}
                />
              </div>
            )}

            <div className="bg-gray-50 p-4 rounded-lg">
              <a
                href={mcp.api_docs_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 text-sm hover:underline"
              >
                📚 View setup instructions →
              </a>
            </div>

            <button
              onClick={handleApiKeyConnect}
              disabled={loading || !apiKey}
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Connect & Test
            </button>
          </div>
        );

      case "database":
        return (
          <div className="space-y-4">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <p className="text-sm text-blue-800">
                Enter your database connection details. We'll test the
                connection before saving.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Connection Name (Optional)
              </label>
              <input
                type="text"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder={`${mcp.display_name} Connection`}
                value={connectionName}
                onChange={(e) => setConnectionName(e.target.value)}
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Host *
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="localhost or db.example.com"
                  value={dbHost}
                  onChange={(e) => setDbHost(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Port *
                </label>
                <input
                  type="number"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="5432"
                  value={dbPort}
                  onChange={(e) => setDbPort(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Database Name *
              </label>
              <input
                type="text"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="mydatabase"
                value={dbDatabase}
                onChange={(e) => setDbDatabase(e.target.value)}
                required
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Username *
                </label>
                <input
                  type="text"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="dbuser"
                  value={dbUsername}
                  onChange={(e) => setDbUsername(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Password *
                </label>
                <input
                  type="password"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="••••••••"
                  value={dbPassword}
                  onChange={(e) => setDbPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                SSL Mode
              </label>
              <select
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                value={dbSslMode}
                onChange={(e) => setDbSslMode(e.target.value)}
              >
                <option value="prefer">Prefer (default)</option>
                <option value="require">Require</option>
                <option value="disable">Disable</option>
              </select>
            </div>

            <button
              onClick={handleDatabaseConnect}
              disabled={
                loading || !dbHost || !dbPort || !dbDatabase || !dbUsername || !dbPassword
              }
              className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-3 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
            >
              {loading && <Loader2 className="h-4 w-4 animate-spin" />}
              Connect & Test
            </button>
          </div>
        );

      default:
        return <div>Unsupported connection type</div>;
    }
  };

  const renderTestingStep = () => (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <Loader2 className="h-12 w-12 animate-spin text-blue-600" />
      <h3 className="text-lg font-semibold text-gray-900">Testing Connection...</h3>
      <p className="text-sm text-gray-500 text-center">
        Verifying credentials and testing connectivity
      </p>
    </div>
  );

  const renderSuccessStep = () => (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <CheckCircle2 className="h-16 w-16 text-green-500" />
      <h3 className="text-xl font-semibold text-gray-900">Connected Successfully!</h3>
      <p className="text-sm text-gray-500 text-center">
        Your {mcp.display_name} connection is now active and ready to use.
      </p>
      <button
        onClick={onClose}
        className="mt-4 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-6 rounded-lg transition-colors"
      >
        Done
      </button>
    </div>
  );

  const renderErrorStep = () => (
    <div className="flex flex-col items-center justify-center py-12 space-y-4">
      <AlertCircle className="h-16 w-16 text-red-500" />
      <h3 className="text-xl font-semibold text-gray-900">Connection Failed</h3>
      <p className="text-sm text-gray-500 text-center">{error}</p>
      <div className="flex gap-2">
        <button
          onClick={() => setStep("configure")}
          className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Try Again
        </button>
        <button
          onClick={onClose}
          className="px-6 py-2 text-gray-500 hover:text-gray-700 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 flex items-center justify-center">
              {mcp.logo_url ? (
                <img
                  src={mcp.logo_url}
                  alt={mcp.display_name}
                  className="w-10 h-10 object-contain"
                  onError={(e) => {
                    e.currentTarget.style.display = 'none';
                    e.currentTarget.nextElementSibling!.style.display = 'block';
                  }}
                />
              ) : null}
              <span className={`text-3xl ${mcp.logo_url ? 'hidden' : ''}`}>{mcp.icon}</span>
            </div>
            <div>
              <h2 className="text-xl font-semibold text-gray-900">
                Connect to {mcp.display_name}
              </h2>
              <p className="text-sm text-gray-500 mt-1">{mcp.description}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors"
          >
            <X className="h-6 w-6" />
          </button>
        </div>

        {/* Content */}
        <div className="px-6 py-6 overflow-y-auto max-h-[calc(90vh-120px)]">
          {step === "configure" && renderConfigureStep()}
          {step === "testing" && renderTestingStep()}
          {step === "success" && renderSuccessStep()}
          {step === "error" && renderErrorStep()}
        </div>
      </div>
    </div>
  );
}
