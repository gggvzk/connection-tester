import { useCallback, useEffect, useState } from "react";

type Data = {
  wifi: {
    ssid?: string; bssid?: string; signal_percent?: number;
    channel?: number; radio_type?: string; receive_mbps?: string;
    transmit_mbps?: string; authentication?: string; cipher?: string;
  };
  network: {
    mac?: string; ipv4: string[]; ipv6: string[];
    gateway?: string; dns: string[];
  };
  connection: {
    ping: { success: boolean; ms: number | null; host: string };
    public_ip?: string;
    nat: { type: string; detail?: string };
  };
  timestamp: number;
};

const fmt = (v: unknown) =>
  v === null || v === undefined || v === "" ? "取得できません" : String(v);

function Card({ title, children }: { title: string; children: React.ReactNode }) {
  return <section className="card"><h2>{title}</h2>{children}</section>;
}

function Row({ label, value }: { label: string; value: unknown }) {
  return <div className="row"><span>{label}</span><strong>{fmt(value)}</strong></div>;
}

export default function App() {
  const [data, setData] = useState<Data | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [auto, setAuto] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const r = await fetch("/api/network", { cache: "no-store" });
      if (!r.ok) throw new Error("API error");
      setData(await r.json());
    } catch {
      setError("Pythonサーバーに接続できません。backend/app.py が起動しているか確認してください。");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);

  useEffect(() => {
    if (!auto) return;
    const id = setInterval(load, 5000);
    return () => clearInterval(id);
  }, [auto, load]);

  return (
    <main>
      <header>
        <div>
          <p className="eyebrow">NETWORK DIAGNOSTICS</p>
          <h1>Connection Tester</h1>
          <p className="sub">このPCのネットワーク接続状態をチェック</p>
        </div>
        <div className="actions">
          <label className="toggle">
            <input type="checkbox" checked={auto} onChange={e => setAuto(e.target.checked)} />
            自動更新
          </label>
          <button onClick={load} disabled={loading}>{loading ? "取得中…" : "今すぐ更新"}</button>
        </div>
      </header>

      {error && <div className="error">{error}</div>}

      {data && (
        <>
          <div className="hero-grid">
            <div className="hero-card">
              <span>Ping</span>
              <b>{data.connection.ping.ms !== null ? `${data.connection.ping.ms} ms` : "—"}</b>
              <small>{data.connection.ping.success ? "接続OK" : "応答なし"} · {data.connection.ping.host}</small>
            </div>
            <div className="hero-card">
              <span>NAT</span>
              <b>{fmt(data.connection.nat.type)}</b>
              <small>STUNによる推定</small>
            </div>
            <div className="hero-card">
              <span>Public IPv4</span>
              <b>{fmt(data.connection.public_ip)}</b>
              <small>外部サービスから見えるIP</small>
            </div>
          </div>

          <div className="grid">
            <Card title="📶 Wi-Fi">
              <Row label="SSID" value={data.wifi.ssid} />
              <Row label="BSSID" value={data.wifi.bssid} />
              <Row label="電波強度" value={data.wifi.signal_percent != null ? `${data.wifi.signal_percent}%` : null} />
              <Row label="チャンネル" value={data.wifi.channel} />
              <Row label="無線規格" value={data.wifi.radio_type} />
              <Row label="受信速度" value={data.wifi.receive_mbps ? `${data.wifi.receive_mbps} Mbps` : null} />
              <Row label="送信速度" value={data.wifi.transmit_mbps ? `${data.wifi.transmit_mbps} Mbps` : null} />
              <Row label="認証" value={data.wifi.authentication} />
              <Row label="暗号化" value={data.wifi.cipher} />
            </Card>

            <Card title="🌐 IP / Network">
              <Row label="MAC" value={data.network.mac} />
              <Row label="IPv4" value={data.network.ipv4.join(", ")} />
              <Row label="IPv6" value={data.network.ipv6.join(", ")} />
              <Row label="Gateway" value={data.network.gateway} />
              <Row label="DNS" value={data.network.dns.join(", ")} />
            </Card>

            <Card title="🧪 Connection">
              <Row label="Ping先" value={data.connection.ping.host} />
              <Row label="Ping" value={data.connection.ping.ms !== null ? `${data.connection.ping.ms} ms` : null} />
              <Row label="NAT Type" value={data.connection.nat.type} />
              <Row label="外部IP" value={data.connection.nat.external_ip || data.connection.public_ip} />
              {data.connection.nat.detail && <Row label="NATメモ" value={data.connection.nat.detail} />}
            </Card>

            <Card title="ℹ️ Status">
              <Row label="OS" value={navigator.platform} />
              <Row label="最終更新" value={new Date(data.timestamp * 1000).toLocaleTimeString("ja-JP")} />
              <Row label="更新間隔" value={auto ? "5秒" : "手動"} />
            </Card>
          </div>
        </>
      )}

      <footer>
        <span>Local Connection Tester</span>
        <span>•</span>
        <span>情報はこのPC上で取得</span>
      </footer>
    </main>
  );
}
