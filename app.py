from flask import Flask, request, jsonify, render_template, send_file, session
import speech_recognition as sr
from pydub import AudioSegment
import io
from gtts import gTTS
import google.generativeai as genai

app = Flask(__name__, template_folder='templates')
app.secret_key = 'your_secret_key'

# Configure Generative AI model
genai.configure(api_key='AIzaSyDNPWVzFfOXbn5XVyvGJu2tepZQMYKdcw8')
model = genai.GenerativeModel('gemini-1.5-flash')

def convert_to_wav(audio_file):
    audio = AudioSegment.from_file(audio_file)
    wav_io = io.BytesIO()
    audio.export(wav_io, format='wav')
    wav_io.seek(0)
    return wav_io

def convert_speech_to_text(audio_file):
    recognizer = sr.Recognizer()
    
    # Convert audio to WAV format
    audio_file = convert_to_wav(audio_file)
    
    with sr.AudioFile(audio_file) as source:
        audio = recognizer.record(source)
    try:
        text = recognizer.recognize_google(audio)
        return text
    except sr.UnknownValueError:
        return "Sorry, I could not understand the audio."
    except sr.RequestError:
        return "Could not request results; check your network connection."

def get_gemini_response(prompt, history):
    combined_prompt = "\n".join(history) + "\n" + prompt
    response = model.generate_content(combined_prompt)
    return response.text

def allowed_file(filename):
    return filename.lower().endswith(('.wav', '.flac', '.aiff'))

@app.route('/ask', methods=['POST'])
def ask():
    if 'audio' in request.files:
        file = request.files['audio']
        if file and allowed_file(file.filename):
            user_prompt = convert_speech_to_text(file)
        else:
            return jsonify({'response': 'Invalid file format', 'audio_url': '', 'history': []})
    else:
        user_prompt = request.form.get('prompt')
    
    if user_prompt:
        chat_history = session.get('chat_history', [])
        response_text = get_gemini_response(user_prompt, chat_history)
        chat_history.append(f"User: {user_prompt}")
        chat_history.append(f"Bot: {response_text}")
        session['chat_history'] = chat_history
        
        tts = gTTS(text=response_text, lang='en')
        audio_file = io.BytesIO()
        tts.write_to_fp(audio_file)
        audio_file.seek(0)
        
        return jsonify({
            'response': response_text,
            'audio_url': '/audio/response',
            'history': chat_history
        })

    return jsonify({
        'response': 'No prompt provided',
        'audio_url': '',
        'history': []
    })

@app.route('/audio/response')
def audio_response():
    # Generate sample response audio
    tts = gTTS(text='Sample response text', lang='en')
    audio_file = io.BytesIO()
    tts.write_to_fp(audio_file)
    audio_file.seek(0)
    return send_file(audio_file, mimetype='audio/mpeg')

@app.route('/')
def index():
    chat_history = session.get('chat_history', [])
    return render_template('index.html', chat_history=chat_history)

if __name__ == "__main__":
    app.run(debug=True)

