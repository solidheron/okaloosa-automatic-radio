import pyaudio
import wave
import numpy as np
from datetime import datetime
import os
import pytz

# Audio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 46000
CHUNK = 1024
THRESHOLD = 500  # Adjust this value to set the audio detection threshold
SILENCE_LIMIT = 2  # Number of seconds of silence before stopping

# File settings
OUTPUT_DIRECTORY = r"D:\Police_audio_recordings"  # Specify your desired output directory here

def record_audio():
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)

    print("Listening for audio...")
    
    while True:
        data = stream.read(CHUNK)
        audio_data = np.frombuffer(data, dtype=np.int16)
        
        if np.abs(audio_data).mean() > THRESHOLD:
            print("Audio detected! Recording...")
            
            frames = []
            silence_counter = 0
            recording_start_time = datetime.now(pytz.timezone('US/Central'))
            
            while True:
                data = stream.read(CHUNK)
                frames.append(data)
                
                audio_data = np.frombuffer(data, dtype=np.int16)
                if np.abs(audio_data).mean() < THRESHOLD:
                    silence_counter += 1
                else:
                    silence_counter = 0
                
                if silence_counter > SILENCE_LIMIT * (RATE / CHUNK):
                    break
            
            # Generate filename with date and CST time stamp of when recording started
            timestamp = recording_start_time.strftime("%Y%m%d_%H%M%S")
            filename = f"recording_{timestamp}.wav"
            filepath = os.path.join(OUTPUT_DIRECTORY, filename)
            
            # Save the recorded audio
            wf = wave.open(filepath, 'wb')
            wf.setnchannels(CHANNELS)
            wf.setsampwidth(p.get_sample_size(FORMAT))
            wf.setframerate(RATE)
            wf.writeframes(b''.join(frames))
            wf.close()
            
            os.system('cls')
            print(f"Recording saved: {filepath}")
            print("Listening for audio...")

    stream.stop_stream()
    stream.close()
    p.terminate()

if __name__ == "__main__":
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIRECTORY, exist_ok=True)
    record_audio()