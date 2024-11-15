import qrcode

img = qrcode.make('NITRO')

print(type(img))
print(img.size)
# <class 'qrcode.image.pil.PilImage'>
# (290, 290)

img.save('QRCodes/qrcode_nitro.png')