"""
Script to copy Paper Dashboard assets to GradeBench static directory.
"""

import os
import shutil
import glob

def ensure_dir(directory):
    """Ensure the directory exists"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def copy_assets():
    """Copy all necessary assets from Paper Dashboard to GradeBench static directory"""
    # Source and destination paths
    paper_dashboard_dir = r"E:\paper-dashboard"
    gradebench_static_dir = r"E:\GradeBench\static"
    
    # Ensure destination directories exist
    for subdir in ["css", "js", "img", "fonts"]:
        ensure_dir(os.path.join(gradebench_static_dir, subdir))
    
    # Copy CSS files
    css_src = os.path.join(paper_dashboard_dir, "assets", "css")
    css_dest = os.path.join(gradebench_static_dir, "css")
    for css_file in ["bootstrap.min.css", "paper-dashboard.css", "paper-dashboard.min.css"]:
        shutil.copy2(os.path.join(css_src, css_file), os.path.join(css_dest, css_file))
    print(f"Copied CSS files to {css_dest}")
    
    # Copy JS files - core
    js_core_src = os.path.join(paper_dashboard_dir, "assets", "js", "core")
    js_core_dest = os.path.join(gradebench_static_dir, "js", "core")
    ensure_dir(js_core_dest)
    for js_file in ["jquery.min.js", "popper.min.js", "bootstrap.min.js"]:
        shutil.copy2(os.path.join(js_core_src, js_file), os.path.join(js_core_dest, js_file))
    print(f"Copied JS core files to {js_core_dest}")
    
    # Copy JS plugin files
    js_plugins_src = os.path.join(paper_dashboard_dir, "assets", "js", "plugins")
    js_plugins_dest = os.path.join(gradebench_static_dir, "js", "plugins")
    ensure_dir(js_plugins_dest)
    for js_file in ["perfect-scrollbar.jquery.min.js", "chartjs.min.js", "bootstrap-notify.js"]:
        plugin_file = os.path.join(js_plugins_src, js_file)
        if os.path.exists(plugin_file):
            shutil.copy2(plugin_file, os.path.join(js_plugins_dest, js_file))
    print(f"Copied JS plugin files to {js_plugins_dest}")
    
    # Copy main JS file
    js_src = os.path.join(paper_dashboard_dir, "assets", "js")
    js_dest = os.path.join(gradebench_static_dir, "js")
    for js_file in ["paper-dashboard.min.js", "paper-dashboard.js"]:
        main_js_file = os.path.join(js_src, js_file)
        if os.path.exists(main_js_file):
            shutil.copy2(main_js_file, os.path.join(js_dest, js_file))
    print(f"Copied main JS files to {js_dest}")
    
    # Copy images
    img_src = os.path.join(paper_dashboard_dir, "assets", "img")
    img_dest = os.path.join(gradebench_static_dir, "img")
    
    # Copy logo and favicon
    for img_file in ["apple-icon.png", "favicon.png", "logo-small.png"]:
        src_file = os.path.join(img_src, img_file)
        if os.path.exists(src_file):
            shutil.copy2(src_file, os.path.join(img_dest, img_file))
    
    # Copy default avatar
    faces_dir = os.path.join(img_src, "faces")
    if os.path.exists(faces_dir):
        for img_file in glob.glob(os.path.join(faces_dir, "*.jpg")):
            avatar_dir = os.path.join(img_dest, "faces")
            ensure_dir(avatar_dir)
            shutil.copy2(img_file, os.path.join(avatar_dir, os.path.basename(img_file)))
    
    # Copy background images
    bg_dir = os.path.join(img_dest, "bg")
    ensure_dir(bg_dir)
    for img_file in glob.glob(os.path.join(img_src, "*.jpg")):
        shutil.copy2(img_file, os.path.join(bg_dir, os.path.basename(img_file)))
    
    print(f"Copied image files to {img_dest}")
    
    # Create default avatar if it doesn't exist
    default_avatar = os.path.join(img_dest, "default-avatar.png")
    if not os.path.exists(default_avatar):
        avatar_found = False
        if os.path.exists(os.path.join(img_dest, "faces")):
            for avatar in glob.glob(os.path.join(img_dest, "faces", "*.jpg")):
                shutil.copy2(avatar, default_avatar)
                print(f"Created default avatar from {os.path.basename(avatar)}")
                avatar_found = True
                break
        
        if not avatar_found:
            print("No avatar images found, please add a default-avatar.png file manually")
    
    print("Asset copy completed successfully!")

if __name__ == "__main__":
    copy_assets()
