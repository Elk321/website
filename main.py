import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
import locale
from functions import *

timezone = pytz.timezone('Europe/Rome')
now = datetime.now(tz=timezone)
current_date = now.strftime("%Y-%m-%d")
if not check_file_exists(f"date/tabacchi/{current_date}.csv"):
    debt_list = pd.DataFrame(columns=["nome", "debiti", "pagati", "oggetto", "ore"])
    upload_file(f"date/tabacchi/{current_date}.csv", debt_list)
else:
    debt_list = read_file(f"date/tabacchi/{current_date}.csv")
lista_tabacchi = read_file("lista/lista_debiti_tabacchi.csv")
name_list = read_file("lista/name_list.csv")
object_list = read_file("lista/oggetto.csv")
blacklist = read_file("lista/lista_nera.csv")


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
        timezone = pytz.timezone("Europe/Rome")
        today = datetime.now(tz=timezone).strftime("%A, %d %B %Y")
        row[1].title(today.capitalize())
        authenticator.logout("Logout", "sidebar")
        nav_menu = option_menu(
            menu_title=None,
            options=["Oggi", "Totale debiti"],
            icons=["pencil-fill", "table"],
            orientation="horizontal")
        if nav_menu == "Oggi":
            pass
        if nav_menu == "Totale debiti":
            pass

    elif username == "tabacchi" or username == "ellen":
        st.sidebar.title("Conto: Tabacchi")
        row = st.columns([0.1, 0.9])
        locale.setlocale(locale.LC_ALL, "it_IT")
        timezone = pytz.timezone("Europe/Rome")
        today = datetime.now(tz=timezone).strftime("%A, %d %B %Y")
        row[1].title(today.capitalize())
        authenticator.logout("Logout", "sidebar")
        nav_menu = option_menu(
            menu_title=None,
            options=["Oggi", "Totale debiti", "Diario debiti", "Debiti Mirko"],
            icons=["pencil-fill", "table", "journal-text"],
            orientation="horizontal")
        if nav_menu == "Oggi":
            lista_tabacchi = current_page_tabacchi(name_list, object_list,
                                                   lista_tabacchi, blacklist,
                                                   debt_list, current_date)
        if nav_menu == "Totale debiti":
            lista_tabacchi, blacklist = show_page_debt_tabacchi(lista_tabacchi, blacklist)
        if nav_menu == "Diario debiti":
            debt_journal_page()
        if nav_menu == "Debiti Mirko":
            pass

elif st.session_state["authentication_status"] is False:
    st.error("Username/password sbagliato")
elif st.session_state["authentication_status"] is None:
    st.warning("Inserire username/password")
