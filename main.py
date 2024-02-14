import streamlit_authenticator as stauth
from streamlit_option_menu import option_menu
from functions import *

hide_st_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                header {visibility: hidden;}
                </style>
                """
st.markdown(hide_st_style, unsafe_allow_html=True)


nav_menu = option_menu(
    menu_title=None,
    options=["Oggi", "Totale debiti", "Diario debiti"],
    orientation="horizontal"
)

if nav_menu == "Totale debiti":
    show_page_debt_tabacchi()