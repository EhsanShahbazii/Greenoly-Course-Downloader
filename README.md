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

