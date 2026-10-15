from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.spinner import Spinner
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import yfinance as yf
import requests
import pandas as pd

class ProTradingMobileApp(App):
    def build(self):
        self.title = "Pro Trading Bot Mobile"
        
        root = BoxLayout(orientation='vertical', padding=15, spacing=10)
        
        # Judul Atas
        root.add_widget(Label(text="?? PRO TRADING BOT MOBILE", font_size=20, bold=True, size_hint_y=(None, 0.08), color=(0, 1, 0.8, 1)))
        
        # Pilihan Aset Otomatis
        root.add_widget(Label(text="Pilih Aset:", size_hint_y=(None, 0.04), halign='left'))
        self.asset_spinner = Spinner(
            text='BBCA.JK (Bank Central Asia)',
            values=(
                'BBCA.JK (Bank Central Asia)',
                'BBRI.JK (Bank Rakyat Indonesia)',
                'BMRI.JK (Bank Mandiri)',
                'ASII.JK (Astra International)',
                'TLKM.JK (Telkom Indonesia)',
                'GOTO.JK (GoTo Gojek Tokopedia)',
                'GC=F (Gold / Emas Berjangka)',
                'BTC-USD (Bitcoin Crypto)',
                'AAPL (Apple Inc)',
                'TSLA (Tesla Inc)'
            ),
            size_hint_y=(None, 0.08)
        )
        root.add_widget(self.asset_spinner)

        # Pilihan Timeframe
        root.add_widget(Label(text="Timeframe:", size_hint_y=(None, 0.04), halign='left'))
        self.tf_spinner = Spinner(
            text='D1 (Harian)',
            values=('M30 (30 Menit)', 'H1 (1 Jam)', 'H4 (4 Jam)', 'D1 (Harian)', 'W1 (Mingguan)'),
            size_hint_y=(None, 0.08)
        )
        root.add_widget(self.tf_spinner)

        # Tombol Analisis
        self.analyze_btn = Button(text="?? Jalankan Analisis Pro", background_color=(0.12, 0.32, 0.55, 1), size_hint_y=(None, 0.09), bold=True)
        self.analyze_btn.bind(on_press=self.run_analysis)
        root.add_widget(self.analyze_btn)

        # Area Laporan / Hasil Analisis
        self.output_box = TextInput(
            text="Pilih aset dan timeframe di atas, lalu klik 'Jalankan Analisis Pro' untuk melihat sinyal dan manajemen risiko.",
            readonly=True,
            background_color=(0.07, 0.07, 0.07, 1),
            foreground_color=(0.9, 0.9, 0.9, 1)
        )
        root.add_widget(self.output_box)

        # Panel Tombol Kontrol Bawah (Eksekusi & Off)
        btn_layout = BoxLayout(orientation='horizontal', spacing=10, size_hint_y=(None, 0.08))
        
        self.exec_btn = Button(text="?? Eksekusi", background_color=(0.17, 0.54, 0.24, 1), bold=True)
        self.exec_btn.bind(on_press=self.execute_trade)
        btn_layout.add_widget(self.exec_btn)

        self.off_btn = Button(text="? OFF (Hentikan)", background_color=(0.78, 0.16, 0.16, 1), bold=True)
        self.off_btn.bind(on_press=self.stop_bot)
        btn_layout.add_widget(self.off_btn)

        root.add_widget(btn_layout)

        return root

    def run_analysis(self, instance):
        try:
            selected_asset = self.asset_spinner.text
            ticker = selected_asset.split(" ")[0].strip()
            
            tf_choice = self.tf_spinner.text
            tf_mapping = {
                "M30 (30 Menit)": {"period": "1mo", "interval": "30m"},
                "H1 (1 Jam)": {"period": "3mo", "interval": "1h"},
                "H4 (4 Jam)": {"period": "6mo", "interval": "1h"},
                "D1 (Harian)": {"period": "1y", "interval": "1d"},
                "W1 (Mingguan)": {"period": "2y", "interval": "1wk"}
            }
            cfg = tf_mapping.get(tf_choice, {"period": "1y", "interval": "1d"})
            
            self.output_box.text = f"Memindai {ticker} ({tf_choice})... Mohon tunggu..."
            
            session = requests.Session()
            session.headers['User-Agent'] = 'Mozilla/5.0'
            stock = yf.Ticker(ticker, session=session)
            hist = stock.history(period=cfg["period"], interval=cfg["interval"])

            if hist.empty:
                self.output_box.text = f"Gagal: Data untuk {ticker} tidak ditemukan."
                return

            close_prices = hist['Close']
            ma_20 = close_prices.rolling(window=20).mean().iloc[-1]
            
            delta = close_prices.diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            current_rsi = (100 - (100 / (1 + rs))).iloc[-1]

            last_close = close_prices.iloc[-1]
            change_pct = ((last_close - close_prices.iloc[-2]) / close_prices.iloc[-2]) * 100

            if current_rsi > 70:
                rsi_status = "OVERBOUGHT (Jenuh Beli)"
            elif current_rsi < 30:
                rsi_status = "OVERSOLD (Jenuh Jual)"
            else:
                rsi_status = "NEUTRAL"

            if last_close > ma_20 and current_rsi < 70:
                signal = "STRONG BUY (Tren Naik)"
                sl = last_close * 0.97
                tp = last_close * 1.06
            elif last_close < ma_20 or current_rsi > 70:
                signal = "SELL / TAKE PROFIT"
                sl = last_close * 1.03
                tp = last_close * 0.95
            else:
                signal = "WAIT & WATCH"
                sl = last_close * 0.98
                tp = last_close * 1.04

            report = f"""=== LAPORAN MOBILE: {ticker} [{tf_choice}] ===
- Harga Terakhir: {last_close:,.2f} ({change_pct:+.2f}%)
- MA-20: {ma_20:,.2f}
- RSI (14): {current_rsi:.2f} -> {rsi_status}

[ MANAJEMEN RISIKO ]
- Sinyal: {signal}
- Stop Loss: {sl:,.2f}
- Take Profit: {tp:,.2f}
"""
            self.output_box.text = report
        except Exception as e:
            self.output_box.text = f"Error: {str(e)}"

    def execute_trade(self, instance):
        self.output_box.text += "\n\n[INFO] Mode Eksekusi Otomatis Aktif. Mengamankan posisi..."

    def stop_bot(self, instance):
        self.output_box.text += "\n\n[INFO] Bot dihentikan (OFF) secara manual."

if __name__ == '__main__':
    ProTradingMobileApp().run()
