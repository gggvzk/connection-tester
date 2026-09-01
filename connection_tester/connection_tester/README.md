# Connection Tester

Windows向けのローカルネットワーク接続テスターです。

## 構成

- `backend/` — Python + Flask API
- `frontend/` — React + TypeScript + TSX + CSS
- JSON APIでネットワーク情報を取得
- Wi-Fi SSID / BSSID / 電波強度 / チャンネル
- MAC / IPv4 / IPv6 / Gateway / DNS
- Ping
- グローバルIP
- NATはオプションのSTUNライブラリを使って推定（判定不能の場合は Unknown）

## 起動

### 1. Python

```powershell
cd backend
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
py app.py
```

APIは `http://127.0.0.1:5000` で起動します。

### 2. フロントエンド

別のターミナルで：

```powershell
cd frontend
npm install
npm run dev
```

表示されたURLをブラウザで開きます。

通常は `http://localhost:5173` です。

## 注意

このアプリは「このPC自身」のネットワーク情報を取得します。
BSSID、MACアドレス、ローカルIPなどは個人情報・ネットワーク情報として扱い、スクリーンショット等を公開するときは伏せることをおすすめします。

NATタイプはルーターやISPの構成によって正確に判定できない場合があります。
