import streamlit as st
import random
import json
import os
from twilio.rest import Client

# =========================
# CONFIG
# =========================
st.set_page_config(
    page_title="Sapar",
    page_icon="🚇",
    layout="wide"
)

# =========================
# TWILIO SAFE MODE
# =========================
def get_twilio_client():
    sid = st.secrets.get("TWILIO_ACCOUNT_SID")
    token = st.secrets.get("TWILIO_AUTH_TOKEN")

    if not sid or not token:
        return None

    return Client(sid, token)

# =========================
# REGIONS
# =========================
KZ_REGIONS = [
    "Астана", "Алматы", "Шымкент",
    "Абайская область", "Акмолинская область", "Актюбинская область",
    "Алматинская область", "Атырауская область", "Восточно-Казахстанская область",
    "Жамбылская область", "Жетысуская область", "Западно-Казахстанская область",
    "Карагандинская область", "Костанайская область", "Кызылординская область",
    "Мангистауская область", "Павлодарская область", "Северо-Казахстанская область",
    "Туркестанская область", "Улытауская область"
]

# =========================
# SMS
# =========================
def send_otp(phone, otp):
    try:
        client = get_twilio_client()

        if client is None:
            st.warning("Twilio не настроен (dev mode)")
            st.info(f"КОД ДЛЯ ТЕСТА: {otp}")
            return True

        client.messages.create(
            body=f"Ваш код: {otp}",
            from_='+16812972877',
            to=phone
        )
        return True

    except Exception as e:
        st.error(f"SMS ошибка: {e}")
        return False


def generate_otp():
    return str(random.randint(100000, 999999))

# =========================
# DB
# =========================
def load_users():
    if not os.path.exists("users.json"):
        return {}
    try:
        with open("users.json", "r") as f:
            data = json.load(f)
            return data if isinstance(data, dict) else {}
    except:
        return {}


def save_users(users):
    try:
        with open("users.json", "w") as f:
            json.dump(users, f)
    except Exception as e:
        st.error(f"DB error: {e}")


file_users = load_users()

if "users" not in st.session_state:
    st.session_state.users = file_users
else:
    st.session_state.users = load_users()

# =========================
# INIT STATE
# =========================
defaults = {
    "logged_in": False,
    "phone": None,
    "region": "Алматы",
    "reg_step": 1,
    "otp": None,
    "temp_phone": None,
    "temp_password": None,
    "forgot_step": 0,
    "forgot_otp": None,
    "forgot_phone": None,
}

for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


def reset_reg():
    st.session_state.reg_step = 1
    st.session_state.otp = None
    st.session_state.temp_phone = None
    st.session_state.temp_password = None


st.title("🚇 Sapar App")

# ======================================================
# AUTH
# ======================================================
if not st.session_state.logged_in:

    tab1, tab2 = st.tabs(["Войти", "Регистрация"])

    # LOGIN
    with tab1:
        phone = st.text_input("Номер телефона", key="login_phone")
        password = st.text_input("Пароль", type="password", key="login_pass")

        if st.button("Войти", disabled=not (phone and password)):
            user = st.session_state.users.get(phone)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.phone = phone
                st.rerun()
            else:
                st.error("Неверный номер или пароль")

        if st.button("Восстановить пароль"):
            st.session_state.forgot_step = 1

        if st.session_state.forgot_step == 1:
            fp_phone = st.text_input("Введите номер", key="fp_phone")

            if st.button("Отправить код"):
                if fp_phone in st.session_state.users:
                    otp = generate_otp()
                    st.session_state.forgot_otp = otp
                    st.session_state.forgot_phone = fp_phone
                    send_otp(fp_phone, otp)
                    st.session_state.forgot_step = 2
                else:
                    st.error("Пользователь не найден")

        elif st.session_state.forgot_step == 2:
            code = st.text_input("SMS код")

            if st.button("Проверить"):
                if code == st.session_state.forgot_otp:
                    st.session_state.forgot_step = 3
                else:
                    st.error("Неверный код")

        elif st.session_state.forgot_step == 3:
            p1 = st.text_input("Новый пароль", type="password")
            p2 = st.text_input("Повторите пароль", type="password")

            if st.button("Сохранить"):
                if p1 == p2:
                    phone = st.session_state.forgot_phone
                    st.session_state.users[phone]["password"] = p1
                    save_users(st.session_state.users)
                    st.success("Пароль обновлён")
                    st.session_state.forgot_step = 0
                else:
                    st.error("Пароли не совпадают")

    # REGISTER
    with tab2:

        if st.session_state.reg_step == 1:
            reg_phone = st.text_input("Номер телефона", key="reg_phone")

            if st.button("Отправить код"):
                if reg_phone in st.session_state.users:
                    st.error("Уже зарегистрирован")
                else:
                    otp = generate_otp()
                    if send_otp(reg_phone, otp):
                        st.session_state.otp = otp
                        st.session_state.temp_phone = reg_phone
                        st.session_state.reg_step = 2

        elif st.session_state.reg_step == 2:
            sms = st.text_input("SMS код")

            if st.button("Проверить"):
                if sms == st.session_state.otp:
                    st.session_state.reg_step = 3
                else:
                    st.error("Неверный код")

        elif st.session_state.reg_step == 3:
            p1 = st.text_input("Пароль", type="password")
            p2 = st.text_input("Повтор пароля", type="password")

            if st.button("Далее"):
                if p1 == p2:
                    st.session_state.temp_password = p1
                    st.session_state.reg_step = 4
                else:
                    st.error("Пароли не совпадают")

        elif st.session_state.reg_step == 4:
            pin1 = st.text_input("PIN", max_chars=4)
            pin2 = st.text_input("Повтор PIN", max_chars=4)

            if st.button("Создать аккаунт"):
                if pin1 == pin2 and len(pin1) == 4:
                    st.session_state.users[st.session_state.temp_phone] = {
                        "password": st.session_state.temp_password,
                        "pin": pin1,
                        "balance": 350,
                        "history": []
                    }
                    save_users(st.session_state.users)
                    st.success("Аккаунт создан!")
                    reset_reg()
                else:
                    st.error("Ошибка PIN")

# ======================================================
# DASHBOARD
# ======================================================
else:

    user = st.session_state.users[st.session_state.phone]

    # REGION SAFE
    default_region = st.session_state.region if st.session_state.region in KZ_REGIONS else "Алматы"

    region = st.sidebar.selectbox(
        "Регион",
        KZ_REGIONS,
        index=KZ_REGIONS.index(default_region)
    )
    st.session_state.region = region

    menu = st.sidebar.selectbox(
        "Меню",
        ["Маршруты", "Профиль", "Карта", "История"]
    )

    if menu == "Маршруты":

        st.title(f"🚌 Маршруты — {region}")

        routes = {
            "Межобластной": [f"{region} — Область {i}" for i in range(1, 4)],
            "Междугородний": [f"{region} — Город {i}" for i in range(1, 4)],
            "Городской": [str(random.randint(1, 150)) for _ in range(5)],
            "Внутрирайонный": [f"{region[:2]}-{i}" for i in range(1, 4)]
        }

        tabs = st.tabs(["🚍 Межобластной", "🏙️ Междугородний", "🚌 Городской", "🚐 Внутрирайонный"])

        for i, key in enumerate(routes):
            with tabs[i]:
                for r in routes[key]:
                    st.write(r)

    elif menu == "Профиль":
        st.title("👤 Профиль")
        st.metric("Баланс", f"{user['balance']} ₸")

    elif menu == "Карта":
        st.title("🗺️ Карта")
        st.info("Скоро будет 🚧")

    elif menu == "История":
        st.title("📜 История")
        for h in user.get("history", []):
            st.write("•", h)

    if st.sidebar.button("Выйти"):
        st.session_state.logged_in = False
        st.rerun()
