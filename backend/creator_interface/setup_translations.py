from pathlib import Path
import subprocess
import os

LOCALE_DIR = Path(__file__).parent / "locales"
LANGUAGES = ['en', 'es', 'ca', 'eu']

# Central storage of all translations
TRANSLATIONS = {
    'en': {
        "Creator Interface": "Creator Interface",
        "Welcome to the Creator Interface": "Welcome to the Creator Interface",
        "Settings": "Settings",
        "Dashboard": "Dashboard",
        "Profile": "Profile",
        "Logout": "Logout",
        "Language": "Language",
        "Theme": "Theme",
        "Dark": "Dark",
        "Light": "Light",
    },
    'es': {
        "Creator Interface": "Interfaz del Creador",
        "Welcome to the Creator Interface": "Bienvenido a la Interfaz del Creador",
        "Settings": "Configuración",
        "Dashboard": "Panel",
        "Profile": "Perfil",
        "Logout": "Cerrar Sesión",
        "Language": "Idioma",
        "Theme": "Tema",
        "Dark": "Oscuro",
        "Light": "Claro",
    },
    'ca': {
        "Creator Interface": "Interfície del Creador",
        "Welcome to the Creator Interface": "Benvingut a la Interfície del Creador",
        "Settings": "Configuració",
        "Dashboard": "Tauler",
        "Profile": "Perfil",
        "Logout": "Tancar Sessió",
        "Language": "Idioma",
        "Theme": "Tema",
        "Dark": "Fosc",
        "Light": "Clar",
    },
    'eu': {
        "Creator Interface": "Sortzailearen Interfazea",
        "Welcome to the Creator Interface": "Ongi etorri Sortzailearen Interfazera",
        "Settings": "Ezarpenak",
        "Dashboard": "Arbela",
        "Profile": "Profila",
        "Logout": "Saioa Itxi",
        "Language": "Hizkuntza",
        "Theme": "Gaia",
        "Dark": "Iluna",
        "Light": "Argia",
    }
}

def extract_messages():
    """
    Extract translatable strings from source files into a POT file.
    This creates/updates the messages.pot template file.
    """
    print("Extracting messages from source files...")
    
    # Ensure the locale directory exists
    LOCALE_DIR.mkdir(parents=True, exist_ok=True)
    
    # Build the xgettext command
    cmd = [
        'xgettext',
        '--from-code=UTF-8',
        '-o', str(LOCALE_DIR / 'messages.pot'),
        '--keyword=_',
        '--keyword=gettext',
        '--language=Python',
        '--language=Jinja2',
        '--add-comments=Translators:',
        '--sort-output',
        '--package-name=creator_interface',
        '--package-version=1.0',
        '--copyright-holder=Your Name',
        '--msgid-bugs-address=your@email.com',
    ]
    
    # Add all Python files
    python_files = list(Path(__file__).parent.rglob('*.py'))
    template_files = list(Path(__file__).parent.rglob('*.html'))
    
    # Add files to command
    cmd.extend(str(f) for f in python_files + template_files)
    
    # Run xgettext
    try:
        subprocess.run(cmd, check=True)
        print("Successfully extracted messages to messages.pot")
    except subprocess.CalledProcessError as e:
        print(f"Error extracting messages: {e}")
        raise

def update_po_files():
    """
    Update existing .po files with new messages from the template.
    Preserves existing translations.
    """
    print("Updating .po files...")
    pot_file = LOCALE_DIR / 'messages.pot'
    
    if not pot_file.exists():
        print("messages.pot not found. Running extract_messages first...")
        extract_messages()
    
    for lang in LANGUAGES:
        po_path = LOCALE_DIR / lang / 'LC_MESSAGES'
        po_file = po_path / 'messages.po'
        
        if po_file.exists():
            print(f"Updating existing translations for {lang}...")
            try:
                subprocess.run([
                    'msgmerge',
                    '--update',
                    '--backup=none',  # Don't create backup files
                    str(po_file),
                    str(pot_file)
                ], check=True)
            except subprocess.CalledProcessError as e:
                print(f"Error updating {lang} translations: {e}")
        else:
            print(f"Creating new translation file for {lang}...")
            po_path.mkdir(parents=True, exist_ok=True)
            generate_po_file(lang, po_file)

def generate_po_file(lang, po_file):
    """Generate a new .po file for the specified language"""
    content = f'''msgid ""
msgstr ""
"Project-Id-Version: creator_interface 1.0\\n"
"Report-Msgid-Bugs-To: your@email.com\\n"
"POT-Creation-Date: 2024-01-01 00:00+0000\\n"
"PO-Revision-Date: 2024-01-01 00:00+0000\\n"
"Last-Translator: Your Name <your@email.com>\\n"
"Language-Team: {lang}\\n"
"Language: {lang}\\n"
"MIME-Version: 1.0\\n"
"Content-Type: text/plain; charset=UTF-8\\n"
"Content-Transfer-Encoding: 8bit\\n"
\n'''
    
    # Add translations from TRANSLATIONS dictionary
    for msgid, msgstr in TRANSLATIONS[lang].items():
        content += f'''
msgid "{msgid}"
msgstr "{msgstr}"
'''
    
    # Write the file
    with open(po_file, 'w', encoding='utf-8') as f:
        f.write(content)

def compile_translations():
    """
    Compile .po files into .mo files that can be used by gettext.
    """
    print("Compiling translation files...")
    for lang in LANGUAGES:
        po_file = LOCALE_DIR / lang / 'LC_MESSAGES' / 'messages.po'
        mo_file = LOCALE_DIR / lang / 'LC_MESSAGES' / 'messages.mo'
        
        if po_file.exists():
            try:
                subprocess.run(['msgfmt', str(po_file), '-o', str(mo_file)], check=True)
                print(f"Successfully compiled translations for {lang}")
            except subprocess.CalledProcessError as e:
                print(f"Error compiling translations for {lang}: {e}")

def setup_translations():
    """
    Main function to set up or update all translations.
    """
    try:
        # Create necessary directories
        for lang in LANGUAGES:
            (LOCALE_DIR / lang / 'LC_MESSAGES').mkdir(parents=True, exist_ok=True)
        
        # Extract messages from source files
        extract_messages()
        
        # Update or create .po files
        update_po_files()
        
        # Compile translations
        compile_translations()
        
        print("Translation setup completed successfully!")
        
    except Exception as e:
        print(f"Error setting up translations: {e}")
        raise

def add_new_translation(msgid, translations):
    """
    Add a new translation to all language files.
    
    Args:
        msgid (str): The message ID (English text)
        translations (dict): Dictionary of translations for each language
    """
    # Update TRANSLATIONS dictionary
    for lang in LANGUAGES:
        if lang in translations:
            TRANSLATIONS[lang][msgid] = translations[lang]
        else:
            TRANSLATIONS[lang][msgid] = msgid if lang == 'en' else ''
    
    # Regenerate all translation files
    setup_translations()

if __name__ == "__main__":
    setup_translations() 