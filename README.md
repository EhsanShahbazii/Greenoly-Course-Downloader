<div align="center">

```
 ██████╗ ██████╗ ███████╗███████╗███╗   ██╗ ██████╗ ██╗  ██╗   ██╗
██╔════╝ ██╔══██╗██╔════╝██╔════╝████╗  ██║██╔═══██╗██║  ╚██╗ ██╔╝
██║  ███╗██████╔╝█████╗  █████╗  ██╔██╗ ██║██║   ██║██║   ╚████╔╝
██║   ██║██╔══██╗██╔══╝  ██╔══╝  ██║╚██╗██║██║   ██║██║    ╚██╔╝
╚██████╔╝██║  ██║███████╗███████╗██║ ╚████║╚██████╔╝███████╗██║
 ╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝╚═╝  ╚═══╝ ╚═════╝ ╚══════╝╚═╝
```

### دانلودر دوره‌های GreenOly TV

دانلود کل یک دوره، پوشه‌به‌پوشه، با نام فارسی هر درس و **بالاترین کیفیت موجود**.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Platform](https://img.shields.io/badge/macOS%20%7C%20Linux%20%7C%20Windows-lightgrey)
![License](https://img.shields.io/badge/استفاده-شخصی-00ff87)

</div>

---

## ✨ چه کار می‌کند؟

- 📚 ساختار کامل دوره را از سایت می‌خواند و **همهٔ درس‌ها** را به ترتیب دانلود می‌کند
- 🗂 برای هر بخش یک پوشه و برای هر درس یک فایل MP4 با **نام فارسی** می‌سازد
- 🎯 از مستر پلی‌لیست همیشه **بهترین کیفیت** (تا 720p در این سایت) را انتخاب می‌کند
- 🍪 کوکی را هم از **مرورگر** می‌خواند و هم از فایل `cookies.txt`
- ⚡ سگمنت‌ها را موازی دانلود می‌کند (۶ به‌طور پیش‌فرض) با تلاش مجدد خودکار
- 🔁 اگر قطع شد، دوباره اجرا کن؛ درس‌های دانلودشده **رد می‌شوند**
- 🎬 خروجی با `ffmpeg -c copy` ریمکس می‌شود؛ یعنی **بدون افت کیفیت** و سریع
- 💚 ترمینال زیبا: بنر گرادیانی، انیمیشن، نوار پیشرفت و گزارش پایانی

## 🚀 نصب

### 📦 نسخهٔ آماده (بدون نصب) — پیشنهادی

از صفحهٔ [Releases](https://github.com/EhsanShahbazii/Greenoly-Course-Downloader/releases)
فایل مناسب سیستم‌ات را دانلود کن، زیپ را باز کن و اجرا کن:

| سیستم | فایل | اجرا |
| --- | --- | --- |
| macOS (Apple Silicon) | `GreenOly-macos-arm64.zip` | دابل‌کلیک روی `Start.command` |
| macOS (Intel) | `GreenOly-macos-x64.zip` | دابل‌کلیک روی `Start.command` |
| Windows 10/11 | `GreenOly-windows-x64.zip` | دابل‌کلیک روی `GreenOly.exe` |
| Linux | `GreenOly-linux-x64.zip` | `./GreenOly` |

پایتون، Chromium، ffmpeg و کتابخانه‌ها داخل بسته هستند؛ نصب Python، pip و دانلود
جداگانهٔ مرورگر لازم نیست. **کل پوشه را از زیپ استخراج کن** و فایل اجرایی را از
پوشهٔ `browsers` و `_internal` جدا نکن. اینترنت فقط برای دسترسی به سایت و ویدئوها لازم است.

1. اول در مرورگر معمولی خودت وارد حساب GreenOly شو.
2. برنامه را باز کن و لینک دوره یا یکی از درس‌ها را وارد کن؛ همهٔ درس‌های دوره دانلود می‌شوند.
3. برای تشخیص خودکار کوکی مرورگر Enter بزن؛ یا مسیر فایل کوکی Netscape `cookies.txt` را بده.
   در مک می‌توانی فایل را داخل پنجرهٔ ترمینال بکشی. اگر تشخیص خودکار ممکن نباشد، برنامه فایل دستی می‌خواهد.
4. پوشهٔ ذخیره را انتخاب کن؛ پیش‌فرض اجرای تعاملی `Downloads/GreenOly` است.

کوکی داخل برنامه جاسازی یا همراه نسخه منتشر نمی‌شود؛ هر کاربر از حساب خودش استفاده می‌کند.
خواندن خودکار کوکی به مجوز سیستم و رمزگذاری مرورگر بستگی دارد؛ فایل دستی همیشه در دسترس است.
روی لینوکس مینیمال ممکن است کتابخانه‌های سیستمی موردنیاز Chromium نصب نباشند.

> نسخهٔ macOS امضای Developer ID و notarization ندارد؛ ممکن است Gatekeeper اجرای آن را
> نیازمند تأیید دستی کند. فقط فایل منتشرشده از مخزن اصلی را دریافت کن.

### 🧑‍💻 نصب از سورس

```bash
git clone https://github.com/EhsanShahbazii/Greenoly-Course-Downloader.git
cd Greenoly-Course-Downloader

python3 -m venv .venv
source .venv/bin/activate          # ویندوز: .venv\Scripts\activate

pip install -r requirements.txt
python -m playwright install chromium
```

ابزارهای سیستمی:

```bash
# macOS
brew install ffmpeg openssl

# Ubuntu / Debian
sudo apt install ffmpeg openssl
```

### 🪟 ویندوز

```powershell
git clone https://github.com/EhsanShahbazii/Greenoly-Course-Downloader.git
cd Greenoly-Course-Downloader

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
python -m playwright install chromium

winget install Gyan.FFmpeg
winget install ShiningLight.OpenSSL.Light
```

بعد از نصب، ترمینال را ببند و دوباره باز کن تا `ffmpeg` و `openssl` در `PATH` باشند.
سپس:

```powershell
python greenoly.py "https://greenoly.tv/courses/<slug>/lessons/<id>" --browser chrome
```

> اگر `openssl` پیدا نشد، مسیر نصب را دستی اضافه کن:
> `setx PATH "%PATH%;C:\Program Files\OpenSSL-Win64\bin"`

## 🎬 اجرا

ساده‌ترین حالت — کوکی مستقیم از مرورگر خوانده می‌شود:

```bash
python greenoly.py "https://greenoly.tv/courses/ترکیبیات/lessons/cmvzgc5m4026dhmo6v9xbpv0v"
```

یا با فایل کوکی:

```bash
python greenoly.py "<lesson-url>" --cookies greenoly.tv_cookies.txt
```

> 💡 اگر کوکی مرورگر خوانده نشد، یک‌بار در مرورگر لاگین کن و دوباره اجرا کن.
> روی macOS ممکن است سیستم اجازهٔ دسترسی به Keychain را بپرسد؛ «Allow» بزن.

## ⚙️ گزینه‌ها

| گزینه | توضیح |
| --- | --- |
| `--cookies PATH` | فایل کوکی Netscape (اختیاری) |
| `--browser NAME` | خواندن کوکی از `chrome`، `firefox`، `safari`، `edge`، `brave`… |
| `--out DIR` | پوشهٔ خروجی (پیش‌فرض `downloads`) |
| `--single` | فقط همان یک درس |
| `--limit N` | فقط N درس اول |
| `--quality 720p` | سقف کیفیت (پیش‌فرض `best`) |
| `--workers N` | تعداد دانلود هم‌زمان سگمنت‌ها (پیش‌فرض ۶) |
| `--list` | فقط فهرست درس‌ها را نشان بده |
| `--quiet` | خروجی ساده و بدون انیمیشن |

## 📁 ساختار خروجی

```
downloads/
├── معرفی دوره/
│   ├── 001 - معرفی دوره.mp4
│   └── 002 - نقشه راه.mp4
├── ترکیبیات - اصل شمول و عدم شمول/
│   ├── 003 - اصل شمول.mp4
│   └── ...
```

## 🧠 چطور کار می‌کند؟

1. **ساختار دوره** — صفحهٔ درس یک اپ Next.js است؛ داده‌ها از RSC payload خوانده می‌شوند.
2. **پلی‌لیست** — پلیر Kavimo مانیفست HLS را به‌صورت AES-GCM رمزنگاری‌شده می‌گیرد و فقط داخل
   جاوااسکریپت خودش رمزگشایی می‌کند. این ابزار `TextDecoder.prototype.decode` را در یک
   Chromium بدون‌هد هوک می‌کند تا پلی‌لیست رمزگشایی‌شده را بگیرد.
3. **دانلود** — سگمنت‌ها AES-128 هستند؛ موازی دانلود، با `openssl` رمزگشایی و به هم چسبانده می‌شوند.
4. **خروجی** — `ffmpeg -c copy` فایل TS را بدون رمزگذاری مجدد به MP4 تبدیل می‌کند.

## 🧩 ساختار پروژه

```
greenoly/
├── cli.py          # رابط خط فرمان
├── config.py       # تنظیمات و آدرس‌ها
├── cookies.py      # کوکی از مرورگر یا فایل
├── api.py          # ساختار دوره از سایت
├── browser.py      # گرفتن پلی‌لیست با Chromium
├── hls.py          # پارس مانیفست HLS
├── media.py        # رمزگشایی و ریمکس
├── downloader.py   # موتور دانلود
├── naming.py       # نام‌گذاری امن فایل‌ها
└── ui.py           # بنر، انیمیشن و نوار پیشرفت
```

## 🛠 رفع اشکال

| مشکل | راه‌حل |
| --- | --- |
| `Timed out waiting for the player playlist` | کوکی منقضی شده؛ دوباره لاگین کن |
| `No greenoly.tv cookies found` | با `--browser chrome` یا `--cookies` امتحان کن |
| `ffmpeg: command not found` | `brew install ffmpeg` |
| دانلود کند است | `--workers 12` |
| قطع‌وصل می‌شود | دوباره اجرا کن؛ از همان درس ادامه می‌دهد |

## ⚖️ یادآوری

این ابزار برای **پشتیبان‌گیری شخصی از دوره‌ای که خریده‌ای** ساخته شده است. فایل‌ها را
عمومی منتشر نکن و حق نشر مدرس را رعایت کن.

<div align="center">

ساخته‌شده با 💚 برای دانشجوهایی که دوست دارند درس‌ها همیشه در دسترسشان باشد.

</div>
