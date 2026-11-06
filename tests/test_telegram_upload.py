import importlib.util
from pathlib import Path
import tempfile
import unittest
import asyncio
import types
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('drive_to_telegram', Path(__file__).resolve().parents[1] / 'scripts/drive_to_telegram.py')
uploader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(uploader)


class UploadPlanTests(unittest.TestCase):
    def test_global_lesson_order_overrides_section_order(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d)
            for name in ['الف/010 - ده.mp4', 'ب/002 - دو.mp4', 'ب/001 - یک.mp4', 'ب/003 - ناقص.part']:
                file = root / name
                file.parent.mkdir(exist_ok=True)
                file.write_bytes(b'video')
            self.assertEqual([f.name[:3] for f in uploader.videos(root)], ['001', '002', '010'])

    def test_catalog_keeps_numbers_when_courses_are_added_or_removed(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'courses'; root.mkdir()
            state = Path(d) / 'catalog.json'
            for name in ['Course 10', 'Course 2']:
                course = root / name; course.mkdir(); (course / '001.mp4').write_bytes(b'video')
            self.assertEqual(uploader.catalog(root, state), ['Course 2', 'Course 10'])
            (root / 'Course 2' / '001.mp4').unlink(); (root / 'Course 2').rmdir()
            course = root / 'Course 1'; course.mkdir(); (course / '001.mp4').write_bytes(b'video')
            self.assertEqual(uploader.catalog(root, state), ['Course 2', 'Course 10', 'Course 1'])

    def test_range_rejects_invalid_input(self):
        self.assertEqual(uploader.parse_range('1-12', 12), list(range(12)))
        self.assertEqual(uploader.parse_range('3', 12), [2])
        for text in ['0', '3-1', '1-13', 'all', '1-2 junk']:
            with self.assertRaises(ValueError):
                uploader.parse_range(text, 12)

    def test_caption_has_persian_hashtag_and_safe_length(self):
        course = Path('/courses/هوش-مصنوعی')
        text = uploader.caption(course, course / 'فصل اول' / '001 - مقدمه.mp4')
        self.assertIn('فصل اول\n001 - مقدمه', text)
        self.assertTrue(text.endswith('#هوش_مصنوعی'))
        long = uploader.caption(course, course / ('😀' * 900 + '.mp4'))
        self.assertLessEqual(len(long.encode('utf-16-le')) // 2, 1024)


class UploadFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_owner_control_order_and_persistent_resume_without_network(self):
        uploads = []
        notes = []

        class FakeClient:
            def __init__(self, *args, **kwargs):
                pass

            async def start(self):
                pass

            async def get_me(self):
                return types.SimpleNamespace(id=123)

            async def get_input_entity(self, value):
                return value

            async def send_message(self, target, text, **kwargs):
                notes.append(text)

            async def send_file(self, target, file, **kwargs):
                uploads.append(Path(file).name)
                self.test_caption = kwargs['caption']
                return types.SimpleNamespace(id=len(uploads))

            def on(self, event):
                def register(handler):
                    self.handler = handler
                    return handler
                return register

            async def run_until_disconnected(self):
                # Commands from other accounts/chats must not start a queue.
                await self.handler(types.SimpleNamespace(sender_id=456, chat_id=123, raw_text='/gr 1'))
                await self.handler(types.SimpleNamespace(sender_id=123, chat_id=999, raw_text='/gr 1'))
                await asyncio.sleep(0)
                if uploads:
                    raise AssertionError('Unauthorized command accepted')
                for _ in range(2):
                    await self.handler(types.SimpleNamespace(sender_id=123, chat_id=123, raw_text='/gr 1'))
                    for attempt in range(200):
                        if sum(note.startswith('تمام شد') for note in notes) >= _ + 1:
                            break
                        await asyncio.sleep(.001)
                    else:
                        raise AssertionError('Queue did not finish')

            async def disconnect(self):
                pass

        fake = types.ModuleType('telethon')
        fake.TelegramClient = FakeClient
        fake.events = types.SimpleNamespace(NewMessage=lambda **kw: None)
        fake.utils = types.SimpleNamespace(get_peer_id=lambda peer: 123)
        errors = types.ModuleType('telethon.errors')
        errors.FloodWaitError = type('FloodWaitError', (Exception,), {})
        with tempfile.TemporaryDirectory() as d:
            root = Path(d) / 'courses'; course = root / 'دوره'; course.mkdir(parents=True)
            for name in ['010 - ده.mp4', '001 - یک.mp4']:
                (course / name).write_bytes(b'video')
            args = types.SimpleNamespace(root=root, state_dir=Path(d) / 'state', target='me', delay=0)
            with patch.dict('sys.modules', {'telethon': fake, 'telethon.errors': errors}), patch.dict(
                'os.environ', {'TG_API_ID': '1', 'TG_API_HASH': 'dummy'}
            ):
                await uploader.run(args)
            self.assertEqual(uploads, ['001 - یک.mp4', '010 - ده.mp4'])
            self.assertTrue(any('قبلاً ارسال‌شده: 2' in note for note in notes))
            self.assertEqual(len(list(course.glob('*.mp4'))), 2)


if __name__ == '__main__':
    unittest.main()
