import pytest
from src.generic.cctx_mapper import parse_order
from src.generic.cctx_model import Order
from dacite.config import Config
import numbers

# Helper pour générer un dict d'ordre minimal

def minimal_order_dict(**overrides):
    base = {
        "id": "order_1",
        "oid": "order_1",
        "price": 100.0,
        "limitPx": 100.0,
        "side": "buy",
        "info": {
            "coin": "BTC",
            "side": "buy",
            "limitPx": "100.0",
            "sz": "0.1",
            "oid": "order_1",
            "timestamp": "0",
            "triggerCondition": "",
            "isTrigger": False,
            "triggerPx": "",
            "children": [],
            "isPositionTpsl": False,
            "reduceOnly": False,
            "orderType": "limit",
            "origSz": "0.1",
            "tif": "",
            "cloid": None
        }
    }
    # Appliquer les overrides, y compris dans info
    for k, v in overrides.items():
        if k in base:
            base[k] = v
        elif k in base["info"]:
            base["info"][k] = v
    return base


def test_parse_order_full():
    data = minimal_order_dict()
    order = parse_order(data)
    assert isinstance(order, Order)
    assert order.id == "order_1"
    assert order.price == 100.0
    assert order.info.coin == "BTC"
    assert order.info.limitPx == "100.0"
    assert order.info.sz == "0.1"


def test_parse_order_missing_fields():
    data = minimal_order_dict()
    del data["info"]["limitPx"]  # Champ manquant dans info
    order = parse_order(data)
    assert order.info.limitPx == "" or order.info.limitPx == 0.0  # Selon le type attendu


def test_parse_order_null_values():
    data = minimal_order_dict()
    data["info"]["limitPx"] = None
    data["info"]["sz"] = None
    order = parse_order(data)
    assert order.info.limitPx == 0.0 or order.info.limitPx == ""  # Selon le type attendu
    assert order.info.sz == 0.0 or order.info.sz == ""


def test_parse_order_unexpected_types():
    data = minimal_order_dict()
    data["info"]["sz"] = "not_a_float"
    order = parse_order(data)
    # Si le champ est typé str dans Info, la valeur brute est conservée
    assert order.info.sz == "not_a_float"


def _create_config():
    """Crée une configuration dacite avec des hooks de type sécurisés"""
    return Config(
        type_hooks={
            str: lambda x: "" if x is None else str(x),
            float: lambda x: 0.0 if x in (None, "") else float(x),
            int: lambda x: 0 if x in (None, "") else int(x),
            bool: lambda x: False if x is None else bool(x)
        },
        strict=False,
        cast=[tuple, list]
    ) 

def test_parse_order_real_api_data():
    """Test avec des données API réelles ou proches qui causent le problème observé"""
    # Simuler les données que l'API Hyperliquid pourrait retourner
    real_api_data = {
        "id": "33186578567",
        "price": 50000.0,
        "amount": 0.001,
        "side": "sell",
        "type": "limit",
        "status": "open",
        "symbol": "BTC/USDC:USDC",
        "info": {
            "oid": "33186578567",
            "limitPx": "50000.0",
            "sz": "0.001",
            "side": "A",
            "coin": "BTC",
            "orderType": "limit",
            "timestamp": "1234567890",
            "children": []  # Liste vide au lieu d'une chaîne
        }
    }
    
    order = parse_order(real_api_data)
    assert isinstance(order, Order)
    assert order.id == "33186578567"
    assert order.price == 50000.0
    assert order.info.coin == "BTC"
    assert order.info.limitPx == "50000.0"
    assert order.info.sz == "0.001"
    assert isinstance(order.info.children, list)
    assert len(order.info.children) == 0


def test_parse_order_with_partial_api_data():
    """Test avec des données API partielles pour voir si les champs manquants sont bien remplis"""
    partial_api_data = {
        "id": "123456",
        "price": 45000.0,
        "side": "buy"
        # Pas d'info du tout
    }
    
    order = parse_order(partial_api_data)
    assert isinstance(order, Order)
    assert order.id == "123456"
    assert order.price == 45000.0
    assert order.side == "buy"
    # Les champs manquants doivent être remplis avec des valeurs par défaut
    assert isinstance(order.info.children, list)
    assert len(order.info.children) == 0  # Liste vide par défaut
    assert order.info.coin == ""  # Chaîne vide par défaut


def test_parse_order_with_generator_object_string():
    """Test pour reproduire le problème avec la chaîne 'generator object' dans children"""
    api_data_with_generator = {
        "id": "33186578567",
        "price": 50000.0,
        "amount": 0.001,
        "side": "sell",
        "info": {
            "oid": "33186578567",
            "limitPx": "50000.0",
            "sz": "0.001",
            "side": "A",
            "coin": "BTC",
            "children": "<generator object _build_value_for_collection.<locals>.<genexpr> at 0x11ad5f010>"
        }
    }
    
    order = parse_order(api_data_with_generator)
    assert isinstance(order, Order)
    # Le champ children devrait être traité correctement, soit comme une liste contenant la chaîne,
    # soit converti en liste vide selon la logique du mapper
    assert isinstance(order.info.children, list)
    # Dans ce cas, la chaîne devrait être conservée comme un élément de liste
    if len(order.info.children) > 0:
        assert isinstance(order.info.children[0], str) 

def test_parse_order_empty_api_response():
    """Test pour reproduire le problème observé dans les logs avec des ordres ayant des champs vides"""
    # Simuler une réponse API Hyperliquid qui ne contient que l'ID
    minimal_api_data = {
        "id": "33186578567"
    }
    
    order = parse_order(minimal_api_data)
    assert isinstance(order, Order)
    assert order.id == "33186578567"
    
    # Vérifier que tous les champs obligatoires sont remplis avec des valeurs par défaut appropriées
    assert isinstance(order.info.children, list)
    assert len(order.info.children) == 0
    assert isinstance(order.info.coin, str)
    assert order.info.coin == ""  # Valeur par défaut spécifiée
    assert isinstance(order.trades, list)
    assert len(order.trades) == 0
    assert isinstance(order.fees, list)
    assert len(order.fees) == 0
    
    # Vérifier que les types numériques ont des valeurs par défaut appropriées
    assert order.price == 0.0
    assert order.amount == 0.0
    assert order.timestamp == 0 

def test_parse_order_ccxt_structure():
    """Test avec une structure de données CCXT typique"""
    # Structure basée sur la documentation CCXT standard
    ccxt_order_data = {
        'id': '33187108569',
        'clientOrderId': None,
        'datetime': '2024-01-15T10:30:00.000Z',
        'timestamp': 1705315800000,
        'lastTradeTimestamp': None,
        'lastUpdateTimestamp': 1705315800000,
        'status': 'open',
        'symbol': 'BTC/USDC:USDC',
        'type': 'limit',
        'timeInForce': 'GTC',
        'amount': 0.001,
        'filled': 0.0,
        'remaining': 0.001,
        'cost': 0.0,
        'average': None,
        'price': 50000.0,
        'triggerPrice': None,
        'stopPrice': None,
        'takeProfitPrice': None,
        'stopLossPrice': None,
        'postOnly': False,
        'reduceOnly': False,
        'side': 'sell',
        'fee': None,
        'fees': [],
        'trades': [],
        'info': {
            'coin': 'BTC',
            'side': 'A',  # A pour Ask (sell)
            'limitPx': '50000.0',
            'sz': '0.001',
            'oid': '33187108569',
            'timestamp': '1705315800000',
            'triggerCondition': '',
            'isTrigger': False,
            'triggerPx': '',
            'children': [],
            'isPositionTpsl': False,
            'reduceOnly': False,
            'orderType': 'limit',
            'origSz': '0.001',
            'tif': 'Gtc',
            'cloid': None
        }
    }
    
    order = parse_order(ccxt_order_data)
    assert isinstance(order, Order)
    assert order.id == '33187108569'
    assert order.symbol == 'BTC/USDC:USDC'
    assert order.side == 'sell'
    assert order.price == 50000.0
    assert order.amount == 0.001
    
    # Vérifications des champs info
    assert order.info.coin == 'BTC'
    assert order.info.side == 'A'
    assert order.info.limitPx == '50000.0'
    assert order.info.sz == '0.001'
    assert order.info.oid == '33187108569'
    assert isinstance(order.info.children, list)
    assert len(order.info.children) == 0 

def test_parse_order_with_missing_id():
    """Test avec une réponse d'API qui n'a pas d'ID - cas de fallback"""
    api_response_without_id = {
        'symbol': 'BTC/USDC:USDC',
        'type': 'limit',    
        'side': 'buy',
        'amount': 0.001,
        'price': 50000.0,
        'status': 'pending',
        # Pas d'ID - simule un échec de création d'ordre
    }
    
    order = parse_order(api_response_without_id)
    assert isinstance(order, Order)
    # L'ID devrait être une chaîne vide par défaut
    assert order.id == ""
    assert order.symbol == 'BTC/USDC:USDC'
    assert order.side == 'buy'
    assert order.price == 50000.0
    assert order.amount == 0.001 