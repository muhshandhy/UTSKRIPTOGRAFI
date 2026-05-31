"""
Script pengujian otomatis untuk memverifikasi enkripsi dan dekripsi
"""

import os
import sys
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256

# Konfigurasi
KEY_SIZE = 32
BLOCK_SIZE = 16
SALT_SIZE = 16
PBKDF2_ITERATIONS = 100000

def derive_key_from_password(password, salt):
    """Turunkan key dari password menggunakan PBKDF2"""
    password_bytes = password.encode('utf-8')
    key = PBKDF2(
        password_bytes,
        salt,
        KEY_SIZE,
        count=PBKDF2_ITERATIONS,
        hmac_hash_module=SHA256
    )
    return key

def test_encryption_decryption():
    """Test enkripsi dan dekripsi"""
    print("\n" + "="*60)
    print("  TEST OTOMATIS ENKRIPSI DAN DEKRIPSI AES-256 CBC")
    print("="*60)
    
    # Data test
    original_text = b"AES (Advanced Encryption Standard) adalah algoritma kriptografi simetris yang digunakan untuk menjaga kerahasiaan data."
    password = "TestPassword123"
    
    print(f"\n1. DATA ORIGINAL")
    print(f"   Text: {original_text.decode('utf-8')}")
    print(f"   Size: {len(original_text)} bytes")
    
    # ===== ENKRIPSI =====
    print(f"\n2. PROSES ENKRIPSI")
    
    # Buat salt dan key
    salt = get_random_bytes(SALT_SIZE)
    key = derive_key_from_password(password, salt)
    print(f"   ✓ Salt dibuat: {salt.hex()[:32]}...")
    print(f"   ✓ Key diturunkan dari password")
    
    # Buat cipher dan IV
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    print(f"   ✓ IV dibuat: {iv.hex()[:32]}...")
    
    # Padding
    padding_length = BLOCK_SIZE - (len(original_text) % BLOCK_SIZE)
    plaintext_padded = original_text + bytes([padding_length] * padding_length)
    
    # Enkripsi
    ciphertext = cipher.encrypt(plaintext_padded)
    print(f"   ✓ File dienkripsi")
    print(f"   ✓ Ciphertext size: {len(ciphertext)} bytes")
    
    encrypted_data = salt + iv + ciphertext
    print(f"   ✓ Total encrypted file: {len(encrypted_data)} bytes")
    print(f"   ✓ Format: [Salt 16] + [IV 16] + [Ciphertext {len(ciphertext)}]")
    
    # ===== DEKRIPSI =====
    print(f"\n3. PROSES DEKRIPSI")
    
    # Ekstrak salt, IV, ciphertext
    salt_extracted = encrypted_data[:SALT_SIZE]
    iv_extracted = encrypted_data[SALT_SIZE:SALT_SIZE + BLOCK_SIZE]
    ciphertext_extracted = encrypted_data[SALT_SIZE + BLOCK_SIZE:]
    
    print(f"   ✓ Salt diekstrak: {salt_extracted.hex()[:32]}...")
    print(f"   ✓ IV diekstrak: {iv_extracted.hex()[:32]}...")
    print(f"   ✓ Ciphertext diekstrak: {len(ciphertext_extracted)} bytes")
    
    # Turunkan key dari password dengan salt yang sama
    key_recovered = derive_key_from_password(password, salt_extracted)
    print(f"   ✓ Key diturunkan ulang dari password")
    
    # Dekripsi
    cipher_decrypt = AES.new(key_recovered, AES.MODE_CBC, iv_extracted)
    plaintext_padded_recovered = cipher_decrypt.decrypt(ciphertext_extracted)
    
    # Hapus padding
    padding_length_recovered = plaintext_padded_recovered[-1]
    plaintext_recovered = plaintext_padded_recovered[:-padding_length_recovered]
    
    print(f"   ✓ File didekripsi")
    print(f"   ✓ Plaintext size: {len(plaintext_recovered)} bytes")
    
    # ===== VERIFIKASI =====
    print(f"\n4. VERIFIKASI HASIL")
    
    if plaintext_recovered == original_text:
        print(f"   ✓ BERHASIL! Plaintext hasil dekripsi identik dengan original")
        print(f"   ✓ Text: {plaintext_recovered.decode('utf-8')}")
        print(f"\n{'='*60}")
        print("  ✓ ENKRIPSI DAN DEKRIPSI BERHASIL 100%")
        print(f"{'='*60}\n")
        return True
    else:
        print(f"   ✗ GAGAL! Plaintext tidak cocok")
        print(f"   Original: {original_text}")
        print(f"   Recovered: {plaintext_recovered}")
        return False

def test_wrong_password():
    """Test dengan password salah"""
    print("\n" + "="*60)
    print("  TEST DENGAN PASSWORD SALAH")
    print("="*60)
    
    original_text = b"Test data untuk enkripsi"
    password = "CorrectPassword123"
    wrong_password = "WrongPassword999"
    
    print(f"\n1. ENKRIPSI dengan password: {password}")
    
    # Enkripsi
    salt = get_random_bytes(SALT_SIZE)
    key = derive_key_from_password(password, salt)
    cipher = AES.new(key, AES.MODE_CBC)
    iv = cipher.iv
    
    padding_length = BLOCK_SIZE - (len(original_text) % BLOCK_SIZE)
    plaintext_padded = original_text + bytes([padding_length] * padding_length)
    ciphertext = cipher.encrypt(plaintext_padded)
    encrypted_data = salt + iv + ciphertext
    
    print(f"   ✓ File berhasil dienkripsi")
    
    # Dekripsi dengan password salah
    print(f"\n2. DEKRIPSI dengan password SALAH: {wrong_password}")
    
    salt_extracted = encrypted_data[:SALT_SIZE]
    iv_extracted = encrypted_data[SALT_SIZE:SALT_SIZE + BLOCK_SIZE]
    ciphertext_extracted = encrypted_data[SALT_SIZE + BLOCK_SIZE:]
    
    wrong_key = derive_key_from_password(wrong_password, salt_extracted)
    cipher_decrypt = AES.new(wrong_key, AES.MODE_CBC, iv_extracted)
    plaintext_wrong = cipher_decrypt.decrypt(ciphertext_extracted)
    
    print(f"   ✓ Dekripsi dilakukan (tanpa error)")
    print(f"   ✓ Hasil dekripsi (CORRUPTED): {plaintext_wrong[:30]}...")
    
    # Coba unpadding
    try:
        padding_length = plaintext_wrong[-1]
        if padding_length > BLOCK_SIZE or padding_length == 0:
            print(f"\n   ✓ DETEKSI! Padding invalid → Password SALAH")
            print(f"{'='*60}")
            print("  ✓ PROGRAM DENGAN BENAR MENDETEKSI PASSWORD SALAH")
            print(f"{'='*60}\n")
            return True
    except:
        pass
    
    return False

if __name__ == "__main__":
    result1 = test_encryption_decryption()
    result2 = test_wrong_password()
    
    if result1 and result2:
        print("\n" + "="*60)
        print("  ✓✓✓ SEMUA TEST BERHASIL ✓✓✓")
        print("  Program siap digunakan untuk tugas Kriptografi!")
        print("="*60 + "\n")
        sys.exit(0)
    else:
        print("\n✗ Ada test yang gagal")
        sys.exit(1)
