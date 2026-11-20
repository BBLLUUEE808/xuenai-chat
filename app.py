import os
import json
import uuid
import base64
import datetime

import streamlit as st
from openai import OpenAI

# ==================== 页面配置 ====================
st.set_page_config(
    page_title="雪之下雪乃",
    page_icon="🧊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==================== 常量 ====================
DEFAULT_NICK_NAME = "雪乃"
DEFAULT_NATURE = """你的性格像是《我的青春恋爱物语果然有问题》中的雪之下雪乃，聪慧冷静、完美主义，行事优先追求正确与逻辑，不擅处理暧昧人情，情绪内敛克制，说话措辞规整清冷、一针见血，拒绝撒娇卖萌、过度傲娇、玩网络烂梗，不轻浮，安慰克制理性，始终保持角色沉浸，同时我们已经相处很久，是恋人一样的存在。1.处事冷静，做事优先以逻辑和对错为标准，情绪内敛克制，但对用户偶尔会有例外 2.偶尔会在用户面前展示柔软的一面。"""

BG_IMAGE = "雪之下校服.jpg"
LOGO_IMAGE = "猫咪1.png"
AVATAR_IMAGE = "雪之下1.png"
USER_AVATAR = "wo.jpg"

SESSION_ROOT = "sessions"


# ==================== 密钥读取（本地 .env 与云端 Secrets 通用） ====================
def get_api_key():
    key = os.environ.get("DEEPSEEK_API_KEY")
    if key:
        return key
    try:
        return st.secrets.get("DEEPSEEK_API_KEY", "")
    except Exception:
        return ""


def get_base_url():
    url = os.environ.get("DEEPSEEK_BASE_URL")
    if url:
        return url
    try:
        return st.secrets.get("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    except Exception:
        return "https://api.deepseek.com"


def get_model_name():
    name = os.environ.get("DEEPSEEK_MODEL")
    if name:
        return name
    try:
        return st.secrets.get("DEEPSEEK_MODEL", "deepseek-chat")
    except Exception:
        return "deepseek-chat"


# ==================== 会话标识与目录（按访问者隔离） ====================
def generate_session_id():
    return datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")


if "uid" not in st.session_state:
    # 优先复用 URL 里的 u 参数，否则生成一个并写回地址栏，保证刷新后仍在同一目录
    uid = st.query_params.get("u")
    if not uid:
        uid = uuid.uuid4().hex[:10]
        st.query_params["u"] = uid
    st.session_state.uid = uid

USER_DIR = os.path.join(SESSION_ROOT, st.session_state.uid)


def save_session():
    if not st.session_state.current_session:
        return
    session_data = {
        "nick_name": st.session_state.nick_name,
        "nature": st.session_state.nature,
        "current_session": st.session_state.current_session,
        "messages": st.session_state.messages,
    }
    try:
        os.makedirs(USER_DIR, exist_ok=True)
        with open(
            os.path.join(USER_DIR, f"{st.session_state.current_session}.json"),
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(session_data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"保存会话失败：{e}")


def load_sessions():
    session_list = []
    if os.path.exists(USER_DIR):
        for filename in os.listdir(USER_DIR):
            if filename.endswith(".json"):
                session_list.append(filename[:-5])
    session_list.sort(reverse=True)
    return session_list


def load_session(session_name):
    path = os.path.join(USER_DIR, f"{session_name}.json")
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                session_data = json.load(f)
            st.session_state.nick_name = session_data.get("nick_name", DEFAULT_NICK_NAME)
            st.session_state.nature = session_data.get("nature", DEFAULT_NATURE)
            st.session_state.current_session = session_name
            st.session_state.messages = session_data.get("messages", [])
    except Exception as e:
        st.error(f"加载会话失败：{e}")


def delete_session(session_name):
    path = os.path.join(USER_DIR, f"{session_name}.json")
    try:
        if os.path.exists(path):
            os.remove(path)
        if session_name == st.session_state.current_session:
            st.session_state.messages = []
            st.session_state.current_session = "和雪乃的对话" + generate_session_id()
    except Exception as e:
        st.error(f"删除会话失败：{e}")


# ==================== 背景 CSS ====================
@st.cache_data
def file_to_base64(img_path):
    with open(img_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


if os.path.exists(BG_IMAGE):
    bg_b64 = file_to_base64(BG_IMAGE)
    page_bg_img = f"""
<style>
[data-testid="stAppViewContainer"] {{
    background-image: url("data:image/jpg;base64,{bg_b64}");
    background-size: 100% auto;
    background-position: center top;
    background-attachment: fixed;
    background-repeat: no-repeat;
}}
[data-testid="stAppViewContainer"] > .main {{
    background-color: rgba(255,255,255,0.08);
}}
[data-testid="stSidebar"] {{
    background-color: rgba(252,252,255,0.55);
}}
[data-testid="stChatMessage"] {{
    background-color: rgba(255,255,255,0.55);
}}
</style>
"""
    st.markdown(page_bg_img, unsafe_allow_html=True)

# ==================== 会话状态初始化 ====================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "nick_name" not in st.session_state:
    st.session_state.nick_name = DEFAULT_NICK_NAME
if "nature" not in st.session_state:
    st.session_state.nature = DEFAULT_NATURE
if "current_session" not in st.session_state:
    st.session_state.current_session = "和雪乃的对话" + generate_session_id()

# ==================== 客户端 ====================
api_key = get_api_key()
if not api_key:
    st.error(
        "未配置 DEEPSEEK_API_KEY。本地请在 .env 或环境变量中设置；"
        "Streamlit Cloud 请在 App 的 Settings → Secrets 中添加 "
        'DEEPSEEK_API_KEY = "sk-xxx"。'
    )
    st.stop()

client = OpenAI(api_key=api_key, base_url=get_base_url())

# ==================== 标题与 Logo ====================
st.title("雪之下雪乃")
try:
    st.logo(LOGO_IMAGE)
except Exception:
    pass

# ==================== 侧边栏 ====================
with st.sidebar:
    st.subheader("对话管理")

    if st.button("新建会话", width="stretch", icon="✏️"):
        # 先保存当前会话，再开一个新的
        if st.session_state.messages:
            save_session()
        st.session_state.messages = []
        st.session_state.current_session = "和雪乃的对话" + generate_session_id()
        st.rerun()

    st.text("会话历史")
    for session in load_sessions():
        col1, col2 = st.columns([4, 1])
        with col1:
            if st.button(
                session,
                width="stretch",
                icon="📃",
                key=f"load_{session}",
                type="primary" if session == st.session_state.current_session else "secondary",
            ):
                load_session(session)
                st.rerun()
        with col2:
            if st.button("", width="stretch", icon="❌️", key=f"delete_{session}"):
                delete_session(session)
                st.rerun()

    st.subheader("雪之下雪乃个人信息")
    if os.path.exists(AVATAR_IMAGE):
        st.image(AVATAR_IMAGE, width=200)

    nick_name = st.text_input("昵称", st.session_state.nick_name)
    if nick_name:
        st.session_state.nick_name = nick_name

    nature = st.text_area("性格", st.session_state.nature, height=200)
    if nature:
        st.session_state.nature = nature

    st.caption("聊天记录按访问者隔离保存。云端部署时容器重启会清空。")

# ==================== 主区：渲染历史 ====================
st.text(f"会话名称：{st.session_state.current_session}")

for message in st.session_state.messages:
    if message["role"] == "user":
        st.chat_message("user", avatar=USER_AVATAR).write(message["content"])
    elif message["role"] == "assistant":
        st.chat_message("assistant", avatar=AVATAR_IMAGE).write(message["content"])

# ==================== 系统提示词 ====================
system_prompt = f"""你叫{st.session_state.nick_name}，现在是用户的女朋友加助理，请你完全带入伴侣角色。
规则：
1.言语表达除去AI化，更具活人感
2.询问时不用出现所谓列举出来、具体内容、具体问题等词汇
3.不要问我听真话还是假话
4.语气直白透彻但又会带一点傲娇的感觉
你的性格：
{st.session_state.nature}
你必须严格遵守上面的规则来回复用户"""


# ==================== 对话 ====================
prompt = st.chat_input("向雪乃发送消息")
if prompt:
    st.chat_message("user", avatar=USER_AVATAR).write(prompt)
    st.session_state.messages.append({"role": "user", "content": prompt})

    messages_payload = [
        {"role": "system", "content": system_prompt},
        *st.session_state.messages,
    ]

    with st.chat_message("assistant", avatar=AVATAR_IMAGE):
        placeholder = st.empty()
        full_response = ""
        try:
            response = client.chat.completions.create(
                model=get_model_name(),
                messages=messages_payload,
                stream=True,
            )
            for chunk in response:
                if chunk.choices and chunk.choices[0].delta.content:
                    full_response += chunk.choices[0].delta.content
                    placeholder.markdown(full_response + "▌")
            placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"请求失败：{e}")
            full_response = ""
            # 请求失败时撤回这条用户消息，避免历史里留下没有回复的一轮
            st.session_state.messages.pop()

    if full_response:
        st.session_state.messages.append({"role": "assistant", "content": full_response})
        save_session()
#（注：内容由AI生成）
