import { FormEvent, useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Html5Qrcode } from "html5-qrcode";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";

type CheckInResult = {
  customer_id: string;
  first_name: string;
  last_name?: string | null;
  phone_number: string;
  total_visits: number;
  total_spending: number;
  is_new_customer: boolean;
};

const UUID_RE = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

function friendlyCheckInError(raw: string): string {
  const msg = raw.toLowerCase();
  if (
    msg.includes("uuid_parsing") ||
    msg.includes("valid uuid") ||
    msg.includes("invalid group") ||
    msg.includes("invalid uuid")
  ) {
    return "No customer found. If you did not enter the full UUID, paste the complete token from the Mini App.";
  }
  if (msg.includes("not found")) {
    return "No customer found for this QR token.";
  }
  // Avoid dumping raw FastAPI validation arrays
  if (raw.trim().startsWith("[") || raw.trim().startsWith("{")) {
    return "No customer found. Check that the UUID is complete and try again.";
  }
  return raw;
}

export default function CheckInPage() {
  const { staff } = useAuth();
  const navigate = useNavigate();
  const [mode, setMode] = useState<"scan" | "qr" | "phone">("scan");
  const [qrToken, setQrToken] = useState("");
  const [phone, setPhone] = useState("");
  const [firstName, setFirstName] = useState("");
  const [result, setResult] = useState<CheckInResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  /* ── Camera scanner state ── */
  const [scanning, setScanning] = useState(false);
  const scannerRef = useRef<Html5Qrcode | null>(null);
  const scanContainerId = "qr-scanner-region";

  const stopScanner = useCallback(async () => {
    if (scannerRef.current) {
      try {
        await scannerRef.current.stop();
      } catch {
        /* already stopped */
      }
      scannerRef.current.clear();
      scannerRef.current = null;
    }
    setScanning(false);
  }, []);

  const handleScanResult = useCallback(
    async (decodedText: string) => {
      if (!staff || busy) return;
      await stopScanner();

      const token = decodedText.trim();
      if (!UUID_RE.test(token)) {
        setError("No customer found. If you did not enter the full UUID, paste the complete token from the Mini App.");
        return;
      }

      setBusy(true);
      setError(null);
      setResult(null);
      try {
        const data = await api.checkinQr(token, staff.id);
        setResult(data as CheckInResult);
      } catch (err) {
        setError(friendlyCheckInError(err instanceof Error ? err.message : "Check-in failed"));
      } finally {
        setBusy(false);
      }
    },
    [staff, busy, stopScanner],
  );

  const startScanner = useCallback(async () => {
    setResult(null);
    setError(null);
    const html5Qr = new Html5Qrcode(scanContainerId);
    scannerRef.current = html5Qr;
    setScanning(true);
    try {
      await html5Qr.start(
        { facingMode: "environment" },
        { fps: 10, qrbox: { width: 250, height: 250 } },
        (decoded) => { handleScanResult(decoded); },
        () => {},
      );
    } catch (err) {
      setScanning(false);
      setError(
        err instanceof Error
          ? `Camera error: ${err.message}`
          : "Could not access camera. Make sure camera permissions are allowed.",
      );
    }
  }, [handleScanResult]);

  useEffect(() => {
    return () => { stopScanner(); };
  }, [stopScanner]);

  useEffect(() => {
    if (mode !== "scan") { stopScanner(); }
  }, [mode, stopScanner]);

  /* ── Phone live search ── */
  useEffect(() => {
    if (mode !== "phone") return;
    if (!phone.trim() && !firstName.trim()) {
      setResult(null);
      setError(null);
      return;
    }
    const timer = setTimeout(async () => {
      if (!staff) return;
      setBusy(true);
      setError(null);
      try {
        const data = await api.checkinPhone({
          phone_number: phone.trim(),
          staff_id: staff.id,
          first_name: firstName.trim() || undefined,
        });
        setResult(data as CheckInResult);
      } catch (err: unknown) {
        setResult(null);
        if (err instanceof Error && !err.message.includes("not found")) {
          setError(err.message);
        }
      } finally {
        setBusy(false);
      }
    }, 400);
    return () => clearTimeout(timer);
  }, [phone, firstName, staff, mode]);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    if (!staff) return;
    setBusy(true);
    setError(null);
    setResult(null);

    if (mode === "qr") {
      const token = qrToken.trim();
      if (!UUID_RE.test(token)) {
        setBusy(false);
        setError(
          "No customer found. If you did not enter the full UUID, paste the complete token from the Mini App.",
        );
        return;
      }
    }

    try {
      const data =
        mode === "qr"
          ? await api.checkinQr(qrToken.trim(), staff.id)
          : await api.checkinPhone({
              phone_number: phone.trim(),
              staff_id: staff.id,
              first_name: firstName.trim() || undefined,
            });
      setResult(data as CheckInResult);
    } catch (err) {
      setError(friendlyCheckInError(err instanceof Error ? err.message : "Check-in failed"));
    } finally {
      setBusy(false);
    }
  }

  function goLogService() {
    if (!result) return;
    const fullName = `${result.first_name} ${result.last_name || ""}`.trim();
    const params = new URLSearchParams({
      customer_id: result.customer_id,
      customer_name: fullName,
      phone: result.phone_number,
    });
    navigate(`/visits?${params.toString()}`);
  }

  const customerName = result
    ? `${result.first_name} ${result.last_name || ""}`.trim()
    : "";

  return (
    <div className="page">
      <header className="page-head">
        <div>
          <h1>Check-in</h1>
          <p className="muted">Scan QR from Mini App or look up by phone</p>
        </div>
      </header>

      <div className="tabs">
        <button type="button" className={mode === "scan" ? "active" : ""} onClick={() => setMode("scan")}>
          Scan QR
        </button>
        <button type="button" className={mode === "qr" ? "active" : ""} onClick={() => setMode("qr")}>
          QR token
        </button>
        <button
          type="button"
          className={mode === "phone" ? "active" : ""}
          onClick={() => setMode("phone")}
        >
          Phone
        </button>
      </div>

      {/* ── Camera scanner tab ── */}
      {mode === "scan" && (
        <div className="panel" style={{ textAlign: "center" }}>
          <div
            id={scanContainerId}
            style={{ width: "100%", maxWidth: 400, margin: "0 auto 1rem" }}
          />
          {!scanning && !result && (
            <button type="button" onClick={startScanner} disabled={busy}>
              {busy ? "Looking up…" : "Start camera"}
            </button>
          )}
          {scanning && (
            <p className="muted">Point the camera at the customer's QR code…</p>
          )}
          {error && <p className="error-text">{error}</p>}
          {!scanning && !result && !error && (
            <p className="muted" style={{ marginTop: "0.5rem" }}>
              Click "Start camera" then point at the customer's Mini App QR code.
            </p>
          )}
        </div>
      )}

      {/* ── Manual QR / Phone tabs ── */}
      {mode !== "scan" && (
        <form className="panel form-grid" onSubmit={onSubmit}>
          {mode === "qr" ? (
            <label>
              QR token (UUID from customer Mini App)
              <input value={qrToken} onChange={(e) => setQrToken(e.target.value)} required />
            </label>
          ) : (
            <>
              <label>
                Phone number
                <input value={phone} onChange={(e) => setPhone(e.target.value)} required />
              </label>
              <label>
                First name (optional)
                <input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </label>
            </>
          )}
          {error && <p className="error-text">{error}</p>}

          {mode === "qr" && (
            <button type="submit" disabled={busy}>
              {busy ? "Looking up…" : "Check in"}
            </button>
          )}
        </form>
      )}

      {result && (
        <section className="panel result-card">
          <h2>Customer found</h2>
          <p>
            <strong>Name:</strong> {customerName}
          </p>
          <p>
            <strong>Phone:</strong> {result.phone_number}
          </p>
          <p>
            <strong>Visits:</strong> {result.total_visits}
          </p>
          <p className="muted">Customer ID: {result.customer_id}</p>
          <div className="row-actions" style={{ marginTop: "0.75rem" }}>
            <button type="button" onClick={goLogService}>
              Log the visit
            </button>
          </div>
        </section>
      )}
    </div>
  );
}
