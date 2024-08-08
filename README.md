### Overview

This suite of Python scripts is designed to automate the recording, transcription, and analysis of police radio communications. The system is composed of several main components, each responsible for a specific task in the workflow. These components are designed to operate independently, allowing them to run concurrently for optimal performance.

### Components

1. **Recording Police Audio (`recording_police_audio.py`)**: 
   - Captures audio from police radio transmissions using an auxiliary cord connected to a radio device.
   - Saves the recorded audio as `.wav` files in a designated directory.

2. **Transcription of Audio (`police_radio_transcription.py`)**:
   - Utilizes the `medium.en` model from OpenAI's Whisper to transcribe the audio files stored in the directory.
   - Compiles the transcriptions into a CSV file with timestamps.

3. **Keyword Flagging and Alert System (`Keyword_flaging_and_alert_push.py`)**:
   - Analyzes the transcriptions to flag keywords such as street names, business names, and crime-related terms.
   - Organizes flagged keywords into two separate files for detailed review and action.

4. **Keywords Storage (`keywords.py`)**:
   - Contains the keywords used for flagging police codes and street names specific to Okaloosa County.
   - While the classification can apply to most English-speaking areas, street names and ten codes will need to be adjusted to fit different regions in the US.

### Installation

Clone the repository and install the necessary dependencies:

```bash
git clone https://github.com/solidheron/okaloosa-automatic-radio.git
cd okaloosa-automatic-radio
pip install openai-whisper pandas numpy scipy librosa soundfile tqdm
```

### Execution

Run each script in a separate terminal or process to enable concurrent functionality:

```bash
python recording_police_audio.py
python police_radio_transcription.py
python Keyword_flaging_and_alert_push.py
```

### Contributions

Contributions are welcome! Please fork the repository and submit a pull request with your improvements or bug fixes.

---

This format clearly outlines the required modules, making it easy for users to understand what they need to install before running the project.
