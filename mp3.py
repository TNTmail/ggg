

import qrcode


url = input("Enter the URL for the QR code: ").strip()
file_path = r"C:\Users\Bruger\Desktop\output_qr_code.png"


qr = qrcode.QRCode()
qr.add_data(url)

img = qr.make_image()
img.save(file_path)

print(f"QR code saved to {file_path}")
