import os

import streamlit as st
from openai import OpenAI
import openai
from dotenv import load_dotenv
from io import BytesIO
from langchain.prompts import (ChatPromptTemplate, HumanMessagePromptTemplate, SystemMessagePromptTemplate)
from langchain_openai import ChatOpenAI


load_dotenv()
API_KEY = os.getenv('OPENAI_API_KEY')

if not API_KEY:
    st.error("OPENAI_API_KEY environment variable not found.")
    st.stop()

client = OpenAI(api_key=API_KEY)

# GA4の測定ID
ga_measurement_id = 'G-WH6S6PRFNC'
ga_script = f"""
<script async src="https://www.googletagmanager.com/gtag/js?id={ga_measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{ga_measurement_id}');
</script>
"""
st.markdown(ga_script, unsafe_allow_html=True)

st.title("声ネタ日本語翻訳BOT")
st.subheader("何言ってるか分からない声ネタを日本語に翻訳！:sparkles:")
st.caption(":blue[※アップロードされたファイルが活用されることはありません。]")

uploaded_file = st.file_uploader(
    "ファイルをアップロードしてください。",
    type=['mp3','wav'],
    key='audio_upload'
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if uploaded_file is not None:
    try:
        with st.spinner("解析中..."):
            bytes_data = BytesIO(uploaded_file.getvalue())
            bytes_data.name = "file.mp3" # https://community.openai.com/t/whisper-error-400-unrecognized-file-format/563474/2
            try:
                transcript = client.audio.transcriptions.create(
                    model="whisper-1",
                    file=bytes_data
                )
            
            except openai.APIStatusError as e:
                st.error(f"Transcription error: {e}")
                st.stop()
            
            if transcript.text:
                chat_prompt = ChatPromptTemplate.from_messages([
                    SystemMessagePromptTemplate.from_template("今から入力される歌詞を日本語に翻訳してください。返事を返す際は、翻訳後の歌詞だけ返してください。"),
                    HumanMessagePromptTemplate.from_template(f"{transcript.text}")
                    ])
                llm = ChatOpenAI(model="gpt-3.5-turbo", openai_api_key=API_KEY)
                messages = chat_prompt.format_prompt(option=transcript.text).to_messages()
                response = llm.invoke(
                    messages
                )
                st.audio(bytes_data)
                with st.chat_message("assistant"):
                        result = f"原文: {transcript.text}  \n\n翻訳: {response.content}"
                        st.markdown(result)                
            else:
                st.error("歌詞が読み取れませんでした。ボーカルのない音源かもしれません。")

    except Exception as e:
        st.error(f"予期しないエラーが発生しました: {e}")
        
