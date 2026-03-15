
import os

file_path = r"c:\Users\deept\OneDrive\Desktop\medical_store_project_Backend\frontend\templates\layout.html"

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Find the last closing html tag
end_tag = "</html>"
index = content.rfind(end_tag)

if index != -1:
    # Keep content up to </html>
    new_content = content[:index + len(end_tag)]
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    print("Successfully truncated layout.html")
else:
    print("Could not find </html> tag")
