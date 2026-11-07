#!/usr/bin/env python3
"""Read-only Drive uploader: send your own /gr command in the destination chat."""
from __future__ import annotations

import argparse
import asyncio
import getpass
import json
import os
from pathlib import Path
import re
import time

VIDEO_EXTENSIONS = {'.mp4', '.mkv', '.mov', '.webm', '.m4v', '.avi', '.ts'}


class WaitRetryMixin:
    """Respect RPC rate limits while preserving the current upload-part request."""

    async def _call(self, *args, **kwargs):
        while True:
            try:
                return await super()._call(*args, **kwargs)
            except self._rate_wait_errors as exc:
                seconds = max(1, exc.seconds) + 1
                print(f'Telegram {type(exc).__name__}: waiting {seconds}s; '
                      'then retrying the same request/upload part.', flush=True)
                await asyncio.sleep(seconds)


def natural(value: str):
    return tuple((0, int(p)) if p.isdecimal() else (1, p.casefold())
                 for p in re.split(r'(\d+)', value))


def videos(course: Path) -> list[Path]:
    def key(path):
        # Downloader lesson indexes are global across sections.
        number = re.match(r'^(\d+)\s*[-–.]', path.stem)
        return (0, int(number[1]), natural(str(path.relative_to(course)))) if number else (
            1, 0, natural(str(path.relative_to(course))))
    return sorted((p for p in course.rglob('*') if p.is_file()
                   and p.suffix.lower() in VIDEO_EXTENSIONS), key=key)


def hashtag(name: str) -> str:
    return '#' + (re.sub(r'[^\w]+', '_', name, flags=re.UNICODE).strip('_') or 'course')[:100]


def caption(course: Path, file: Path) -> str:
    section = str(file.parent.relative_to(course))
    text = f'{course.name}\n'
    if section != '.':
        text += section + '\n'
    text += file.stem
    # Stay below Telegram's regular caption limit, including UTF-16 characters.
    title = text.encode('utf-16-le')[:1700].decode('utf-16-le', errors='ignore')
    return title + '\n\n' + hashtag(course.name)


def save_json(path: Path, data):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
    temp.chmod(0o600)
    temp.replace(path)


def catalog(root: Path, path: Path, progress=None) -> list[str]:
    names = json.loads(path.read_text()) if path.exists() else []
    new = []
    for folder in sorted(root.iterdir(), key=lambda p: natural(p.name)):
        if not folder.is_dir() or folder.name.startswith('.') or folder.name in names:
            continue
        if progress:
            progress(f'Checking course: {folder.name}')
        # Stop at the first video; listing every lesson here is unnecessary.
        if any(p.suffix.lower() in VIDEO_EXTENSIONS and p.is_file() for p in folder.rglob('*')):
            new.append(folder.name)
    names.extend(new)
    save_json(path, names)
    return names


def parse_range(text: str, count: int) -> list[int]:
    match = re.fullmatch(r'(\d+)(?:\s*-\s*(\d+))?', text.strip())
    if not match:
        raise ValueError('مثال: /gr 1-12 یا /gr 3')
    start, end = int(match[1]), int(match[2] or match[1])
    if not 1 <= start <= end <= count:
        raise ValueError(f'بازه باید بین 1 و {count} باشد.')
    return list(range(start - 1, end))


async def run(args):
    print('Starting Telegram uploader...', flush=True)
    from telethon import TelegramClient, events
    from telethon.errors import FloodWaitError, FloodPremiumWaitError

    class UploadClient(WaitRetryMixin, TelegramClient):
        _rate_wait_errors = (FloodWaitError, FloodPremiumWaitError)

    root = args.root.expanduser().resolve()
    print(f'Checking Drive mount: {root}', flush=True)
    if not root.is_dir():
        raise SystemExit(f'Drive folder not found: {root}; mount Drive first.')
    state = args.state_dir.expanduser().resolve()
    print(f'Opening session/state folder: {state}', flush=True)
    state.mkdir(parents=True, exist_ok=True)
    state.chmod(0o700)
    # Prevent two processes from sending the same queue with the same state.
    import fcntl
    lock = (state / 'uploader.lock').open('a')
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        raise SystemExit('Another uploader is using this state directory.')
    binding = state / 'source.json'
    if binding.exists() and json.loads(binding.read_text()) != str(root):
        raise SystemExit('This state directory belongs to another source; use a different --state-dir.')
    save_json(binding, str(root))
    checkpoint = state / 'sent.json'
    sent = json.loads(checkpoint.read_text()) if checkpoint.exists() else {}
    api_id = int(os.environ.get('TG_API_ID') or input('api_id: '))
    api_hash = os.environ.get('TG_API_HASH') or getpass.getpass('api_hash: ')
    client = UploadClient(str(state / 'account'), api_id, api_hash,
                          flood_sleep_threshold=0, sequential_updates=False)
    print('Connecting to Telegram (30-second connection timeout)...', flush=True)
    try:
        await asyncio.wait_for(client.connect(), timeout=30)
        print('Logging in; an existing authorized session does not need a new code.', flush=True)
        await client.start(
            phone=lambda: input('Telegram phone number (e.g. +989...): '),
            code_callback=lambda: getpass.getpass('Telegram login code: '),
        )
        me = await client.get_me()
        print(f'Logged in: account ID {me.id}', flush=True)
        print('Scanning course folders...', flush=True)
        names = catalog(root, state / 'courses.json', progress=lambda text: print(text, flush=True))
        print(f'Courses indexed: {len(names)}', flush=True)
    except BaseException:
        await client.disconnect()
        lock.close()
        raise
    stop = asyncio.Event()
    task = None
    status = 'آماده'

    async def notify(text, destination):
        for offset in range(0, len(text), 3000):
            while True:
                try:
                    await client.send_message(destination, text[offset:offset + 3000], parse_mode=None)
                    break
                except FloodWaitError as exc:
                    await asyncio.sleep(exc.seconds + 1)

    async def upload(indexes, target, target_id, origin):
        nonlocal status
        completed = skipped = 0
        try:
            for index in indexes:
                course = root / names[index]
                if not course.is_dir():
                    raise FileNotFoundError(f'پوشه موجود نیست: {course.name}')
                for file in videos(course):
                    if stop.is_set():
                        status = 'متوقف شد؛ اجرای دوباره فایل‌های ثبت‌شده را رد می‌کند.'
                        await notify(status, origin)
                        return
                    stat = file.stat()
                    if not stat.st_size:
                        raise ValueError(f'فایل خالی: {file}')
                    identity = json.dumps([target_id, str(file.relative_to(root)),
                                           stat.st_size, stat.st_mtime_ns], ensure_ascii=False)
                    if identity in sent:
                        skipped += 1
                        continue
                    status = f'دوره {index + 1}: {course.name}\n{file.name}'
                    print(status, flush=True)
                    last_progress = 0.0

                    def progress(current, total):
                        nonlocal last_progress
                        if time.monotonic() - last_progress >= 15 or current == total:
                            print(f'  {current / total:.1%} ({current}/{total} bytes)', flush=True)
                            last_progress = time.monotonic()

                    while True:
                        try:
                            message = await client.send_file(
                                target, str(file), caption=caption(course, file),
                                parse_mode=None, supports_streaming=file.suffix.lower() == '.mp4',
                                progress_callback=progress,
                            )
                            break
                        except FloodWaitError as exc:
                            status = f'مکث تلگرام: {exc.seconds} ثانیه؛ {file.name}'
                            print(status, flush=True)
                            try:
                                await asyncio.wait_for(stop.wait(), timeout=exc.seconds + 1)
                                await notify('متوقف شد.', origin)
                                return
                            except asyncio.TimeoutError:
                                pass
                    sent[identity] = message.id
                    save_json(checkpoint, sent)
                    completed += 1
                    await asyncio.sleep(args.delay)
            status = f'تمام شد؛ ارسال: {completed}، قبلاً ارسال‌شده: {skipped}'
            await notify(status, origin)
        except Exception as exc:
            # Stop at the first failure to preserve ordering; never delete Drive files.
            status = f'ارسال متوقف شد: {type(exc).__name__}: {exc}'
            print(status, flush=True)
            await notify(status + '\nبعد از رفع خطا، همان بازه را دوباره بفرست.', origin)

    @client.on(events.NewMessage(outgoing=True, forwards=False, pattern=r'^/gr(?:\s|$)'))
    async def command(event):
        nonlocal task, names
        # Broadcast posts may identify the channel as sender. Require outgoing,
        # including in that case; never accept another user's incoming command.
        if not event.out or getattr(event, 'fwd_from', None):
            return
        if event.sender_id != me.id and not (
            event.is_channel and event.sender_id == event.chat_id
        ):
            return
        origin = await event.get_input_chat()

        async def reply(text):
            await notify(text, origin)

        text = event.raw_text[3:].strip()
        if text in ('', 'help'):
            await reply('راهنما:\n/gr list — شماره دوره‌ها\n/gr 1-12 — ارسال بازه\n/gr 3 — یک دوره\n/gr status — وضعیت\n/gr stop — توقف بعد از فایل فعلی\nمقصد: ' + (args.target or 'همین گفتگو'))
        elif text == 'list':
            names = catalog(root, state / 'courses.json')
            await reply('\n'.join(f'{i + 1}. {n}' for i, n in enumerate(names)) or 'دوره‌ای پیدا نشد.')
        elif text == 'status':
            await reply(status)
        elif text == 'stop':
            stop.set()
            await reply('درخواست توقف ثبت شد؛ ارسال فایل فعلی ممکن است ادامه پیدا کند.')
        elif task and not task.done():
            await reply('یک ارسال فعال است. ابتدا /gr status یا /gr stop را بفرست.')
        else:
            try:
                indexes = parse_range(text, len(names))
            except ValueError as exc:
                await reply(str(exc))
                return
            if args.target:
                value = int(args.target) if args.target.lstrip('-').isdigit() else args.target
                target = await client.get_input_entity(value)
                from telethon import utils
                target_id = str(me.id if args.target in ('me', 'self') else utils.get_peer_id(target))
            else:
                target, target_id = origin, str(event.chat_id)
            stop.clear()
            await reply(f'شروع ارسال {len(indexes)} دوره؛ مقصد: {args.target or event.chat_id}')
            task = asyncio.create_task(upload(indexes, target, target_id, origin))

    print('Ready. Send /gr list in any destination chat/channel. Drive videos are never deleted.', flush=True)
    try:
        await client.run_until_disconnected()
    finally:
        if task and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await client.disconnect()
        lock.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/content/drive/MyDrive/GreenOly'))
    parser.add_argument('--state-dir', type=Path, default=Path('/content/drive/MyDrive/.telegram-upload'))
    parser.add_argument('--target', help='Optional destination override; default: chat containing your /gr command')
    parser.add_argument('--delay', type=float, default=3, help='Seconds between videos')
    args = parser.parse_args()
    if args.delay < 0:
        parser.error('--delay must be nonnegative')
    os.umask(0o077)
    asyncio.run(run(args))


if __name__ == '__main__':
    main()
