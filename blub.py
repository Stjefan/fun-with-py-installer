import PyInstaller.__main__

PyInstaller.__main__.run([
    'my_script.py',
    '--noconfirm',
    '--add-data=im_flieger;im_flieger',
    '--add-data=senegal.txt;.',
    '--windowed'
    
])

