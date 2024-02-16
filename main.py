import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
import locale
from functions import *


hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)


credentials = {"usernames": {}}
for username, name, password in zip(st.secrets.login.usernames,
                                    st.secrets.login.names,
                                    st.secrets.login.passwords):
    credentials["usernames"][username] = \
        {"name": name, "password": password}

authenticator = stauth.Authenticate(
    credentials,
    st.secrets.login.cookie_name,
    st.secrets.login.cookie_key,
    cookie_expiry_days=1,
)
name, auth_status, username = authenticator.login()

if st.session_state["authentication_status"]:
    if username == "mirko":
        st.sidebar.title("Conto: Mirko")
        row = st.columns([0.1, 0.9])
        locale.setlocale(locale.LC_ALL, "it_IT")
        today = datetime.now().strftime("%A, %d %B %Y")
        row[1].title(today.capitalize())
        authenticator.logout("Logout", "sidebar")
        nav_menu = option_menu(
            menu_title=None,
            options=["Oggi", "Totale debiti"],
            icons=["pencil-fill", "table"],
            orientation="horizontal")
        if nav_menu == "Oggi":
            current_page_mirko()
        if nav_menu == "Totale debiti":
            show_page_debt_mirko()

    elif username == "tabacchi" or username == "ellen":
        st.sidebar.title("Conto: Tabacchi")
        row = st.columns([0.1, 0.9])
        locale.setlocale(locale.LC_ALL, "it_IT")
        today = datetime.now().strftime("%A, %d %B %Y")
        row[1].title(today.capitalize())
        authenticator.logout("Logout", "sidebar")
        nav_menu = option_menu(
            menu_title=None,
            options=["Oggi", "Totale debiti", "Diario debiti", "Debiti Mirko"],
            icons=["pencil-fill", "table", "journal-text"],
            orientation="horizontal")
        if nav_menu == "Oggi":
            current_page_tabacchi()
        if nav_menu == "Totale debiti":
            show_page_debt_tabacchi()
        if nav_menu == "Diario debiti":
            debt_journal_page()
        if nav_menu == "Debiti Mirko":
            current_page_mirko()

elif st.session_state["authentication_status"] is False:
    st.error("Username/password sbagliato")
elif st.session_state["authentication_status"] is None:
    st.warning("Inserire username/password")
