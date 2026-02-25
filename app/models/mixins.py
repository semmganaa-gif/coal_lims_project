# app/models/mixins.py
# -*- coding: utf-8 -*-
"""
Shared model mixins and constants.
"""

from app import db

# Float тооны харьцуулалтын хязгаар (epsilon)
FLOAT_EPSILON = 1e-9


class HashableMixin:
    """
    ISO 17025 audit log integrity mixin.

    Аудит бүртгэлүүдийн бүрэн бүтэн байдлыг SHA-256 hash-аар хангана.
    Бүртгэл өөрчлөгдсөн эсэхийг шалгах боломжтой.
    """

    def _get_hash_data(self) -> str:
        """Override: Return pipe-separated string of fields to hash."""
        raise NotImplementedError("Subclass must implement _get_hash_data()")

    def compute_hash(self) -> str:
        """Compute SHA-256 hash of the record data."""
        import hashlib
        return hashlib.sha256(self._get_hash_data().encode('utf-8')).hexdigest()

    def verify_hash(self) -> bool:
        """Verify hash integrity. Returns True if hash is valid or not set."""
        if not self.data_hash:
            return True
        return self.data_hash == self.compute_hash()
