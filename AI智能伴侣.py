import streamlit as st
import os
from openai import OpenAI
import  datetime
import json
from openai.types.beta.realtime import session

st.set_page_config(
    page_title="AI智能伴侣",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={}
)
def save_session():
    if st.session_state.current_session:
        session_date={
            "nick_name":st.session_state.nick_name,
            "nature":st.session_state.nature,
            "current_session":st.session_state.current_session,
            "messages":st.session_state.messages
        }
        if not os.path.exists("sessions"):
            os.mkdir("sessions")
        with open(f"sessions/{st.session_state.current_session}.json","w",encoding="utf-8") as f:
            json.dump(session_date,f,ensure_ascii=False,indent=2)
def load_sessions():
    session_list=[]
    if os.path.exists("sessions"):
        file_list=os.listdir("sessions")
        for filename in file_list:
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list
def load_session(session_name):
    try:
         if os.path.exists(f"sessions/{session_name}.json"):
            with open(f"sessions/{session_name}.json","r",encoding="utf-8") as f:
                session_data=json.load(f)
                st.session_state.messages=session_data["messages"]
                st.session_state.nick_name=session_data["nick_name"]
                st.session_state.nature=session_data["nature"]
                st.session_state.current_session=session_name
    except Exception:
        st.error("加载会话失败")
def delete_session(session_name):
    try:
        if os.path.exists(f"sessions/{session_name}.json"):
            os.remove(f"sessions/{session_name}.json")
            if session_name==st.session_state.current_session:
                st.session_state.messages=[]
                st.session_state.current_session=generate_session_name()
    except Exception :
        st.error("删除对话失败")
st.title("AI智能伴侣")
system_prompt="""
你叫{0}。
你的性格是{1}。
"""
if "messages" not in st.session_state:
  st.session_state.messages= []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = "然后"
if "nature" not in st.session_state:
    st.session_state.nature = "温柔可爱姑娘"
if "current_session" not in st.session_state:
    now=datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    st.session_state.current_session =now
st.text(f"会话名称：{st.session_state.current_session}")
for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user").write(message["content"])
    else:
        st.chat_message("system").write(message["content"])
client = OpenAI(
    api_key=os.environ.get('DEEPSEEK_API_KEY'),
    base_url="https://api.deepseek.com")
with st.sidebar:
    st.subheader("AI控制面板")
    if st.button("新建会话", width="stretch"):
        if st.session_state.current_session:
            save_session()
            st.session_state.messages = []
            st.session_state.current_session = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            save_session()
            st.rerun()
    st.text("历史会话")
    session_list=load_sessions()
    for session in session_list:
        col1,col2=st.columns([4,1])
        with col1:
            if st.button(session,width="stretch",key=f"load_{session}",type="primary" if session==st.session_state.current_session else "secondary"):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("",width="stretch",icon="❌",key=f"delete_{session}"):
                delete_session(session)
                st.rerun()
    st.divider()
    st.subheader("伴侣信息")
    nick_name=st.text_input("昵称",placeholder="请输入昵称",value=st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name
    nature=st.text_area("性格",placeholder="请输入性格",value=st.session_state.nature)
    if nature:
        st.session_state.nature = nature
prompt=st.chat_input("请输入你要问的问题")
if prompt:
    st.chat_message("user").write(prompt)
    st.session_state.messages.append({"role":"user","content": prompt})
    response = client.chat.completions.create(
        model="deepseek-v4-pro",
        messages=[
            {"role": "system", "content":system_prompt.format(st.session_state.nick_name,st.session_state.nature)},
            *st.session_state.messages
        ],
        stream=True,
        reasoning_effort="high",
        extra_body={"thinking": {"type": "enabled"}}
    )
    response_message=st.empty()
    full_response=""
    for chunk in response:
        if chunk.choices[0].delta.content is not None:
            content=chunk.choices[0].delta.content
            full_response=full_response+content
            response_message.chat_message("assistant").write(full_response)
    st.session_state.messages.append({"role":"assistant","content":full_response})
    save_session()