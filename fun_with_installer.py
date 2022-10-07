import PyInstaller.__main__

PyInstaller.__main__.run([
    'run_monatsbericht_gui.py',
    '--noconfirm',
    # '--add-data=im_flieger;im_flieger',
    # '--add-data=senegal.txt;.',
    '--windowed'
    
])
