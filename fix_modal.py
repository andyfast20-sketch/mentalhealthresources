import re

file_path = r'G:\mentalhealthresources-main\mentalhealthresources-main\templates\resources.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Pattern to match the modal-header content we want to remove
old_header = '''        <div class="modal-header">
            <div>
                <p class="eyebrow">Anxiety overview</p>
                <h3 id="anxietyVideoTitle">Anxiety symptoms explained</h3>
                <p class="body muted">Press play for a calm walkthrough without leaving the page.</p>
            </div>
            <button class="modal-close" type="button" aria-label="Close anxiety video" data-anxiety-video-close>&times;</button>
        </div>'''

new_header = '''        <div class="modal-header">
            <button class="modal-close" type="button" aria-label="Close anxiety video" data-anxiety-video-close>&times;</button>
        </div>'''

if old_header in content:
    content = content.replace(old_header, new_header)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Successfully removed the modal header text!')
else:
    print('Could not find the exact text. Checking content...')
    if 'Anxiety overview' in content:
        print('Found "Anxiety overview" in file')
        # Find and print the surrounding content
        idx = content.find('Anxiety overview')
        print('Context:', repr(content[idx-50:idx+200]))
