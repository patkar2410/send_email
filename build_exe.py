import PyInstaller.__main__
import shutil
import os
import sys

def build():
    print("Building executable...")
    
    # PyInstaller arguments
    args = [
        'main.py',
        '--name=BatchEmailSender',
        '--windowed', # GUI mode
        '--clean',
        '--onefile',
    ]
    
    # Check for icon
    icon_file = None
    if sys.platform == 'darwin':
        if os.path.exists('app_icon.icns'):
            icon_file = 'app_icon.icns'
    
    # Fallback or Windows/Linux
    if not icon_file and os.path.exists('app_icon.ico'):
        icon_file = 'app_icon.ico'
        
    if icon_file:
        print(f"Using icon: {icon_file}")
        args.append(f'--icon={icon_file}')
    else:
        print("No 'app_icon.icns' or 'app_icon.ico' found. Using default icon.")
    
    PyInstaller.__main__.run(args)
    
    print("Build finished. Checking for output...")
    
    # Copy config.ini to dist
    # On macOS, --onefile --windowed creates a .app
    # On Windows/Linux, it creates an executable file.
    
    dist_dir = 'dist'
    
    if os.path.exists(dist_dir):
        print(f"Copying default config.ini to {dist_dir}...")
        try:
            shutil.copy('config.ini', dist_dir)
            print("Successfully copied config.ini.")
        except Exception as e:
            print(f"Failed to copy config.ini: {e}")
            
    print("Done. Check the 'dist' folder.")

if __name__ == '__main__':
    build()
