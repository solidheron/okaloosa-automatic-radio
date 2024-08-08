Here's an updated and professional description for your GitHub repository, incorporating the additional details about `keywords.py`:

---

### Overview

This suite of Python scripts is designed to automate the recording, transcription, and analysis of police radio communications. The system is composed of several main components, each responsible for a specific task in the workflow. These components are designed to operate independently, allowing them to run concurrently for optimal performance.

### Components

1. **Recording Police Audio (`recording_police_audio.py`)**: 
   - This script captures audio from police radio transmissions using an auxiliary cord connected to a radio device.
   - The recorded audio is saved as `.wav` files in a designated directory.

2. **Transcription of Audio (`police_radio_transcription.py`)**:
   - Utilizes the `medium.en` model from OpenAI's Whisper to transcribe the audio files stored in the directory.
   - The transcriptions are timestamped and compiled into a CSV file for easy access and further processing.

3. **Keyword Flagging and Alert System (`Keyword_flaging_and_alert_push.py`)**:
   - Analyzes the transcriptions to flag keywords such as street names, business names, and crime-related terms.
   - The flagged keywords are organized into two separate files for detailed review and action.

4. **Keywords Storage (`keywords.py`)**:
   - This script contains the keywords used for flagging police codes and street names specific to Okaloosa County.
   - While the classification can apply to most English-speaking areas, street names and ten codes will need to be adjusted to fit different regions in the US.

### Usage

Each script is intended to be executed independently, allowing simultaneous operation. This setup ensures that audio recording, transcription, and keyword analysis can occur in parallel, enhancing the system's efficiency and responsiveness.

### Requirements

- Python 3.x
- OpenAI Whisper model
- Additional dependencies as specified in the `requirements.txt` file

### Installation

Clone the repository and install the necessary dependencies:

```bash
git clone https://github.com/solidheron/okaloosa-automatic-radio.git
cd okaloosa-automatic-radio
pip install -r requirements.txt
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

This description provides a clear and professional outline of the program's functionality and usage, making it suitable for a GitHub repository.
