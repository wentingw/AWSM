"""Bounded RGB cache: retain attributes, reload immutable source PNG pixels."""
from dataclasses import replace
import cv2
import torch

class RGBReferenceStore:
    def __init__(self, files):
        self.files = files
        self.metadata = []
    def __len__(self):
        return len(self.metadata)
    def _read(self, index):
        bgr = cv2.imread(str(self.files[index]))
        if bgr is None:
            raise OSError(f'Cannot read frozen RGB {self.files[index]}')
        return torch.as_tensor(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)).float() / 255.0
    def append(self, frame):
        index = len(self.metadata)
        if index == 0 or index % 500 == 0:
            assert torch.equal(frame.rgb, self._read(index)), 'Readthrough cache requires unmodified RGB'
        self.metadata.append(replace(frame, rgb=torch.empty(0)))
    def __getitem__(self, index):
        return replace(self.metadata[index], rgb=self._read(index))

def install(files):
    from vipe.streams.base import CachedVideoStream, ProcessedVideoStream
    original = ProcessedVideoStream.cache
    def cache(self, desc='Caching', online=False, async_prefetch=False, prefetch_queue_size=16):
        if desc != 'process':
            return original(self, desc, online, async_prefetch, prefetch_queue_size)
        assert not async_prefetch
        assert len(self) == len(files)
        result = CachedVideoStream(self, desc)
        result.data = RGBReferenceStore(files)
        if not online:
            _ = result[len(result) - 1]
        return result
    ProcessedVideoStream.cache = cache
