import streamlit as st
import speech_recognition as sr
from langchain.chat_models import ChatOpenAI
from langchain.chains import ConversationChain
from gtts import gTTS
import os
from aiortc.contrib.media import MediaRecorder
from streamlit_webrtc import webrtc_streamer, VideoProcessorBase, RTCConfiguration, WebRtcMode, ClientSettings
from pydub import AudioSegment
import time

openai_api_key = st.secrets["my_secret"]["OPENAI_API_KEY"]
recognized_text = ""
recorder = None

if openai_api_key:
    if "llm" not in st.session_state:
        st.session_state.llm = ConversationChain(llm=ChatOpenAI(api_key=openai_api_key))

    #chat = ChatOpenAI(api_key=openai_api_key)
    #llm = ConversationChain(llm=chat)
    
    def recorder_factory():
        global recorder
        if recorder is None:
            recorder = MediaRecorder("record.wav")
        return recorder

        
    def stop_recorder():
        recognizer = sr.Recognizer()
        #if "mensagens" not in st.session_state:
        #    st.session_state.mensagens = [
        #        {"role": 'system', "content": 'Você irá responder ao que o usuário falar.'}
        #    ]
        audio_file = "record.wav"
        with sr.AudioFile(audio_file) as source:
            with st.spinner('Transcrevendo o áudio...'):
                try:
                    audio = recognizer.record(source)
                    prompt = recognizer.recognize_google(audio, language='pt-BR')
                    return prompt
                except sr.UnknownValueError:
                    return "Desculpe, não entendi o áudio."

            

    # Função para interagir com o ChatGPT
    def chat_with_gpt(prompt):
        try:
            saida = st.session_state.llm.run(prompt)
            return saida
        except Exception as e:
            return f"Erro ao interagir com o modelo: {str(e)}"

    # Função para síntese de voz
    def text_to_speech(text):
        tts = gTTS(text=text, lang='pt-br')
        tts.save("response.mp3")
        os.system("mpg321 response.mp3")



    # Interface do Streamlit
    st.header("Chat por Voz")
    instrucoes = (
    "**Instruções:** Clique em START e fale alguma coisa, depois clique em STOP e em Enviar Áudio.<br>"
    "Para uma nova fala repita o processo.<br>"
    "Para limpar a conversar clique em Encerrar Conversa.<br>"
    "ATENÇÃO: Só comece a falar quando o microfone do navegador estiver ativado."
    )

    st.markdown(instrucoes, unsafe_allow_html=True)
    webrtc_streamer(
        key="sendonly-audio",
        mode=WebRtcMode.SENDONLY,
        in_recorder_factory=recorder_factory,
        client_settings=ClientSettings(
            rtc_configuration={
                "iceServers": [{"urls": ["stun:stun.l.google.com:19302"]}]
            },
            media_stream_constraints={
                "audio": True,
                "video": False,
            },
        ),
    )

    c0,_,c1 = st.columns(3)
    
    with c0:
        inicio = st.button("Enviar áudio")

    with c1:
        stop_button = st.button("Encerrar Conversa", key="encerrar_conversa")

    
    if "mensagens" not in st.session_state:
        st.session_state.mensagens = [{"role": 'system', "content": 'Você será um amigo para conversar qualquer coisa.'}] 


    if inicio:
        recognized_text = stop_recorder()
        input_text = recognized_text
        #escevendo o histórico anterior
        for mensagens in st.session_state.mensagens[1:]:
            with st.chat_message(mensagens["role"]):
                st.markdown(mensagens["content"])

        if input_text and "Desculpe, não entendi o áudio." not in input_text:
            st.session_state.mensagens.append({"role": 'user', "content": input_text})
            with st.chat_message("user"):
                st.markdown(input_text)
            response_text = chat_with_gpt(input_text)
            st.session_state.mensagens.append({"role": 'system', "content": response_text})
            with st.chat_message("system"):
                st.markdown(response_text)
            if "Erro ao interagir com o modelo" not in response_text:
                text_to_speech(response_text)
                st.audio("response.mp3")
        else:
            st.write("Não foi detectado texto na fala. Por favor, fale novamente.")

    if stop_button:
        st.session_state.mensagens = [{"role": 'system', "content": 'Você será um amigo para conversar qualquer coisa.'}]
        del st.session_state.llm             
    
else:
    st.warning("Por favor, informe a chave da API OpenAI.")
