import streamlit as st
import random
import json
import os
from twilio.rest import Client

# безопасный доступ к secrets
TWILIO_ACCOUNT_SID = st.secrets.get("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = st.secrets.get("TWILIO_AUTH_TOKEN", "")

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
        if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
            st.error("Twilio secrets не настроены")
            return False

        client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
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
            return json.load(f)
    except:
        return {}

def save_users(users):
    with open("users.json", "w") as f:
        json.dump(users, f)

# =========================
# SYNC
# =========================
file_users = load_users()

if "users" not in st.session_state:
    st.session_state.users = file_users
else:
    if not os.path.exists("users.json"):
        st.session_state.users = {}
    else:
        st.session_state.users = file_users

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

st.title("🚇 Sapar")

# ======================================================
# AUTH
# ======================================================
if not st.session_state.logged_in:

    tab1, tab2 = st.tabs(["Войти", "Регистрация"])

    # LOGIN
    with tab1:
        phone = st.text_input("Номер телефона", key="login_phone")
        password = st.text_input("Пароль", type="password", key="login_pass")

        if st.button("Войти", key="login_btn", disabled=not (phone and password)):
            user = st.session_state.users.get(phone)
            if user and user["password"] == password:
                st.session_state.logged_in = True
                st.session_state.phone = phone
                st.rerun()
            else:
                st.error("Неверный номер или пароль")

        st.markdown("<small><u>Забыли пароль?</u></small>", unsafe_allow_html=True)

        if st.button("Восстановить пароль", key="forgot_start"):
            st.session_state.forgot_step = 1

        if st.session_state.forgot_step == 1:
            fp_phone = st.text_input("Введите номер", key="fp_phone")

            if st.button("Отправить код", key="forgot_send_code"):
                if fp_phone in st.session_state.users:
                    otp = generate_otp()
                    st.session_state.forgot_otp = otp
                    st.session_state.forgot_phone = fp_phone
                    send_otp(fp_phone, otp)
                    st.session_state.forgot_step = 2
                else:
                    st.error("Пользователь не найден")

        elif st.session_state.forgot_step == 2:
            code = st.text_input("SMS код", key="forgot_code")

            if st.button("Проверить", key="forgot_verify"):
                if code == st.session_state.forgot_otp:
                    st.session_state.forgot_step = 3
                else:
                    st.error("Неверный код")

        elif st.session_state.forgot_step == 3:
            p1 = st.text_input("Новый пароль", type="password", key="forgot_p1")
            p2 = st.text_input("Повторите пароль", type="password", key="forgot_p2")

            if st.button("Сохранить", key="forgot_save"):
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

            if st.button("Отправить код", key="reg_send_code"):
                if reg_phone in st.session_state.users:
                    st.error("Уже зарегистрирован")
                else:
                    otp = generate_otp()
                    if send_otp(reg_phone, otp):
                        st.session_state.otp = otp
                        st.session_state.temp_phone = reg_phone
                        st.session_state.reg_step = 2

        elif st.session_state.reg_step == 2:
            sms = st.text_input("Введите SMS код", key="reg_sms")

            if st.button("Проверить", key="reg_verify"):
                if sms == st.session_state.otp:
                    st.session_state.reg_step = 3
                else:
                    st.error("Неверный код")

        elif st.session_state.reg_step == 3:
            p1 = st.text_input("Пароль", type="password", key="reg_p1")
            p2 = st.text_input("Повторите пароль", type="password", key="reg_p2")

            if st.button("Далее", key="reg_next"):
                if p1 == p2:
                    st.session_state.temp_password = p1
                    st.session_state.reg_step = 4
                else:
                    st.error("Пароли не совпадают")

        elif st.session_state.reg_step == 4:
            pin1 = st.text_input("PIN", max_chars=4, key="reg_pin1")
            pin2 = st.text_input("Повтор PIN", max_chars=4, key="reg_pin2")

            if st.button("Создать аккаунт", key="reg_create"):
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

    # REGION
    st.sidebar.markdown("### 🌍 Регион")
    region = st.sidebar.selectbox(
        "Выберите регион",
        KZ_REGIONS,
        index=KZ_REGIONS.index(st.session_state.region),
        key="region_select"
    )
    st.session_state.region = region

    # MENU
    menu = st.sidebar.selectbox(
        "Меню",
        ["Маршруты", "Профиль", "Карта", "История"],
        index=0,
        key="menu_select"
    )

    # ================= ROUTES (MAIN SCREEN)
    if menu == "Маршруты":

        st.title(f"🚌 Маршруты — {region}")

        region_routes = {
            "Межобластной": [f"{region} — Область {i}" for i in range(1, 4)],
            "Междугородний": [f"{region} — Город {i}" for i in range(1, 4)],
            "Городской": [str(random.randint(1, 150)) for _ in range(5)],
            "Внутрирайонный": [f"{region[:2]}-{i}" for i in range(1, 4)]
        }

        tab1, tab2, tab3, tab4 = st.tabs([
            "🚍 Межобластной",
            "🏙️ Междугородний",
            "🚌 Городской",
            "🚐 Внутрирайонный"
        ])

        with tab1:
            for r in region_routes["Межобластной"]:
                st.write("🚍", r)

        with tab2:
            for r in region_routes["Междугородний"]:
                st.write("🏙️", r)

        with tab3:
            for r in region_routes["Городской"]:
                st.write("🚌 Маршрут", r)

        with tab4:
            for r in region_routes["Внутрирайонный"]:
                st.write("🚐", r)

    # ================= PROFILE
    elif menu == "Профиль":
        st.title("👤 Профиль")
        st.metric("Баланс", f"{user['balance']} ₸")

    # ================= MAP
    elif menu == "Карта":
        st.title(f"🗺️ Карта — {region}")
        st.info("Скоро будет 🚧")

    # ================= HISTORY
    elif menu == "История":
        st.title("📜 История")
        for h in user.get("history", []):
            st.write("•", h)

    # LOGOUT
    if st.sidebar.button("Выйти", key="logout_btn"):
        st.session_state.logged_in = False
        st.rerun()
