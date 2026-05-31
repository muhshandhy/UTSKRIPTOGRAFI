import os
import sys
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
import getpass


# ====================================================================
# KONFIGURASI KONSTANTA
# ====================================================================

# Ukuran key untuk AES-256 (32 bytes = 256 bits)
KEY_SIZE = 32

# Ukuran block untuk AES (selalu 16 bytes = 128 bits)
BLOCK_SIZE = 16

# Ukuran salt untuk PBKDF2 (16 bytes)
SALT_SIZE = 16

# Jumlah iterasi untuk PBKDF2 (100000 iterasi)
PBKDF2_ITERATIONS = 100000

# Direktori untuk file
INPUT_DIR = "input"
ENCRYPTED_DIR = "encrypted"
DECRYPTED_DIR = "decrypted"

# File default
INPUT_FILE = os.path.join(INPUT_DIR, "data.txt")
ENCRYPTED_FILE = os.path.join(ENCRYPTED_DIR, "data.enc")
DECRYPTED_FILE = os.path.join(DECRYPTED_DIR, "hasil.txt")


# ====================================================================
# FUNGSI UTILITAS UNTUK MEMBUAT FOLDER
# ====================================================================

def create_directories():
    """
    Membuat folder-folder yang diperlukan jika belum ada.
    Folder: input/, encrypted/, decrypted/
    """
    directories = [INPUT_DIR, ENCRYPTED_DIR, DECRYPTED_DIR]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"✓ Folder '{directory}' berhasil dibuat.")


# ====================================================================
# FUNGSI DERIVASI KEY DARI PASSWORD
# ====================================================================

def derive_key_from_password(password, salt):
    """
    Mengkonversi password menjadi key 256-bit menggunakan PBKDF2.
    
    Parameter:
        password (str): Password yang dimasukkan pengguna
        salt (bytes): Salt untuk proses derivasi (16 bytes)
    
    Return:
        bytes: Key 256-bit (32 bytes) untuk AES-256
    
    Penjelasan:
        PBKDF2 (Password-Based Key Derivation Function 2) adalah fungsi
        yang mengkonversi password menjadi key kriptografi yang aman.
        Dengan 100000 iterasi, password lebih sulit untuk di-brute force.
    """
    # Konversi password ke bytes menggunakan UTF-8 encoding
    password_bytes = password.encode('utf-8')
    
    # Gunakan PBKDF2 dengan SHA256 untuk derivasi key
    key = PBKDF2(
        password_bytes,      # Password yang dimasukkan pengguna
        salt,                # Salt untuk randomisasi
        KEY_SIZE,            # Output key size (32 bytes untuk AES-256)
        count=PBKDF2_ITERATIONS,  # Iterasi (semakin banyak, semakin aman)
        hmac_hash_module=SHA256    # Hash function untuk PBKDF2
    )
    
    return key


# ====================================================================
# FUNGSI ENKRIPSI FILE
# ====================================================================

def encrypt_file():
    """
    Mengenkripsi file TXT menggunakan AES-256 CBC.
    
    Proses:
    1. Membaca file input/data.txt
    2. Meminta password dari pengguna
    3. Membuat salt dan IV secara acak
    4. Menurunkan key dari password menggunakan PBKDF2
    5. Mengenkripsi isi file menggunakan AES-256 CBC
    6. Menyimpan [salt + IV + ciphertext] ke encrypted/data.enc
    
    Return:
        bool: True jika enkripsi berhasil, False jika gagal
    """
    try:
        # Cek apakah file input ada
        if not os.path.exists(INPUT_FILE):
            print(f"✗ Error: File '{INPUT_FILE}' tidak ditemukan!")
            return False
        
        # Baca isi file yang akan dienkripsi
        print(f"\n Membaca file: {INPUT_FILE}")
        with open(INPUT_FILE, 'rb') as f:
            plaintext = f.read()
        
        print(f"   Ukuran file: {len(plaintext)} bytes")
        
        # Minta password dari pengguna (tidak ditampilkan saat diketik)
        password = getpass.getpass(" Masukkan password: ")
        password_confirm = getpass.getpass(" Konfirmasi password: ")
        
        # Cek apakah password cocok
        if password != password_confirm:
            print("✗ Error: Password tidak cocok!")
            return False
        
        # Cek panjang password
        if len(password) < 6:
            print("✗ Error: Password minimal 6 karakter!")
            return False
        
        # Buat salt secara acak (16 bytes)
        salt = get_random_bytes(SALT_SIZE)
        print(f"\n Salt berhasil dibuat (16 bytes)")
        
        # Turunkan key dari password menggunakan PBKDF2
        key = derive_key_from_password(password, salt)
        print(f" Key berhasil diturunkan dari password (32 bytes)")
        
        # Buat cipher AES dengan mode CBC
        cipher = AES.new(key, AES.MODE_CBC)
        
        # Dapatkan IV yang dibuat otomatis oleh cipher
        iv = cipher.iv
        print(f" IV berhasil dibuat (16 bytes)")
        
        # Padding plaintext ke kelipatan 16 bytes (PKCS7 padding)
        # Penjelasan: AES CBC hanya bisa mengenkripsi data dengan panjang
        # kelipatan 16 bytes, jadi kita perlu padding.
        padding_length = BLOCK_SIZE - (len(plaintext) % BLOCK_SIZE)
        plaintext_padded = plaintext + bytes([padding_length] * padding_length)
        
        # Enkripsi plaintext
        ciphertext = cipher.encrypt(plaintext_padded)
        print(f" File berhasil dienkripsi!")
        print(f"  Ukuran ciphertext: {len(ciphertext)} bytes")
        
        # Gabungkan salt + IV + ciphertext dan simpan ke file
        # Format: [salt(16) + IV(16) + ciphertext(n)]
        encrypted_data = salt + iv + ciphertext
        
        # Buat folder encrypted jika belum ada
        if not os.path.exists(ENCRYPTED_DIR):
            os.makedirs(ENCRYPTED_DIR)
        
        # Simpan file terenkripsi
        with open(ENCRYPTED_FILE, 'wb') as f:
            f.write(encrypted_data)
        
        print(f" File terenkripsi berhasil disimpan: {ENCRYPTED_FILE}")
        print(f"   Ukuran file terenkripsi: {len(encrypted_data)} bytes")
        print("\n Enkripsi berhasil!\n")
        
        return True
    
    except Exception as e:
        print(f"\n✗ Error saat enkripsi: {str(e)}\n")
        return False


# ====================================================================
# FUNGSI DEKRIPSI FILE
# ====================================================================

def decrypt_file():
    """
    Mendekripsi file yang sudah dienkripsi menggunakan AES-256 CBC.
    
    Proses:
    1. Membaca file encrypted/data.enc
    2. Ekstrak salt, IV, dan ciphertext dari file
    3. Meminta password dari pengguna
    4. Turunkan key dari password menggunakan PBKDF2 dan salt
    5. Dekripsi ciphertext menggunakan AES-256 CBC
    6. Hapus padding dan simpan plaintext ke decrypted/hasil.txt
    
    Return:
        bool: True jika dekripsi berhasil, False jika gagal
    """
    try:
        # Cek apakah file terenkripsi ada
        if not os.path.exists(ENCRYPTED_FILE):
            print(f"✗ Error: File '{ENCRYPTED_FILE}' tidak ditemukan!")
            return False
        
        # Baca file terenkripsi
        print(f"\n Membaca file: {ENCRYPTED_FILE}")
        with open(ENCRYPTED_FILE, 'rb') as f:
            encrypted_data = f.read()
        
        print(f"   Ukuran file: {len(encrypted_data)} bytes")
        
        # Validasi ukuran file
        if len(encrypted_data) < (SALT_SIZE + BLOCK_SIZE):
            print(" Error: File terenkripsi rusak atau tidak valid!")
            return False
        
        # Ekstrak salt, IV, dan ciphertext dari file
        salt = encrypted_data[:SALT_SIZE]                    # 16 bytes pertama
        iv = encrypted_data[SALT_SIZE:SALT_SIZE + BLOCK_SIZE]  # 16 bytes berikutnya
        ciphertext = encrypted_data[SALT_SIZE + BLOCK_SIZE:]  # Sisanya adalah ciphertext
        
        print(f" Salt berhasil diekstrak (16 bytes)")
        print(f" IV berhasil diekstrak (16 bytes)")
        print(f" Ciphertext berhasil diekstrak ({len(ciphertext)} bytes)")
        
        # Minta password dari pengguna
        password = getpass.getpass("\n Masukkan password untuk dekripsi: ")
        
        # Turunkan key dari password menggunakan PBKDF2 dan salt yang diekstrak
        key = derive_key_from_password(password, salt)
        print(f" Key berhasil diturunkan dari password")
        
        # Buat cipher AES dengan mode CBC menggunakan IV yang diekstrak
        cipher = AES.new(key, AES.MODE_CBC, iv)
        
        # Dekripsi ciphertext
        plaintext_padded = cipher.decrypt(ciphertext)
        
        # Hapus padding (PKCS7 unpadding)
        # Byte terakhir menunjukkan berapa bytes padding yang ditambahkan
        padding_length = plaintext_padded[-1]
        
        # Validasi padding
        if padding_length > BLOCK_SIZE or padding_length == 0:
            print(" Error: Password salah atau file rusak!")
            return False
        
        plaintext = plaintext_padded[:-padding_length]
        
        print(f" File berhasil didekripsi!")
        print(f"  Ukuran plaintext: {len(plaintext)} bytes")
        
        # Buat folder decrypted jika belum ada
        if not os.path.exists(DECRYPTED_DIR):
            os.makedirs(DECRYPTED_DIR)
        
        # Simpan plaintext ke file
        with open(DECRYPTED_FILE, 'wb') as f:
            f.write(plaintext)
        
        print(f" File terdekripsi berhasil disimpan: {DECRYPTED_FILE}")
        print("\n Dekripsi berhasil!\n")
        
        return True
    
    except Exception as e:
        print(f"\n✗ Error saat dekripsi: {str(e)}\n")
        return False


# ====================================================================
# FUNGSI MENU UTAMA
# ====================================================================

def main_menu():
    """
    Menampilkan menu utama dan menangani pilihan pengguna.
    
    Menu:
    1. Encrypt File - Mengenkripsi file TXT
    2. Decrypt File - Mendekripsi file terenkripsi
    3. Exit - Keluar dari program
    """
    while True:
        # Bersihkan layar (opsional, untuk tampilan yang lebih rapi)
        print("\n" + "="*50)
        print("       === AES FILE ENCRYPTION ===")
        print("="*50)
        print("1.  Encrypt File")
        print("2.  Decrypt File")
        print("3.  Exit")
        print("="*50)
        
        # Minta pilihan dari pengguna
        choice = input("Pilih menu (1-3): ").strip()
        
        # Proses pilihan
        if choice == '1':
            encrypt_file()
        
        elif choice == '2':
            decrypt_file()
        
        elif choice == '3':
            print("\n Terima kasih telah menggunakan AES Encryption!")
            print("   Program berakhir.\n")
            break
        
        else:
            print("\n✗ Pilihan tidak valid! Silakan masukkan 1, 2, atau 3.\n")


# ====================================================================
# FUNGSI UTAMA PROGRAM
# ====================================================================

def main():
    """
    Fungsi utama yang menjalankan program.
    """
    # Buat folder-folder yang diperlukan
    create_directories()
    
    # Tampilkan menu utama
    main_menu()


# ====================================================================
# ENTRY POINT PROGRAM
# ====================================================================

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n  Program dihentikan oleh pengguna (Ctrl+C)")
        sys.exit(0)
    except Exception as e:
        print(f"\n✗ Error yang tidak terduga: {str(e)}")
        sys.exit(1)
