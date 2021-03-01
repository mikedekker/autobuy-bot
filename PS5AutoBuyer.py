#!/usr/bin/env python
# -*- coding: utf-8 -*-

import configparser
import platform
import random
import re
import sys
import time
from os import system, name
from amazoncaptcha import AmazonCaptcha

import requests
from bs4 import BeautifulSoup
import six
from PyInquirer import (Token, ValidationError, Validator, prompt,
                        style_from_dict)
from pyfiglet import figlet_format
from rich.console import Console
from selenium.common import exceptions as SE
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as WDW

try:
    from termcolor import colored
except ImportError:
    colored = None

__author__ = "Olle de Jong"
__copyright__ = "Copyright 2020, Olle de Jong"
__license__ = "MIT"
__maintainer__ = "Olle de Jong"
__email__ = "olledejong@gmail.com"

# ================= #
# PARSE CONFIG FILE #
# ================= #
parser = configparser.ConfigParser()
parser.read("config.ini")
in_production = parser.getboolean("developer", "production")
bot_token = parser['telegram']['tgtoken']
bot_chatID = parser['telegram']['tgchatid']

# ================ #
# INITIALIZE STUFF #
# ================ #
console = Console()

with open('resources\\user-agents.txt') as f:
    user_agents = f.read().splitlines()

referers = [
    'http://www.bing.com/',
    'http://www.google.com/',
    'https://search.yahoo.com/',
    'http://www.baidu.com/',
    'https://duckduckgo.com/'
]

# =============================== #
# DICTIONARY WITH WEBSHOP DETAILS #
# =============================== #
locations = {
    'Amazon NL Disk': {
        'webshop': 'amazon-nl',
        'url': 'https://www.amazon.nl/dp/B08H93ZRK9',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Momenteel niet verkrijgbaar",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon NL Digital': {
        'webshop': 'amazon-nl',
        'url': 'https://www.amazon.nl/dp/B08H98GVK8',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Momenteel niet verkrijgbaar",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon IT Disk': {
        'webshop': 'amazon-it',
        'url': 'https://www.amazon.it/dp/B08KKJ37F7',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Non disponibile",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon IT Digital': {
        'webshop': 'amazon-it',
        'url': 'https://www.amazon.it/dp/B08KJF2D25',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Non disponibile",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon FR Disk': {
        'webshop': 'amazon-fr',
        'url': 'https://www.amazon.fr/dp/B08H93ZRK9',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Actuellement indisponible",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon FR Digital': {
        'webshop': 'amazon-fr',
        'url': 'https://www.amazon.fr/dp/B08H98GVK8',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Actuellement indisponible",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon ES Disk': {
        'webshop': 'amazon-es',
        'url': 'https://www.amazon.es/dp/B08KKJ37F7',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "No disponible",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon ES Digital': {
        'webshop': 'amazon-es',
        'url': 'https://www.amazon.es/dp/B08KJF2D25',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "No disponible",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon DE Disk': {
        'webshop': 'amazon-de',
        'url': 'https://www.amazon.de/dp/B08VLX84G6',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Derzeit nicht verfügbar.",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon DE Digital': {
        'webshop': 'amazon-de',
        'url': 'https://www.amazon.de/dp/B08W8JT5ZN',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Derzeit nicht verfügbar.",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon UK Disk': {
        'webshop': 'amazon-uk',
        'url': 'https://www.amazon.co.uk/dp/B08H95Y452',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Currently unavailable",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'Amazon UK Digital': {
        'webshop': 'amazon-uk',
        'url': 'https://www.amazon.co.uk/dp/B08H97NYGP',
        'inStock': False,
        'inStockLabel': "submit.add-to-cart-announce",
        'outOfStockLabel': "Currently unavailable",
        'detectedAsBotLabel': "please contact api-services-support@amazon.com"},
    'COOLBLUE Disk': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/865866',
        'inStock': False,
        'inStockLabel': "In mijn winkelwagen",
        'outOfStockLabel': "Houd mij op de hoogte",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'COOLBLUE Digital': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/865867',
        'inStock': False,
        'inStockLabel': "In mijn winkelwagen",
        'outOfStockLabel': "Houd mij op de hoogte",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'COOLBLUE Disk set spider man + pulse 3D headset': {
        'webshop': 'coolblue-nietkopen',
        'url': 'https://www.coolblue.nl/product/878811',
        'inStock': False,
        'inStockLabel': "In mijn winkelwagen",
        'outOfStockLabel': "Houd mij op de hoogte",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'COOLBLUE Disk set FIFA21 + controller': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/878814',
        'inStock': False,
        'inStockLabel': "In mijn winkelwagen",
        'outOfStockLabel': "Houd mij op de hoogte",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'COOLBLUE Disk set COD black ops + steelseries headset': {
        'webshop': 'coolblue-nietkopen',
        'url': 'https://www.coolblue.nl/product/878814',
        'inStock': False,
        'inStockLabel': "In mijn winkelwagen",
        'outOfStockLabel': "Houd mij op de hoogte",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'COOLBLUE Disk set met controller': {
        'webshop': 'coolblue',
        'url': 'https://www.coolblue.nl/product/878814',
        'inStock': False,
        'inStockLabel': "In mijn winkelwagen",
        'outOfStockLabel': "Houd mij op de hoogte"},
    'BCC Disk en extra controller': {
        'webshop': 'bcc',
        'url': 'https://www.bcc.nl/gaming/playstation/playstation-5-console/playstation-5-bundel-met-extra-controller/302239',
        'inStock': False,
        'inStockLabel': "Online op voorraad",
        'outOfStockLabel': "niet leverbaar",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'BOL.COM Disk': {
        'webshop': 'bol',
        'url': 'https://www.bol.com/nl/p/sony-playstation-5-console/9300000004162282/',
        'inStock': False,
        'inStockLabel': "btn btn--cta btn--buy btn--lg ] js_floating_basket_btn js_btn_buy js_preventable_buy_action",
        'outOfStockLabel': "outofstock-buy-block",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'BOL.COM Digital': {
        'webshop': 'bol',
        'url': 'https://www.bol.com/nl/p/sony-playstation-5-all-digital-console/9300000004162392/',
        'inStock': False,
        'inStockLabel': "btn btn--cta btn--buy btn--lg ] js_floating_basket_btn js_btn_buy js_preventable_buy_action",
        'outOfStockLabel': "outofstock-buy-block",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'MEDIAMARKT NL Disk': {
        'webshop': 'mediamarkt-nl',
        'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-disk-edition-1664768.html',
        'inStock': False,
        'inStockLabel': "online online-ndd",
        'outOfStockLabel': "Online uitverkocht",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'MEDIAMARKT NL Digital': {
        'webshop': 'mediamarkt-nl',
        'url': 'https://www.mediamarkt.nl/nl/product/_sony-playstation-5-digital-edition-1665134.html',
        'inStock': False,
        'inStockLabel': "online online-ndd",
        'outOfStockLabel': "Online uitverkocht",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'GAMEMANIA Disk': {
        'webshop': 'gamemania',
        'url': 'https://www.gamemania.nl/Consoles/playstation-5/144093_playstation-5-disc-edition',
        'inStock': False,
        'inStockLabel': "AddToCartOverlay",
        'outOfStockLabel': "Niet beschikbaar",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'GAMEMANIA Digital': {
        'webshop': 'gamemania',
        'url': 'https://www.gamemania.nl/Consoles/playstation-5/145721_playstation-5-digital-edition',
        'inStock': False,
        'inStockLabel': "AddToCartOverlay",
        'outOfStockLabel': "Niet beschikbaar",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'INTERTOYS Disk': {
        'webshop': 'intertoys',
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-825gb',
        'inStock': False,
        'inStockLabel': "productPageAdd2Cart",
        'outOfStockLabel': "uitverkocht!",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'INTERTOYS Digital': {
        'webshop': 'intertoys',
        'url': 'https://www.intertoys.nl/shop/nl/intertoys/ps5-digital-edition-825gb',
        'inStock': False,
        'inStockLabel': "productPageAdd2Cart",
        'outOfStockLabel': "uitverkocht!",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'NEDGAME Disk': {
        'webshop': 'nedgame',
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5--levering-begin-2021-/6036644854/',
        'inStock': False,
        'inStockLabel': "AddProductToBasket",
        'outOfStockLabel': "Uitverkocht",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'NEDGAME Digital': {
        'webshop': 'nedgame',
        'url': 'https://www.nedgame.nl/playstation-5/playstation-5-digital-edition--levering-begin-2021-/9647865079/',
        'inStock': False,
        'inStockLabel': "AddProductToBasket",
        'outOfStockLabel': "Uitverkocht",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Alternate DE Disk': {
        'webshop': 'Alternate.de',
        'url': 'https://www.alternate.de/Sony-Interactive-Entertainment/PlayStation-5-Spielkonsole/html/product/1651220',
        'inStock': False,
        'inStockLabel': "arrow-cart-white_red-right",
        'outOfStockLabel': "Artikel kann nicht gekauft werden",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Alternate DE Digital': {
        'webshop': 'Alternate.de',
        'url': 'https://www.alternate.de/Sony-Interactive-Entertainment/PlayStation-5-Digital-Edition-Spielkonsole/html/product/1651221',
        'inStock': False,
        'inStockLabel': "arrow-cart-white_red-right",
        'outOfStockLabel': "Artikel kann nicht gekauft werden",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
#    'Mediamarkt DE Disk': {
#        'webshop': 'mediamarkt-de',
#        'url': 'https://www.mediamarkt.de/de/product/_sony-playstation%C2%AE5-2661938.html',
#        'inStock': False,
#        'inStockLabel': "pdp-add-to-cart-button",
#        'outOfStockLabel': "Dieser Artikel ist aktuell nicht verfügbar.<",
#        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
#    'Mediamarkt DE Digital': {
#        'webshop': 'mediamarkt-de',
#        'url': 'https://www.mediamarkt.de/de/product/_sony-playstation%C2%AE5-digital-edition-2661939.html',
#        'inStock': False,
#        'inStockLabel': "pdp-add-to-cart-button",
#        'outOfStockLabel': "Dieser Artikel ist aktuell nicht verfügbar.<",
#        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
#    'Saturn DE Disk': {
#        'webshop': 'saturn-de',
#        'url': 'https://www.saturn.de/de/product/_sony-playstation%C2%AE5-2661938.html',
#        'inStock': False,
#        'inStockLabel': "Buttonstyled__StyledButton-sc-140xkaw-1 dwrUQL BasketButton__StyledButton-sc-1qvc90d-0 gQISZA",
#        'outOfStockLabel': "Dieser Artikel ist aktuell nicht verfügbar.<",
#        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
#    'Saturn DE Digital': {
#        'webshop': 'saturn-de',
#        'url': 'https://www.saturn.de/de/product/_sony-playstation%C2%AE5-digital-edition-2661939.html',
#        'inStock': False,
#        'inStockLabel': "Buttonstyled__StyledButton-sc-140xkaw-1 dwrUQL BasketButton__StyledButton-sc-1qvc90d-0 gQISZA",
#        'outOfStockLabel': "Dieser Artikel ist aktuell nicht verfügbar.<",
#        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
#    'Euronics DE Disk': {
#        'webshop': 'euronics-de',
#        'url': 'https://www.euronics.de/spiele-und-konsolen-film-und-musik/spiele-und-konsolen/playstation-5/spielekonsole/playstation-5-konsole-4061856837826',
#        'inStock': False,
#        'inStockLabel': "buybox--button block btn is--cta is--icon-right is--center is--large",
#        'outOfStockLabel': "Leider ist der Artikel aktuell in unserem Onlineshop nicht verfügbar.",
#        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
#    'Euronics DE Digital': {
#        'webshop': 'euronics-de',
#        'url': 'https://www.euronics.de/spiele-und-konsolen-film-und-musik/spiele-und-konsolen/playstation-5/spielekonsole/playstation-5-digital-edition-konsole-4061856837833',
#        'inStock': False,
#        'inStockLabel': "buybox--button block btn is--cta is--icon-right is--center is--large",
#        'outOfStockLabel': "Leider ist der Artikel aktuell in unserem Onlineshop nicht verfügbar.",
#        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Alternate BE Disk': {
        'webshop': 'alternate-be',
        'url': 'https://www.alternate.be/Sony-Interactive-Entertainment/PlayStation-5-spelconsole/html/product/1651220',
        'inStock': False,
        'inStockLabel': "button-bg arrow-cart-white_red-right",
        'outOfStockLabel': "Nog niet bestelbaar",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Alternate BE Digital': {
        'webshop': 'alternate-be',
        'url': 'https://www.alternate.be/Sony-Interactive-Entertainment/PlayStation-5-Digital-Edition-spelconsole/html/product/1651221',
        'inStock': False,
        'inStockLabel': "button-bg arrow-cart-white_red-right",
        'outOfStockLabel': "Nog niet bestelbaar",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Mediamarkt BE Disk': {
        'webshop': 'mediamarkt-be',
        'url': 'https://www.mediamarkt.be/nl/product/_playstation-ps5-825-gb-9395201-1907411.html',
        'inStock': False,
        'inStockLabel': "EEC_ADD_TO_CART",
        'outOfStockLabel': "Artikel tijdelijk niet in voorraad",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Mediamarkt BE Digital': {
        'webshop': 'mediamarkt-be',
        'url': 'https://www.mediamarkt.be/nl/product/_playstation-ps5-digital-edition-825-gb-9395300-1907412.html',
        'inStock': False,
        'inStockLabel': "EEC_ADD_TO_CART",
        'outOfStockLabel': "Artikel tijdelijk niet in voorraad",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Fun BE Disk': {
        'webshop': 'fun-be',
        'url': 'https://www.fun.be/ps5-console-1.html',
        'inStock': False,
        'inStockLabel': "productAddToCartFormSubmit(this)",
        'outOfStockLabel': "Niet in voorraad",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Fun BE Digital': {
        'webshop': 'fun-be',
        'url': 'https://www.fun.be/ps5-console.html',
        'inStock': False,
        'inStockLabel': "productAddToCartFormSubmit(this)",
        'outOfStockLabel': "Niet in voorraad",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
    'Dreamland BE Digital': {
        'webshop': 'fun-be',
        'url': 'https://www.dreamland.be/e/nl/dl/playstation-5-console-digital-edition-wit-125033',
        'inStock': False,
        'inStockLabel': "In winkelwagen",
        'outOfStockLabel': "Niet in voorraad",
        'detectedAsBotLabel': "detectedAsBotPlaceholderLabel"},
#    'Fnac BE Disk': {
#        'webshop': 'fnac-be',
#        'url': 'https://www.nl.fnac.be/a14119956',
#        'inStock': False,
#        'inStockLabel': "In winkelmandje",
#        'outOfStockLabel': "Niet in voorraad",
#        'detectedAsBotLabel': "You have been blocked."},
#    'Fnac BE Digital': {
#        'webshop': 'fnac-be',
#        'url': 'https://www.nl.fnac.be/a14119956',
#        'inStock': False,
#        'inStockLabel': "In winkelmandje",
#        'outOfStockLabel': "icon_i_223_unavailable-circle",
#        'detectedAsBotLabel': "You have been blocked."},
}

style = style_from_dict({
    Token.QuestionMark: '#ff7f50 bold',
    Token.Answer: '#ff7f50 bold',
    Token.Instruction: '',  # default
    Token.Separator: '#cc5454',
    Token.Selected: '#0abf5b',  # default
    Token.Pointer: '#673ab7 bold',
    Token.Question: '',
})


class EmailValidator(Validator):
    """
    Checks if the input is a valid email address
    """
    pattern = r"\"?([-a-zA-Z0-9._`?{}]+@\w+\.\w+)\"?"

    def validate(self, email):
        if len(email.text):
            if re.match(self.pattern, email.text):
                return True
            else:
                raise ValidationError(
                    message="That is not a valid email address",
                    cursor_position=len(email.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(email.text))


class EmptyValidator(Validator):
    """
    Checks if the input to the question is not empty
    """

    def validate(self, value):
        if len(value.text):
            return True
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(value.text))


class PhoneValidator(Validator):
    """
    Checks if the input is a valid dutch number
    """
    pattern = r"^[+][3][1][6][0-9]{8}$"

    def validate(self, phone):
        if len(phone.text):
            if re.match(self.pattern, phone.text):
                return True
            else:
                raise ValidationError(
                    message="That is not a valid dutch phone number",
                    cursor_position=len(phone.text))
        else:
            raise ValidationError(
                message="You can't leave this blank",
                cursor_position=len(phone.text))


class NumberValidator(Validator):
    """
    Checks if the input is a number
    """

    def validate(self, document):
        try:
            int(document.text)
        except ValueError:
            raise ValidationError(
                message='Please enter a number',
                cursor_position=len(document.text))


def ask_to_configure_settings():
    """
    Asks the user to configure the settings of the script via the cli
    """
    clear_cmdline()
    log("The PS5 AutoBuyer", "white", "larry3d", True)
    console.log("[yellow]Welcome. To get started, please answer the following questions. All information is vital. "
                "If it wasn't, I wouldn't be asking :). Don't worry about leaking your passwords. This script "
                "will run locally on your very own machine. I can not, in any way, reach your credentials.\n")

    questions = [
        {
            'type': 'input',
            'name': 'email',
            'message': 'Enter your email address:',
            'validate': EmailValidator
        },
        {
            'type': 'input',
            'name': 'phone',
            'message': 'Enter your phone number (e.g. +31612345678):',
            'validate': PhoneValidator
        },
        # Telegram notify
        {
            'type': 'confirm',
            'name': 'telegram_notify',
            'message': 'Do you want to be updated via Telegram?'
        },
        # auto-buy
        {
            'type': 'confirm',
            'name': 'auto_buy',
            'message': 'Do you want to automatically buy consoles when in stock?'
        },
        {
            'type': 'input',
            'name': 'max_ordered_items',
            'message': 'How many consoles do you wish to buy at a maximum?',
            'validate': NumberValidator,
            'when': lambda answers: answers['auto_buy'],
            'filter': lambda val: int(val)
        },
        # web-shop passwords
        {
            'type': 'password',
            'name': 'amazon_password',
            'message': 'What is your Amazon account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'coolblue_password',
            'message': 'What is your Coolblue account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'bol_password',
            'message': 'What is your Bol.com account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'mediamarkt_password',
            'message': 'What is your Mediamarkt account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'nedgame_password',
            'message': 'What is your Nedgame account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'intertoys_password',
            'message': 'What is your Intertoys account password?:',
            'when': lambda answers: answers['auto_buy']
        },
        {
            'type': 'password',
            'name': 'paypal_password',
            'message': 'What is your Paypal account password (needed for auto-buy at webshops)?:',
            'when': lambda answers: answers['auto_buy']
        },
        # Creditcard CVC
        {
            'type': 'confirm',
            'name': 'creditcard_payment',
            'message': 'Do you want to pay with creditcard?'
        },
        {
            'type': 'input',
            'name': 'cvccode',
            'message': 'Enter your Creditcard CVC code:',
            'when': lambda answers: answers['creditcard_payment']
        }
    ]

    answers = prompt(questions, style=style)
    print('\n')
    console.log("[yellow]Thank you. Program is starting now!\n")

    return answers


def log(string, color, font="slant", figlet=False):
    """
    Prints a cli message with extra options
    """
    if colored:
        if not figlet:
            six.print_(colored(string, color, attrs=["bold"]))
        else:
            six.print_(colored(figlet_format(
                string, font=font), color, attrs=["bold"]))
    else:
        six.print_(string)


def auto_buy_item(info, ordered_items, place, settings):
    """
    Proceeds to auto-buy the item that is in stock. Notifies the
    user if notifications are enabled.
    """
    if delegate_purchase(info.get('webshop'), info.get('url'), settings):
        print("[=== ITEM ORDERED, HOORAY! ===] [=== {} ===]".format(place))
        if settings.get("telegram_notify"):
            bot_message = "🎉Hooray! Item ordered at {}!🎉".format(place)
            send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
            requests.get(send_text)
        ordered_items += 1
        # if reached max amount of ordered items
        if not ordered_items < settings.get("max_ordered_items"):
            print("[=== Desired amount of ordered items reached! ===] [=== Bye! ===]")
            sys.exit(0)
    return ordered_items


def clear_cmdline():
    """
    Clears the cmd window.
    """
    if name == 'nt':
        _ = system('cls')
    else:
        _ = system('clear')


def initialize_webdriver(url):
    """
    This function initializes the webdriver.

    :param: url
    """
    if platform.system() == "Windows" or platform.system() == "Darwin":
        from selenium.webdriver import Chrome, ChromeOptions
        options = ChromeOptions()
        options.use_chromium = True
        options.headless = True
        driver = Chrome(parser.get("driver", "path_to_driver"), options=options)
    else:
        print("Only Windows and MacOS are supported. Terminating.")
        sys.exit(0)
    driver.get(url)
    return driver


def delegate_purchase(webshop, url, settings):
    """
    Function that delegates the automatically ordering of items

    First, the driver is instantiated. After that, based on the webshop its name
    a function is called that executes the ordering sequence for that specific
    webshop. That is, if it is implemented / possible for that webshop.
    """
    if webshop in ['amazon-nl', 'amazon-fr', 'amazon-it', 'amazon-es', 'amazon-de', 'amazon-uk']:
        return buy_item_at_amazon(initialize_webdriver(url), settings, webshop)
    elif webshop == 'coolblue':
        return buy_item_at_coolblue(initialize_webdriver(url), settings)
    elif webshop == 'bol':
        return buy_item_at_bol(initialize_webdriver(url), url, settings)
    elif webshop == 'mediamarkt-nl':
        return buy_item_at_mediamarkt_nl(initialize_webdriver(url), settings)
    elif webshop == 'nedgame':
        return buy_item_at_nedgame(initialize_webdriver(url), settings)
    elif webshop == 'intertoys':
        return buy_item_at_intertoys(initialize_webdriver(url), settings)
    else:
        console.log("Auto-buy is not implemented for {} yet.".format(webshop))
        return False


def buy_item_at_amazon(driver, settings, webshop):
    """
    Function that will buy the item from the Amazon webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    :param settings:
    :param webshop:
    """
    try:
        # ACCEPT COOKIES
        driver.find_element_by_id("sp-cc-accept").click()
        # ADD TO CART
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'add-to-cart-button'))).click()
        # WARRANTY SCREEN CHECK
        time.sleep(1)
        amazon_warranty_right = True
        try:
            driver.find_element_by_id("attachSiNoCoverage-announce").click()
        except SE.NoSuchElementException:
            amazon_warranty_right = False
        amazon_warranty_middle = True
        try:
            driver.find_element_by_id("siNoCoverage-announce").click()
        except SE.NoSuchElementException:
            amazon_warranty_middle = False
        if amazon_warranty_right == True:
            if webshop == 'amazon-nl':
                cart_url = 'https://amazon.nl/gp/cart/view.html'
            elif webshop == 'amazon-fr':
                cart_url = 'https://amazon.fr/gp/cart/view.html'
            elif webshop == 'amazon-it':
                cart_url = 'https://amazon.it/gp/cart/view.html'
            elif webshop == 'amazon-es':
                cart_url = 'https://amazon.es/gp/cart/view.html'
            elif webshop == 'amazon-de':
                cart_url = 'https://amazon.de/gp/cart/view.html'
            elif webshop == 'amazon-uk':
                cart_url = 'https://amazon.co.uk/gp/cart/view.html'
            time.sleep(2)
            driver.get(cart_url)
            WDW(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="sc-buy-box-ptc-button"]/span/input'))).click()
        elif amazon_warranty_right == False or amazon_warranty_middle == True or amazon_warranty_middle == False:
            WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'hlb-ptc-btn-native'))).click()
        # LOGIN USERNAME
        ActionChains(driver).pause(1) \
            .send_keys_to_element(driver.find_element(By.ID, 'ap_email'), settings.get("email")) \
            .click(driver.find_element(By.ID, 'continue')) \
            .perform()
        # LOGIN PASSWORD
        ActionChains(driver).pause(1) \
            .send_keys_to_element(driver.find_element(By.ID, 'ap_password'), settings.get("amazon_password")) \
            .click(driver.find_element(By.ID, 'signInSubmit')) \
            .perform()
        # PROCESS DIFFERS
        amazon_endscreen = True
        try:
            driver.find_element_by_class_name('place-your-order-button')
        except SE.NoSuchElementException:
            amazon_endscreen = False
        if amazon_endscreen == False:
            # ACCEPT SHIPPING ADDRESS
            WDW(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//*[@id='address-book-entry-0']/div[2]/span/a"))).click()
            # ACCEPT SHIPPING METHOD
            WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'a-button-text'))).click()
            # SELECT PAYMENT METHOD
            if webshop == 'amazon-uk':
                WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                      '/html/body/div[5]/div/div[2]/div[2]/div/div[2]/div/form/div/div/div/div[3]/div[2]/div/div/div/div/div/div/span/div/label/input'))).click()
                WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                      '/html/body/div[5]/div/div[2]/div[2]/div/div[2]/div/form/div/div/div/div[3]/div[2]/div/div/div/div/div/div/span/div/label/input'))).click()
            if webshop == 'amazon-de':
                WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH,
                                                                      '/html/body/div[5]/div[1]/div[2]/div[3]/div/div[2]/div[2]/form/div/div/div/div[3]/div[2]/div/div/div/div/div/div[1]/span/div/label/input'))).click()
            WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'a-button-input'))).click()
            time.sleep(10)
        elif amazon_endscreen == True:
            time.sleep(20)
        # IF IN PRODUCTION, CONFIRM PURCHASE
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'place-your-order-button'))).click()
        else:
            console.log("[ Confirmation of order prevented. Application not in production ] [ See config.ini ]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        console.log("[ Something went wrong while trying to order at Amazon ]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_coolblue(driver, settings):
    """
    Function that will buy the item from the COOLBLUE webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    :param settings:
    """
    try:
        # ACCEPT COOKIES
        driver.find_element_by_name("accept_cookie").click()
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "/html/body/header/div/div[4]/ul/li[2]/a"))).click()
        # LOGIN
        ActionChains(driver).pause(1) \
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_emailaddress'), settings.get("email")) \
            .send_keys_to_element(driver.find_element(By.ID, 'header_menu_password'), settings.get("coolblue_password")) \
            .click(driver.find_element(By.XPATH, '/html/body/header/div/div[4]/ul/li[2]/div/div/div[2]/div/form/div['
                                                 '2]/div[2]/div[2]/button')) \
            .perform()
        # ADD TO CART
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'js-add-to-cart-button'))).click()
        # GO TO BASKET
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'modal-box__container')))
        driver.get("https://www.coolblue.nl/winkelmandje")
        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        WDW(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-shopping-cart-item')))
        if len(driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')) != 1:
            one_item = False
            while not one_item:
                basket = driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')
                for item in basket:
                    try:
                        title = item.find_element(By.CLASS_NAME, 'shopping-cart-item__remove-button').get_attribute(
                            'title')
                        remove_href = item.find_element(By.CLASS_NAME,
                                                        'shopping-cart-item__remove-button').get_attribute('href')
                    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                        continue
                    print(title)
                    if "playstation" not in str.lower(title) or "ps5" not in str.lower(title):
                        driver.get(remove_href)
                        if len(driver.find_elements(By.CLASS_NAME, 'js-shopping-cart-item')) == 1:
                            one_item = True

        WDW(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'js-shopping-cart-item')))
        driver.find_element(By.CLASS_NAME, "js-shopping-cart-item-quantity-input").clear()
        driver.find_element(By.CLASS_NAME, "js-shopping-cart-item-quantity-input").send_keys('1')
        # ORDER
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='shoppingcart_form']/div/div[4]/div[1]/div[2]/div[1]/div[2]/button"))).click()
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='main-content']/div/div/div[11]/div[2]/div/div/div[2]/button"))).click()
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div[3]/div[3]/button"))).click()
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, "//*[@id='main-content']/div[7]/div[3]/div/div"))).click()
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='main-content']/div[7]/div[3]/div/div/div/div[2]/div/div[2]/div[2]/button"))).click()
        # IF IN PRODUCTION, CONFIRM PURCHASE
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id='main-content']/div/div[4]/div/div/div[1]/div[2]/button"))).click()
        else:
            print("[ Confirmation of order prevented. Application not in production ] [ See config.ini ]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[ Something went wrong while trying to order at Amazon ]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_bol(driver, url, settings):
    """
    Function that will buy the item from the BOL.COM webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    :param url:
    :param settings:
    """
    try:
        # ACCEPT COOKIES
        driver.find_element_by_xpath(
            "//*[@id='modalWindow']/div[2]/div[2]/wsp-consent-modal/div[2]/div/div[1]/button").click()
        # LOGIN
        driver.get('https://www.bol.com/nl/rnwy/account/overzicht')
        actions = ActionChains(driver)
        actions.pause(1).send_keys_to_element(driver.find_element(By.ID, 'login_email'), settings.get("email")) \
            .send_keys_to_element(driver.find_element(By.ID, 'login_password'), settings.get("bol_password")) \
            .click(driver.find_element(By.XPATH, '//*[@id="existinguser"]/fieldset/div[3]/input')).perform()
        actions.reset_actions()
        driver.get(url)
        # LOGIC FOR REGULAR ORDER / PREORDER
        try:
            driver.find_element(By.LINK_TEXT, 'Reserveer nu').click()
        except SE.NoSuchElementException as e:
            driver.find_element(By.LINK_TEXT, 'In winkelwagen').click()
        driver.get('https://www.bol.com/nl/order/basket.html')
        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        if len(driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')) != 1:
            # there is more than the auto-buy item in cart
            only_one_item = False
            while not only_one_item:
                basket = driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')
                for item in basket:
                    try:
                        title = item.find_element(By.CLASS_NAME, 'product-details__title').get_attribute('title')
                    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                        continue
                    if "playstation" not in str.lower(title) or "ps5" not in str.lower(title):
                        remove_url = item.find_element(By.ID, 'tst_remove_from_basket').get_attribute('href')
                        driver.get(remove_url)
                        if len(driver.find_elements(By.CLASS_NAME, 'shopping-cart__row')) == 2:
                            only_one_item = True
        # PROCEED
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'continue_ordering_bottom'))).click()
        #PAYMENT
        if in_production:
            time.sleep(1)
            WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="executepayment"]/form/div/button'))).click()
            WDW(driver, 10).until(EC.frame_to_be_available_and_switch_to_it((By.XPATH,"//iframe[@title='Iframe for secured card data input field' and @class='js-iframe']")))
            WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'encryptedSecurityCode'))).send_keys(settings.get("cvccode"))
            driver.switch_to.default_content()
            WDW(driver, 10).until(EC.presence_of_element_located((By.XPATH, "/html/body/div[4]/div[2]/div[2]/div/div[2]/button"))).click()
        else:
            print("[ Confirmation of order prevented. Application not in production ] [ See config.ini ]")
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[ Something went wrong while trying to order at BOL.COM ]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_mediamarkt_nl(driver, settings):
    """
    Function that will buy the item from the Mediamarkt webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    """
    try:
        # ACCEPT COOKIES
        WDW(driver, 10).until(
            EC.presence_of_element_located((By.CLASS_NAME, 'gdpr-cookie-layer__btn--submit--all'))).click()
        # LOGIN
        driver.execute_script("document.getElementById('pdp-add-to-cart').click()")
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'basket-flyout-cart'))).click()
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'cobutton-next'))).click()
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'login-email'))).send_keys(settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'loginForm-password'))).send_keys(
            settings.get("mediamarkt_password"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'loginForm'))).find_element(By.CLASS_NAME,
                                                                                                   'cobutton-next').click()

        # CHECK CART FOR OTHER ITEMS AND DELETE THESE
        basket = WDW(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'cart-product-table')))
        length_basket = len(basket)
        if length_basket > 1:
            while length_basket > 1:
                basket = driver.find_elements(By.CLASS_NAME, 'cart-product-table')
                for item in basket:
                    try:
                        title = item.find_element(By.CLASS_NAME, 'cproduct-heading').get_attribute('innerHTML')
                    except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                        continue
                    if "playstation" not in str.lower(title) or "ps5" not in str.lower(title):
                        try:
                            options = item.find_element_by_class_name('js-cartitem-qty')
                        except (SE.NoSuchElementException, SE.StaleElementReferenceException) as e:
                            continue
                        for option in options.find_elements_by_tag_name('option'):
                            if option.text == 'Verwijder':
                                option.click()
                            length_basket -= 1

        # PROCEED TO PAYMENT
        delivery_form = WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'deliveryForm')))
        delivery_form.find_element(By.CLASS_NAME, 'cobutton-next').click()
        # PAYPAL
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'paypal__xpay'))).click()
        driver.execute_script("document.getElementsByClassName('cobutton-next')[1].click()")
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, '/html/body/div[4]/form/checkout-footer/div/div[1]/div/div[2]/button'))).click()
        email_input = WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'email')))
        email_input.clear()
        email_input.send_keys(settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'password'))).send_keys(
            settings.get("paypal_password"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'btnLogin'))).click()
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'confirmButtonTop'))).click()
        else:
            print("[ Confirmation of order prevented. Application not in production ] [ See config.ini ]")
        # QUIT
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[ Something went wrong while trying to order at Mediamarkt ]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_nedgame(driver, settings):
    """
    Function that will buy the item from the Nedgame webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    :param settings:
    """
    try:
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'koopbutton'))).click()
        driver.get('https://www.nedgame.nl/winkelmand')
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'login_emailadres'))).send_keys(
            settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.NAME, 'login_wachtwoord'))).send_keys(
            settings.get("nedgame_password"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'bigbutton'))).click()
        WDW(driver, 10).until(EC.visibility_of_element_located((By.ID, 'BetaalWijze_9'))).click()
        WDW(driver, 10).until(EC.visibility_of_element_located((By.ID, 'mobiel'))).send_keys(settings.get("phone"))
        if in_production:
            WDW(driver, 10).until(EC.visibility_of_element_located(
                (By.XPATH, '/html/body/div[4]/div/div[2]/div[2]/div/div[1]/form/div/div[6]/button'))).click()
        else:
            print("[ Confirmation of order prevented. Application not in production ] [ See config.ini ]")
        # QUIT
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[ Something went wrong while trying to order at Nedgame ]")
        driver.close()
        driver.quit()
        return False


def buy_item_at_intertoys(driver, settings):
    """
    Function that will buy the item from the Intertoys webshop.

    This is done by a sequence of interactions on the website, just like
    a person would normally do. Only actually buys when application is in
    production. See the config.ini setting `production`.

    :param driver:
    """
    try:
        # ACCEPT COOKIES
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'PrivacyAcceptBtnText'))).click()
        # ORDER
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'productPageAdd2Cart'))).click()
        time.sleep(1)
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'GotoCartButton2'))).click()
        # LOGIN
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'WC_CheckoutLogon_FormInput_logonId'))).send_keys(settings.get("email"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'WC_CheckoutLogon_FormInput_logonPassword'))).send_keys(
            settings.get("intertoys_password"))
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'guestShopperLogon'))).click()
        # ORDER
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'shopcartCheckout'))).click()
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='WC_CheckoutPaymentsAndBillingAddressf_div_2_1']/div[4]/label/div[3]/span"))).click()
        time.sleep(1)
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='WC_CheckoutPaymentsAndBillingAddressf_div_2_1']/div[4]/div/div[2]/a"))).click()
        WDW(driver, 10).until(EC.presence_of_element_located((By.ID, 'singleOrderSummary'))).click()
        time.sleep(5)
        WDW(driver, 10).until(EC.presence_of_element_located(
            (By.XPATH, "//*[@id='payment-zone']/form/table/tbody/tr[5]/td/div/input"))).click()
        time.sleep(5)
        if in_production:
            WDW(driver, 10).until(EC.presence_of_element_located(
                (By.XPATH, "//*[@id='payment-zone']/form/table/tbody/tr[7]/td/input"))).click()
        else:
            print("[ Confirmation of order prevented. Application not in production ] [ See config.ini ]")
        # QUIT
        driver.close()
        driver.quit()
        return True
    except (SE.NoSuchElementException, SE.ElementNotInteractableException,
            SE.StaleElementReferenceException, SE.TimeoutException) as e:
        print("[ Something went wrong while trying to order at Intertoys ]")
        driver.close()
        driver.quit()
        return False


def main():
    """
    Function that loops until the 'desired amount of items bought' is reached.

    While that amount is not reached, the function checks whether the item is
    in stock for every webshop in the locations dictionary. Once an item is in
    stock, it will proceed to buy this item by calling the `delegate_purchase`
    function. This function takes the name of the webshop and the url of the
    item as its arguments.

    Between every check, there is a wait of 30 seconds.
    """
    # get settings
    settings = ask_to_configure_settings()
    user_agent = random.choice(user_agents)
    referer = random.choice(referers)
    ordered_items = 0
    # loop until desired amount of ordered items is reached
    while True:
        detected_as_bot = []
        times_detected_as_bot = 0
        # ==================================================== #
        # loop through all web-shops where potentially in stock #
        # ==================================================== #
        for place, info in sorted(locations.items(), key=lambda x: random.random()):
            # generate headers
            # user_agent = random.choice(user_agents)
            headers = {
                'pragma': 'no-cache',
                'cache-control': 'no-cache',
                'dnt': '1',
                "User-Agent": user_agent,
                "Accept-Encoding": "gzip, deflate",
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
                'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
                'sec-fetch-site': 'same-origin',
                'sec-fetch-user': '?1',
                'sec-fetch-mode': 'navigate',
                'sec-fetch-dest': 'document',
                'referer': referer,
                "Connection": "close", "Upgrade-Insecure-Requests": "1"
            }
            try:
                content = requests.get(info.get('url'), timeout=10, headers=headers).content.decode('utf-8')
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout,
                    requests.exceptions.ChunkedEncodingError) as e:
                console.log(f"[ [bold red]REQUEST ERROR[/]   ] [ {place} ]")
                continue
            # ======================================== #
            # item in stock, proceed to try and buy it #
            # ======================================== #
            if (info.get('detectedAsBotLabel') not in content and  info.get('outOfStockLabel') not in content and info.get('inStockLabel') in content):
                # ===================== #
                # Price check at Amazon #
                # ===================== #
                if info.get('webshop') in ['amazon-nl', 'amazon-fr', 'amazon-it', 'amazon-es', 'amazon-de', 'amazon-uk']:
                    soup = BeautifulSoup(content, 'html.parser')
                    price_raw = soup.body.select_one('div#price span#priceblock_ourprice').get_text()
                    price_strip_space = price_raw.replace(' ', '')
                    try:
                        price_strip_euro = price_strip_space.replace('€', '')
                    except:
                        pass
                    try:
                        price_strip_euro = price_strip_space.replace('£', '')
                    except:
                        pass
                    try:
                        price = int(price_strip_euro.replace(',', ''))
                    except:
                        pass
                    try:
                        price = int(price_strip_euro.replace('.', ''))
                    except:
                        pass
                    if price <= 39000:
                        console.log(f"[ [bold red]ERROR PRICE [/]    ] [ {place} ] [[bold red] {price_raw} [/]]")
                    elif price >= 41000:
                        console.log(f"[ [bold red]ERROR PRICE [/]    ] [ {place} ] [[bold red] {price_raw} [/]]")
                    else:
                        console.log(f"[ [bold green]OMG, IN STOCK![/]  ] [ {place} ]")
                        # === IF ENABLED, SEND Telegram === #
                        if settings.get("telegram_notify") and not info.get('inStock'):
                            try:
                                bot_message = "💶Item might be in stock at {}💶".format(place)
                                send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&disable_web_page_preview=True&parse_mode=Markdown&text=' + bot_message
                                requests.get(send_text)
                                bot_message = "URL: {}".format(info.get('url'))
                                send_text = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&disable_web_page_preview=True&text=' + bot_message
                                requests.get(send_text)
                            except:
                                console.log(
                                    "[=== ERROR ===] [=== SENDING TELEGRAM MESSAGE FAILED ===]")
                        # === IF ENABLED, BUY ITEM === #
                        if settings.get("auto_buy"):
                            ordered_items = auto_buy_item(info, ordered_items, place, settings)
                        # === SET IN-STOCK TO TRUE === #
                        info['inStock'] = True
            elif info.get('detectedAsBotLabel') in content:
                detected_as_bot.append(place)
                if info.get('webshop') in ['amazon-nl', 'amazon-fr', 'amazon-it', 'amazon-es', 'amazon-de', 'amazon-uk']:
                    if info.get('webshop') == 'amazon-nl':
                        bot_url = 'https://www.amazon.nl/errors/validateCaptcha'
                    elif info.get('webshop') == 'amazon-fr':
                        bot_url = 'https://www.amazon.fr/errors/validateCaptcha'
                    elif info.get('webshop') == 'amazon-it':
                        bot_url = 'https://www.amazon.it/errors/validateCaptcha'
                    elif info.get('webshop') == 'amazon-es':
                        bot_url = 'https://www.amazon.es/errors/validateCaptcha'
                    elif info.get('webshop') == 'amazon-de':
                        bot_url = 'https://www.amazon.de/errors/validateCaptcha'
                    elif info.get('webshop') == 'amazon-uk':
                        bot_url = 'https://www.amazon.co.uk/errors/validateCaptcha'
                    from selenium.webdriver import Chrome, ChromeOptions
                    options = ChromeOptions()
                    options.use_chromium = True
                    options.headless = True
                    driver = Chrome(parser.get("driver", "path_to_driver"), options=options)
                    driver.get(bot_url)
                    captcha = AmazonCaptcha.fromdriver(driver)
                    solution = captcha.solve()
                    ActionChains(driver).pause(1) \
                        .send_keys_to_element(driver.find_element(By.ID, 'captchacharacters'), solution) \
                        .click(driver.find_element(By.XPATH, '/html/body/div/div[1]/div[3]/div/div/form/div[2]/div/span/span/button')) \
                        .perform()
                    driver.close()
                    driver.quit()
                    console.log(
                        f"[ [bold red]DETECTED AS BOT[/] ] [ {place} ] [ [bold yellow]Captcha solved[/] ]")
                else:
                    console.log(f"[ [bold red]DETECTED AS BOT[/] ] [ {place} ]")
                times_detected_as_bot += 1
                # rotate headers stuff
                user_agent = random.choice(user_agents)
                referer = random.choice(referers)
            elif info.get('outOfStockLabel') in content:
                info['inStock'] = False
                console.log(f"[ OUT OF STOCK    ] [ {place} ]")
            else:
                console.log(f"[ [bold red]ERROR IN PAGE[/]   ] [ {place} ]")
            time.sleep(random.randint(45, 85) / 100.0)

        # print report
        print('\n')
        console.log(f"Total requests: [bold red]{len(locations)}[/]. Amount of times detected as bot: "f"[bold red]{times_detected_as_bot}[/].")
        print('\n')


# start of program
if __name__ == "__main__":
    main()
