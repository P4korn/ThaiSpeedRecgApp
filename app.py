import streamlit as st
import speech_recognition as sr
from pydub import AudioSegment
import os
import time

# Specify the directory in the project folder to save audio files and transcripts
project_folder = "transcripts"  # Create a folder named "transcripts" in your project directory
os.makedirs(project_folder, exist_ok=True)

# Function to convert audio to WAV format
def convert_to_wav(audio_file, output_file):
    audio = AudioSegment.from_file(audio_file)
    audio.export(output_file, format="wav")

# Function to try transcribing the entire audio first
def transcribe_whole_audio(audio_file):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(audio_file) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language="th-TH")
        return text, None  # If successful, return the transcription and no error
    except sr.RequestError as e:
        return None, f"Request error: {e}"
    except sr.UnknownValueError:
        return None, "Could not understand audio"

# Function to transcribe audio in chunks if full transcription fails
def transcribe_audio_in_chunks(audio_file, file_name_base):
    recognizer = sr.Recognizer()
    audio = AudioSegment.from_file(audio_file, format="wav")
    
    chunk_length = 30 * 1000  # 30 seconds
    num_chunks = len(audio) // chunk_length + (len(audio) % chunk_length > 0)
    recognized_text = []

    for i in range(num_chunks):
        start_time = i * chunk_length
        end_time = start_time + chunk_length
        chunk = audio[start_time:end_time]

        chunk_file_name = f"{project_folder}/{file_name_base}_chunk_{i}.wav"
        chunk.export(chunk_file_name, format="wav")

        with sr.AudioFile(chunk_file_name) as source:
            audio_data = recognizer.record(source)
            try:
                text = recognizer.recognize_google(audio_data, language="th-TH")
                recognized_text.append(text)
            except sr.UnknownValueError:
                recognized_text.append("Could not understand audio")
            except sr.RequestError as e:
                recognized_text.append(f"Could not request results; {e}")

    full_text = "\n".join(recognized_text)
    return full_text

# Streamlit app
st.title("Audio Transcription App")
st.write("Upload an audio file (WAV or M4A format) to transcribe.")

# File uploader
uploaded_file = st.file_uploader("Choose an audio file", type=["wav", "m4a"])

if uploaded_file is not None:
    # Extract the original file name and timestamp to generate a unique base name
    original_file_name = os.path.splitext(uploaded_file.name)[0]
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    file_name_base = f"{original_file_name}_{timestamp}"
    
    wav_file_path = f"{project_folder}/{file_name_base}.wav"
    
    # Check if the uploaded file is not a WAV file
    if uploaded_file.type != "audio/wav":
        st.write("Converting audio to WAV format...")
        convert_to_wav(uploaded_file, wav_file_path)  # Convert to WAV
    else:
        with open(wav_file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

    st.audio(wav_file_path)  # Play the uploaded audio file

    if st.button("Transcribe"):
        with st.spinner("Transcribing..."):
            # First try to transcribe the whole audio
            transcription, error_message = transcribe_whole_audio(wav_file_path)

            if transcription is None:
                # If whole transcription fails, show the error and fallback to chunking
                # st.write(f"Whole audio transcription failed: {error_message}")
                # st.write("Falling back to chunk-based transcription...")
                
                # Transcribe the audio in chunks
                transcription = transcribe_audio_in_chunks(wav_file_path, file_name_base)

        # Show the transcription result
        st.subheader("Transcription Result:")
        st.write(transcription)

        # Export the recognized text to a text file in the project folder
        text_file_path = f"{project_folder}/text/{file_name_base}_recognized_text.txt"
        with open(text_file_path, "w", encoding="utf-8") as f:
            f.write(transcription)

        # Provide a download link for the text file
        st.download_button(
            label="Download Transcription",
            data=open(text_file_path, "r", encoding="utf-8").read(),
            file_name=f"{file_name_base}_recognized_text.txt",
            mime="text/plain"
        )
