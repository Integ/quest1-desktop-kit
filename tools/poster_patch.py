"""Restore the omitted CarouselItem::UserData assignment in the pinned ARM64 cinema.

SPDX-License-Identifier: GPL-3.0-or-later.

Upstream AppSelectionView::SetAppList omits `item->UserData = (void *)movie`.
MoviePosterComponent::SetItem treats a null UserData as an empty slot and hides
the poster. PcSelectionView already has this assignment. At 0xa3fe4, x25 is
the new CarouselItem and x27 is the PcDef read at 0xa3fc0. Replace the inlined
constructor's `str xzr, [x25, #0x18]` with `str x27, [x25, #0x18]`.
Full input/output hashes pin the original layout and reject other binaries.
"""
import hashlib

from common import KitError

LIBRARY = 'lib/arm64-v8a/libcinema.so'
BEFORE_SHA = 'bcdced76fea31bdf50f80193a579fe2e71e21aeca5161d5ececde265c329ba31'
AFTER_SHA = 'ef801ee9ec18dbe6c5690b18f1867c6da2ec34c552c55c7101ae03d10a2d905d'
OFFSET = 0xa3fe4


def fix_posters(data: bytes) -> bytes:
    if hashlib.sha256(data).hexdigest() != BEFORE_SHA:
        raise KitError('Poster fix requires the pinned v8 ARM64 libcinema.so')
    if data[OFFSET:OFFSET + 4] != bytes.fromhex('3f0f00f9'):
        raise KitError('Unexpected poster instruction; refusing to patch')
    fixed = data[:OFFSET] + bytes.fromhex('3b0f00f9') + data[OFFSET + 4:]
    if hashlib.sha256(fixed).hexdigest() != AFTER_SHA:
        raise KitError('Poster fix output checksum mismatch')
    return fixed
