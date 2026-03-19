# Random Word Picker – Japanese Vocabulary Trainer

A simple, single-file **Python + Tkinter** desktop application for random Japanese word practice (mainly aimed at JLPT / Kanji / Katakana study).

Generates a sequence of random words according to your filters, shows big Japanese text, and gradually reveals reading (romaji) + meaning — perfect for quick review sessions, spaced repetition warm-up, or "guess before reveal" drills.

https://github.com/yourusername/random-word-picker  
*(replace with your actual repo link)*

## Features

- **Big centered Japanese text** (auto-resizing font to fit screen)
- **Reveal on demand** — meaning & romaji hidden until you want to see them
  - Hold **Alt** → temporary reveal
  - Press **Up Arrow** → toggle reveal / hide
  - "Reveal / Hide" button
- **Keyboard friendly**
  - **Enter** / **>** → next word
  - **Backspace** / **<** → previous word
  - **Up** → toggle reveal
- Filters / Settings:
  - Word types: noun (n), verb (v), adjective (adj), other/blank
  - Levels: N5–N1, H (hiragana-only), K (katakana)
  - Show/hide: romaji, English meaning, category, level
  - Number of words to generate per session
  - Custom font sizes for English & romaji
- Tracks how many times each word has been shown (saved in `word_counter.csv`)
- Remembers settings between runs (`settings.json`)
- Supports custom dictionaries (just replace or load new `dictionary.csv`)
- Sample dictionary included if file is missing

## Screenshots

<img width="891" height="689" alt="image" src="https://github.com/user-attachments/assets/45783a53-90bc-41d2-b15c-2a847a82223e" />

<img width="1920" height="1024" alt="image" src="https://github.com/user-attachments/assets/7ff5eac5-db8b-4fa8-b515-69943e97a27b" />

<!-- You can later do:
![Landing screen](screenshots/landing.png)
![Settings](screenshots/settings.png)
![Main view – hidden](screenshots/main-hidden.png)
![Main view – revealed](screenshots/main-revealed.png)
-->

## Requirements

- Python **3.8** or newer
- Tkinter (usually comes with Python on Windows & macOS; on Linux you may need `sudo apt install python3-tk`)

No external pip packages required.

## File Structure

```text
random_word_picker/
├── random_word_picker.py      ← main script (run this)
├── dictionary.csv             ← your word list (can be replaced)
├── word_counter.csv           ← automatically created/updated
├── rw_picker_settings.json    ← saved user settings
└── README.md
