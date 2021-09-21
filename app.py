import os
import base64
from flask import Flask, jsonify, request

# Create a app
app = Flask(__name__)

# Simple content of the app
@app.route("/")
def hello_world():
    return "<p>Hola mundo!</p>"

# Read files from testers
@app.route('/', methods=['POST'])
def read_base64_files():
    # Tecnology
    from pydub import AudioSegment
    from pydub.effects import normalize
    import speech_recognition as sr
    from fuzzywuzzy import fuzz
    import numpy as np
    import pandas as pd

    # Read information
    print('Its reading request inputs')
    request_data = request.get_json()
    pronunciationBase64 = request_data['Pronunciation']
    pronunciationFormat = request_data['PronunciationFormat']
    pronunciationNativeBase64 = request_data['PronunciationNative']
    pronunciationNativeFormat = request_data['PronunciationNativeFormat']
    phrase = request_data['Phrase'].lower()
    puntuacions_marks = ['?', '¿', '.', ',', ':', ';']
    for puntuacion_mark in puntuacions_marks:
        phrase = phrase.replace(puntuacion_mark, '')

    # Create audios into a RawAudiosAndTxtFile folder and put in the same folder the phrase in txt file format
    print('Its transforming base64 inputs to audio files')
    os.system('mkdir RawAudiosAndTxtFile')
    
    # Pronunciation Audio
    pathnamepronunciationAudio = './RawAudiosAndTxtFile/pronunciation.' + pronunciationFormat
    pronunciationAudio = open(pathnamepronunciationAudio, "wb")
    decode_string = base64.b64decode(pronunciationBase64)
    pronunciationAudio.write(decode_string)

    # Pronunciation Native Audio
    pathnamepronunciationNativeAudio = './RawAudiosAndTxtFile/pronunciationNative.' + pronunciationNativeFormat
    pronunciationNativeAudio = open(pathnamepronunciationNativeAudio, "wb")
    decode_string = base64.b64decode(pronunciationNativeBase64)
    pronunciationNativeAudio.write(decode_string)

    # write phrase.txt file
    text_file = open('./RawAudiosAndTxtFile/pronunciationNative.txt', "wt")
    n = text_file.write(phrase)
    text_file.close()

    # Generate adecuate audio files
    print('Its generating adecuate audio files')
    os.system('mkdir audios')
    # Iterate over multiples audios files
    for audiofile in os.scandir('./RawAudiosAndTxtFile'):

        # Work only with audios files. Add other possible formats to conditional if it is necesary
        if audiofile.path.endswith('.txt') != True:
        
            # name of the file 
            nameinput = os.path.splitext(os.path.basename(audiofile.path))[0]

            # folder with adecuate audio files
            pathoutput = './audios' + '/' + nameinput + '.wav'

            # Read raw audio file
            audio = AudioSegment.from_file(audiofile.path)

            # Normalize
            audio = normalize(audio)

            # Set adecuate features
            audio = audio.set_channels(1)
            audio = audio.set_frame_rate(16000)
            audio = audio.set_sample_width(2)

            # Write in .wav format
            audio.export(pathoutput, format = 'wav')
    
    os.system('cp -i ./RawAudiosAndTxtFile/pronunciationNative.txt ./audios')

    # Speech to text with SpeechRecognition Package
    # Create recognizer instance
    print('Its doing speech recognition process')
    r = sr.Recognizer()

    # Capture audio data
    # pronunciation audio
    path_audio_pronunciation = './audios/pronunciation.wav'
    audiofilepronunciation = sr.AudioFile(path_audio_pronunciation)
    with audiofilepronunciation as source:
        audiopronunciation = r.record(source)

    # Speech to text
    try:
        pronunciation = r.recognize_google(audiopronunciation, language='es-CO').lower()
    except sr.UnknownValueError:
        print("Google Speech Recognition could not understand audio")
    except sr.RequestError as e:
        print("Could not request results from Google Speech Recognition service; {0}".format(e))

    # write nameaudio.txt file
    text_file = open('./audios/pronunciation.txt', "wt")
    n = text_file.write(pronunciation)
    text_file.close()

    # To excecute forced alignment process until to produce the whished files
    print('Its doing forced alignment process')
    namepronunciationfile = 'pronunciation-palign.csv'
    namepronunciationNativefile = 'pronunciationNative-palign.csv'
    filesinaudio = os.listdir('./audios')
    number_of_times = 0

    while (namepronunciationfile not in filesinaudio) and (namepronunciationNativefile not in filesinaudio):
        # Forced alignment
        # annotation_fillipus = './SPPAS-3/sppas/bin/fillipus.py -I ./audios -e .csv'
        # os.system(annotation_fillipus)
        # print(annotation_fillipus)
        # # annotation_textnormalization = './SPPAS-3/sppas/bin/normalize.py -r .SPPAS-3/resources/vocab/spa.vocab -I ./audios -l spa -e .csv'
        # annotation_textnormalization = './SPPAS-3/sppas/bin/normalize.py -I ./audios -l spa -e .csv'
        # os.system(annotation_textnormalization)
        # print(annotation_textnormalization)
        # annotation_phonetization = './SPPAS-3/sppas/bin/phonetize.py -I ./audios -l spa -e .csv'
        # os.system(annotation_phonetization)
        # print(annotation_phonetization)
        # annotation_alignment = './SPPAS-3/sppas/bin/alignment.py -I ./audios -l spa -e .csv'
        # os.system(annotation_alignment)
        # print(annotation_alignment)
        annotation_cli = './SPPAS-3/sppas/bin/annotation.py -I ./audios -l spa -e .csv --fillipus --textnorm --phonetize --alignment'
        os.system(annotation_cli)
        print(annotation_cli)
        filesinaudio = os.listdir('./audios')
        number_of_times += 1

    print('Number of times that forced alignment process was excecuted: {}'.format(number_of_times))

    # Calculate Completeness Score
    print('Its calculating scores')
    # completeness score
    completeness_score = int(round(fuzz.QRatio(pronunciation, phrase),0))

    # Calculate Accuaracy Score
    # read pronunciation palign file
    path_pronunciation_palign = 'audios/pronunciation-palign.csv'
    df_pronunciation_palign = pd.read_csv(path_pronunciation_palign, names=['typealign', 'start', 'end', 'phonem'])
    df_pronunciation_palign['duration'] = df_pronunciation_palign.end - df_pronunciation_palign.start

    # read pronunciation native palign file
    path_native_palign = 'audios/pronunciationNative-palign.csv'
    df_native_palign = pd.read_csv(path_native_palign, names=['typealign', 'start', 'end', 'phonem'])
    df_native_palign['duration'] = df_native_palign.end - df_native_palign.start

    # read spa_dict file
    path_spa_dict = 'SPPAS-3/resources/dict/spa.dict'
    with open(path_spa_dict, 'r', encoding='utf-8') as datafile:
            raw_lines = datafile.readlines()

    # create dict with spa_dict information. Word as key and Phonems as values
    words_phonems = [line.split('\n')[0].split(' [] ') for line in raw_lines]
    spa_dict = {}
    for word_phonem in words_phonems:
        spa_dict[word_phonem[0]] = word_phonem[1].replace(' ', '-')

    # phrase in phonems
    phrase_phonem_list = [spa_dict[word] for word in phrase.split(' ')]
    phrase_phonem_str = ' '.join(phrase_phonem_list)

    # pronunciation in phonems
    pronunciation_phonem_list = df_pronunciation_palign[(df_pronunciation_palign.typealign == 'PronTokAlign')][1:-1].phonem.values.tolist()
    pronunciation_phonem_list = [element.split('=')[0] for element in pronunciation_phonem_list]
    pronunciation_phonem_str = ' '.join(pronunciation_phonem_list)

    # accuracy score
    accuracy_score = int(round(fuzz.QRatio(pronunciation_phonem_str, phrase_phonem_str),0))

    # Calculate Fluency Score

    # Pronunciation Phrase duration
    print('Its printing df_pronunciation_palign')
    print(df_pronunciation_palign)
    pronunciation_phrase_duration = round(df_pronunciation_palign[df_pronunciation_palign.typealign == 'PhonAlign'][1:-1].end.values[-1] - df_pronunciation_palign[df_pronunciation_palign.typealign == 'PhonAlign'][1:-1].start.values[0], 1)

    # Pronunciation tokens duration
    pronunciation_tokens_duration = df_pronunciation_palign[df_pronunciation_palign.typealign == 'TokensAlign'][1:-1].duration.values
    pronunciation_tokens_duration = [round(score, 1) for score in pronunciation_tokens_duration]

    # Pronunciation phonems duration
    pronunciation_phonem_duration = df_pronunciation_palign[df_pronunciation_palign.typealign == 'PhonAlign'][1:-1].end.values - df_pronunciation_palign[df_pronunciation_palign.typealign == 'PhonAlign'][1:-1].start.values
    pronunciation_phonem_duration = [round(score, 1) for score in pronunciation_phonem_duration]

    # Native Phrase duration
    native_phrase_duration = round(df_native_palign[df_native_palign.typealign == 'PhonAlign'][1:-1].end.values[-1] - df_native_palign[df_native_palign.typealign == 'PhonAlign'][1:-1].start.values[0], 1)

    # Native tokens duration
    native_tokens_duration = df_native_palign[df_native_palign.typealign == 'TokensAlign'][1:-1].duration.values
    native_tokens_duration = [round(score, 1) for score in native_tokens_duration]

    # Native phonems duration
    native_phonem_duration = df_native_palign[df_native_palign.typealign == 'PhonAlign'][1:-1].end.values - df_native_palign[df_native_palign.typealign == 'PhonAlign'][1:-1].start.values
    native_phonem_duration = [round(score, 1) for score in native_phonem_duration]

    # Fluency Score
    native_duration = [native_phrase_duration] + native_tokens_duration + native_phonem_duration
    long_native = len(native_duration)
    pronunciation_duration = [pronunciation_phrase_duration] + pronunciation_tokens_duration + pronunciation_phonem_duration
    pronunciation_duration = pronunciation_duration[:long_native]
    fluency_score = round((sum([en == ep for en, ep in zip(native_duration, pronunciation_duration)])/long_native)*100, 2)

    # Pronunciation Score
    pronunciation_score = round((((completeness_score/100)*0.3333) + ((accuracy_score/100)*0.3333) + ((fluency_score/100)*0.3334))*100, 2)

    # Write Pronunciations Scores
    pronunciations_scores = {'Completeness': completeness_score,
                            'Accuracy': accuracy_score,
                            'Fluency': fluency_score,
                            'Pronunciation': pronunciation_score}

    # Remove audios and RawAudiosAndTxtFile
    os.system  ('rm -r audios RawAudiosAndTxtFile')

    return jsonify(pronunciations_scores)





# @app.route('/store', methods=['POST'])
# def create_store():
#     request_data = request.get_json()
#     new_store = {
#         'name': request_data['name'],
#         'items': []
#     }
#     stores.append(new_store)
#     return jsonify(new_store)